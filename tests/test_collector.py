from unittest.mock import patch

import pytest

from pihole_exporter.collector import PiholeCollector


def metrics_by_name(collector):
    """Collect metrics and index them by family name."""
    return {m.name: m for m in collector.collect()}


# --- Happy path ---


def test_collect_pihole_up_is_1_on_success(mock_client):
    collector = PiholeCollector(mock_client)
    metrics = metrics_by_name(collector)
    assert metrics["pihole_up"].samples[0].value == 1.0


def test_collect_queries_total(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_queries_total"].samples[0].value == 42000.0


def test_collect_queries_blocked(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_queries_blocked_total"].samples[0].value == 1500.0


def test_collect_queries_percent_blocked(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_queries_percent_blocked"].samples[0].value == pytest.approx(
        3.57
    )


def test_collect_clients_active(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_clients_active"].samples[0].value == 8.0


def test_collect_clients_total(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_clients_total"].samples[0].value == 15.0


def test_collect_gravity_domains_being_blocked(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_gravity_domains_being_blocked"].samples[0].value == 185000.0


def test_collect_gravity_last_update(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert (
        metrics["pihole_gravity_last_update_timestamp"].samples[0].value == 1710000000.0
    )


# --- Query types ---


def test_collect_query_type_labels(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    qt = metrics["pihole_query_type_count"]
    by_type = {s.labels["type"]: s.value for s in qt.samples}
    assert by_type["A"] == 25000.0
    assert by_type["AAAA"] == 12000.0
    assert by_type["MX"] == 500.0


def test_collect_empty_query_types(mock_client):
    mock_client.get_query_types.return_value = {"querytypes": {}}
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_query_type_count"].samples == []


# --- Upstream metrics ---


def test_collect_upstream_queries_total_value(mock_client):
    # count is a top-level field in the upstream object (not inside statistics)
    metrics = metrics_by_name(PiholeCollector(mock_client))
    sample = metrics["pihole_upstream_queries_total"].samples[0]
    assert sample.value == 5000.0


def test_collect_upstream_queries_total_labels(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    sample = metrics["pihole_upstream_queries_total"].samples[0]
    assert sample.labels["ip"] == "1.1.1.1"
    assert sample.labels["port"] == "53"
    assert sample.labels["name"] == "one.one.one.one"


def test_collect_upstream_queries_failed(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_upstream_queries_failed"].samples[0].value == 10.0


def test_collect_upstream_response_time(mock_client):
    # API returns response in seconds (0.0125s), collector converts to ms (* 1000)
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_upstream_response_time_ms"].samples[
        0
    ].value == pytest.approx(12.5)


def test_collect_empty_upstreams(mock_client):
    mock_client.get_upstreams.return_value = {"upstreams": []}
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_upstream_queries_total"].samples == []


# --- Version ---


def test_collect_version_info_label(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    ver = metrics["pihole_version_info"]
    assert ver.samples[0].labels["core"] == "v6.0.5"
    assert ver.samples[0].value == 1.0


def test_collect_version_unknown_when_missing(mock_client):
    mock_client.get_version.return_value = {}
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_version_info"].samples[0].labels["core"] == "unknown"


# --- Scrape metadata ---


def test_collect_scrape_duration_is_non_negative(mock_client):
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_scrape_duration_seconds"].samples[0].value >= 0.0


def test_collect_scrape_errors_starts_at_zero(mock_client):
    # prometheus_client strips _total from CounterMetricFamily.name — look up without it
    collector = PiholeCollector(mock_client)
    metrics = metrics_by_name(collector)
    assert metrics["pihole_scrape_errors"].samples[0].value == 0.0


# --- Error scenarios ---


def test_collect_pihole_up_0_when_summary_fails(mock_client):
    mock_client.get_summary.side_effect = Exception("Connection refused")
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_up"].samples[0].value == 0.0


@pytest.mark.parametrize(
    "failing_method",
    ["get_upstreams", "get_query_types", "get_version"],
)
def test_collect_pihole_up_stays_1_on_partial_failure(mock_client, failing_method):
    """pihole_up remains 1 when non-summary endpoints fail."""
    getattr(mock_client, failing_method).side_effect = Exception("timeout")
    metrics = metrics_by_name(PiholeCollector(mock_client))
    assert metrics["pihole_up"].samples[0].value == 1.0


def test_collect_increments_error_count_on_summary_failure(mock_client):
    mock_client.get_summary.side_effect = Exception("Connection refused")
    collector = PiholeCollector(mock_client)
    list(collector.collect())
    list(collector.collect())
    metrics = metrics_by_name(collector)
    assert metrics["pihole_scrape_errors"].samples[0].value == 3.0


def test_collect_error_count_accumulates_across_scrapes(mock_client):
    mock_client.get_upstreams.side_effect = Exception("timeout")
    collector = PiholeCollector(mock_client)
    list(collector.collect())
    list(collector.collect())
    metrics = metrics_by_name(collector)
    assert metrics["pihole_scrape_errors"].samples[0].value == 3.0


@patch("pihole_exporter.collector.LOGGER")
def test_collect_logs_error_when_summary_fails(mock_logger, mock_client):
    mock_client.get_summary.side_effect = Exception("Connection refused")
    list(PiholeCollector(mock_client).collect())
    mock_logger.error.assert_called_once()


@pytest.mark.parametrize(
    "failing_method,log_level",
    [
        ("get_upstreams", "warning"),
        ("get_query_types", "warning"),
        ("get_version", "warning"),
    ],
)
@patch("pihole_exporter.collector.LOGGER")
def test_collect_logs_warning_on_partial_failure(
    mock_logger, mock_client, failing_method, log_level
):
    getattr(mock_client, failing_method).side_effect = Exception("timeout")
    list(PiholeCollector(mock_client).collect())
    getattr(mock_logger, log_level).assert_called_once()
