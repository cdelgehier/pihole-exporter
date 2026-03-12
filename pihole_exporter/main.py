"""Entry point for the Pi-hole Prometheus exporter."""

import time

from prometheus_client import REGISTRY, start_http_server

from pihole_exporter.client import PiholeClient
from pihole_exporter.collector import PiholeCollector
from pihole_exporter.logger import LOGGER
from pihole_exporter.settings import SETTINGS

__version__ = "0.4.0"


def run_server(port: int, client: PiholeClient) -> None:
    """Register the collector and start the Prometheus HTTP server."""
    REGISTRY.register(PiholeCollector(client))
    start_http_server(port)


def main() -> None:
    scheme = "https" if SETTINGS.pihole_https else "http"
    LOGGER.info(
        "Pi-hole exporter v%s listening on :%d", __version__, SETTINGS.exporter_port
    )
    LOGGER.info(
        "Scraping Pi-hole at %s://%s:%d",
        scheme,
        SETTINGS.pihole_host,
        SETTINGS.pihole_port,
    )

    client = PiholeClient(
        host=SETTINGS.pihole_host,
        port=SETTINGS.pihole_port,
        password=SETTINGS.pihole_password,
        use_https=SETTINGS.pihole_https,
    )

    run_server(SETTINGS.exporter_port, client)

    # Keep the process alive — the collector is invoked by prometheus_client on each scrape
    while True:
        time.sleep(SETTINGS.scrape_interval)


if __name__ == "__main__":
    main()
