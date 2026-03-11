import logging

from pihole_exporter.settings import SETTINGS

logging.basicConfig(
    level=SETTINGS.log_level.upper(),
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

LOGGER = logging.getLogger("pihole_exporter")
