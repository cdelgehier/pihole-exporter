from unittest.mock import MagicMock

import pytest

from pihole_exporter.client import PiholeClient

SUMMARY_RESPONSE = {
    "queries": {
        "total": 42000,
        "blocked": 1500,
        "percent_blocked": 3.57,
        "unique_domains": 1200,
        "forwarded": 35000,
        "cached": 5500,
    },
    "clients": {"active": 8, "total": 15},
    "gravity": {"domains_being_blocked": 185000, "last_update": 1710000000},
}

UPSTREAMS_RESPONSE = {
    "upstreams": [
        {
            "ip": "1.1.1.1",
            "port": 53,
            "name": "one.one.one.one",
            "count": 5000,
            "failed": 10,
            "statistics": {"response": 0.0125, "variance": 0.001},
        }
    ]
}

# Pi-hole v6 real API uses "types" (not "querytypes")
QUERY_TYPES_RESPONSE = {"types": {"A": 25000, "AAAA": 12000, "MX": 500}}

# Pi-hole v6 real API uses "version" (not "tag")
VERSION_RESPONSE = {"version": {"core": {"local": {"version": "v6.0.5"}}}}


@pytest.fixture
def mock_client():
    client = MagicMock(spec=PiholeClient)
    client.get_summary.return_value = SUMMARY_RESPONSE
    client.get_upstreams.return_value = UPSTREAMS_RESPONSE
    client.get_query_types.return_value = QUERY_TYPES_RESPONSE
    client.get_version.return_value = VERSION_RESPONSE
    return client


@pytest.fixture
def http_client():
    return PiholeClient(host="localhost", port=80, password="secret", use_https=False)


@pytest.fixture
def passwordless_client():
    return PiholeClient(host="localhost", port=80, password="", use_https=False)
