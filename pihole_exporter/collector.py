"""Custom Prometheus collector for Pi-hole v6."""

import time
from collections.abc import Iterator

from prometheus_client.metrics_core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    Metric,
)

from pihole_exporter.client import PiholeClient
from pihole_exporter.logger import LOGGER


class PiholeCollector:
    """Custom Prometheus collector for Pi-hole v6."""

    def __init__(self, client: PiholeClient) -> None:
        self.client = client
        self._scrape_errors = 0

    def collect(self) -> Iterator[Metric]:
        start = time.time()
        up = 1
        errors = 0

        # Fetch summary
        summary: dict = {}
        try:
            summary = self.client.get_summary()
        except Exception as exc:
            LOGGER.error("Failed to fetch summary: %s", exc)
            up = 0
            errors += 1

        # Fetch upstreams
        upstreams_data: dict = {}
        try:
            upstreams_data = self.client.get_upstreams()
        except Exception as exc:
            LOGGER.warning("Failed to fetch upstreams: %s", exc)
            errors += 1

        # Fetch query types
        query_types_data: dict = {}
        try:
            query_types_data = self.client.get_query_types()
        except Exception as exc:
            LOGGER.warning("Failed to fetch query_types: %s", exc)
            errors += 1

        # Fetch version
        version_data: dict = {}
        try:
            version_data = self.client.get_version()
        except Exception as exc:
            LOGGER.warning("Failed to fetch version: %s", exc)
            errors += 1

        # Fetch top clients
        top_clients_data: dict = {}
        try:
            top_clients_data = self.client.get_top_clients()
        except Exception as exc:
            LOGGER.warning("Failed to fetch top_clients: %s", exc)
            errors += 1

        duration = time.time() - start
        self._scrape_errors += errors

        queries = summary.get("queries", {})
        clients = summary.get("clients", {})
        gravity = summary.get("gravity", {})

        if up:
            LOGGER.info(
                "Scrape completed in %.3fs — queries_total=%s blocked=%s",
                duration,
                queries.get("total", 0),
                queries.get("blocked", 0),
            )

        # pihole_up
        g_up = GaugeMetricFamily(
            "pihole_up", "1 if the last scrape succeeded, 0 otherwise"
        )
        g_up.add_metric([], up)
        yield g_up

        # Query / client / gravity gauges
        metrics_map = {
            "pihole_queries_total": (queries.get("total", 0), "Total DNS queries"),
            "pihole_queries_blocked_total": (
                queries.get("blocked", 0),
                "Total blocked queries",
            ),
            "pihole_queries_percent_blocked": (
                queries.get("percent_blocked", 0.0),
                "Percentage of queries blocked",
            ),
            "pihole_queries_unique_domains": (
                queries.get("unique_domains", 0),
                "Number of unique domains seen",
            ),
            "pihole_queries_forwarded": (
                queries.get("forwarded", 0),
                "Forwarded queries",
            ),
            "pihole_queries_cached": (queries.get("cached", 0), "Cached queries"),
            "pihole_clients_active": (clients.get("active", 0), "Active clients"),
            "pihole_clients_total": (clients.get("total", 0), "Total clients"),
            "pihole_gravity_domains_being_blocked": (
                gravity.get("domains_being_blocked", 0),
                "Domains being blocked by gravity",
            ),
            "pihole_gravity_last_update_timestamp": (
                gravity.get("last_update", 0),
                "Last gravity update timestamp (epoch)",
            ),
        }

        for metric_name, (value, description) in metrics_map.items():
            g = GaugeMetricFamily(metric_name, description)
            g.add_metric([], float(value))
            yield g

        # pihole_query_type_count{type=}
        g_qt = GaugeMetricFamily(
            "pihole_query_type_count",
            "Number of queries by DNS type",
            labels=["type"],
        )
        for qtype, count in query_types_data.get("types", {}).items():
            g_qt.add_metric([qtype], float(count))
        yield g_qt

        # pihole_upstream_*{ip, port, name}
        g_uq = GaugeMetricFamily(
            "pihole_upstream_queries_total",
            "Total queries per upstream DNS server",
            labels=["ip", "port", "name"],
        )
        g_uf = GaugeMetricFamily(
            "pihole_upstream_queries_failed",
            "Failed queries per upstream DNS server",
            labels=["ip", "port", "name"],
        )
        g_urt = GaugeMetricFamily(
            "pihole_upstream_response_time_ms",
            "Response time in ms per upstream DNS server",
            labels=["ip", "port", "name"],
        )

        for upstream in upstreams_data.get("upstreams", []):
            ip = upstream.get("ip", "")
            port = str(upstream.get("port", ""))
            name = upstream.get("name", "")
            stats = upstream.get("statistics", {})
            labels = [ip, port, name]
            g_uq.add_metric(labels, float(upstream.get("count", 0)))
            g_uf.add_metric(labels, float(upstream.get("failed", 0)))
            g_urt.add_metric(labels, float(stats.get("response", 0.0)) * 1000)

        yield g_uq
        yield g_uf
        yield g_urt

        # pihole_client_queries_total{ip, name}
        g_cq = GaugeMetricFamily(
            "pihole_client_queries_total",
            "Total DNS queries per client",
            labels=["ip", "name"],
        )
        for client_entry in top_clients_data.get("clients", []):
            ip = client_entry.get("ip", "")
            name = client_entry.get("name", ip)
            count = client_entry.get("count", 0)
            g_cq.add_metric([ip, name], float(count))
        yield g_cq

        # pihole_version_info{core=}
        core_version = (
            version_data.get("version", {})
            .get("core", {})
            .get("local", {})
            .get("version", "unknown")
        )
        g_ver = GaugeMetricFamily(
            "pihole_version_info",
            "Pi-hole version information",
            labels=["core"],
        )
        g_ver.add_metric([core_version], 1.0)
        yield g_ver

        # pihole_scrape_duration_seconds
        g_dur = GaugeMetricFamily(
            "pihole_scrape_duration_seconds",
            "Duration of the last scrape in seconds",
        )
        g_dur.add_metric([], duration)
        yield g_dur

        # pihole_scrape_errors_total
        c_err = CounterMetricFamily(
            "pihole_scrape_errors_total",
            "Total number of scrape errors",
        )
        c_err.add_metric([], float(self._scrape_errors))
        yield c_err
