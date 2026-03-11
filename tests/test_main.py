from unittest.mock import patch

import pytest

# --- run_server ---


@patch("pihole_exporter.main.start_http_server")
@patch("pihole_exporter.main.REGISTRY")
def test_run_server_registers_collector(mock_registry, mock_start_http, mock_client):
    from pihole_exporter.main import run_server

    run_server(9666, mock_client)

    mock_registry.register.assert_called_once()
    mock_start_http.assert_called_once_with(9666)


@patch("pihole_exporter.main.start_http_server")
@patch("pihole_exporter.main.REGISTRY")
def test_run_server_uses_provided_port(mock_registry, mock_start_http, mock_client):
    from pihole_exporter.main import run_server

    run_server(8080, mock_client)

    mock_start_http.assert_called_once_with(8080)


# --- main ---


@patch("pihole_exporter.main.time.sleep", side_effect=[None, KeyboardInterrupt])
@patch("pihole_exporter.main.run_server")
@patch("pihole_exporter.main.LOGGER")
@patch("pihole_exporter.main.SETTINGS")
def test_main_logs_startup_info(
    mock_settings, mock_logger, mock_run_server, mock_sleep
):
    mock_settings.pihole_https = False
    mock_settings.pihole_host = "localhost"
    mock_settings.pihole_port = 80
    mock_settings.exporter_port = 9666
    mock_settings.pihole_password = ""
    mock_settings.scrape_interval = 30

    from pihole_exporter.main import main

    with pytest.raises(KeyboardInterrupt):
        main()

    assert mock_logger.info.call_count >= 2


@patch("pihole_exporter.main.time.sleep", side_effect=[None, KeyboardInterrupt])
@patch("pihole_exporter.main.run_server")
@patch("pihole_exporter.main.LOGGER")
@patch("pihole_exporter.main.SETTINGS")
def test_main_calls_run_server_with_exporter_port(
    mock_settings, mock_logger, mock_run_server, mock_sleep
):
    mock_settings.pihole_https = False
    mock_settings.pihole_host = "localhost"
    mock_settings.pihole_port = 80
    mock_settings.exporter_port = 9666
    mock_settings.pihole_password = ""
    mock_settings.scrape_interval = 30

    from pihole_exporter.main import main

    with pytest.raises(KeyboardInterrupt):
        main()

    mock_run_server.assert_called_once()
    call_port, _ = mock_run_server.call_args[0]
    assert call_port == 9666


@pytest.mark.parametrize(
    "use_https,expected_scheme",
    [
        (False, "http"),
        (True, "https"),
    ],
)
@patch("pihole_exporter.main.time.sleep", side_effect=KeyboardInterrupt)
@patch("pihole_exporter.main.run_server")
@patch("pihole_exporter.main.LOGGER")
@patch("pihole_exporter.main.SETTINGS")
def test_main_logs_correct_scheme(
    mock_settings, mock_logger, mock_run_server, mock_sleep, use_https, expected_scheme
):
    mock_settings.pihole_https = use_https
    mock_settings.pihole_host = "pihole.local"
    mock_settings.pihole_port = 80
    mock_settings.exporter_port = 9666
    mock_settings.pihole_password = ""
    mock_settings.scrape_interval = 30

    from pihole_exporter.main import main

    with pytest.raises(KeyboardInterrupt):
        main()

    logged_messages = " ".join(str(c) for c in mock_logger.info.call_args_list)
    assert expected_scheme in logged_messages
