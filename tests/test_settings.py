from unittest.mock import patch

import pytest
from pydantic import ValidationError

from pihole_exporter.settings import Settings


@patch.dict("os.environ", {}, clear=True)
def test_settings_default_values():
    s = Settings()
    assert s.pihole_host == "localhost"
    assert s.pihole_port == 80
    assert s.pihole_password == ""
    assert s.pihole_https is False
    assert s.scrape_interval == 30
    assert s.exporter_port == 9666
    assert s.log_level == "INFO"


@patch.dict(
    "os.environ",
    {
        "PIHOLE_HOST": "pihole.local",
        "PIHOLE_PORT": "8080",
        "PIHOLE_PASSWORD": "s3cr3t",
        "PIHOLE_HTTPS": "true",
        "SCRAPE_INTERVAL": "60",
        "EXPORTER_PORT": "9999",
        "LOG_LEVEL": "DEBUG",
    },
    clear=True,
)
def test_settings_reads_all_env_vars():
    s = Settings()
    assert s.pihole_host == "pihole.local"
    assert s.pihole_port == 8080
    assert s.pihole_password == "s3cr3t"
    assert s.pihole_https is True
    assert s.scrape_interval == 60
    assert s.exporter_port == 9999
    assert s.log_level == "DEBUG"


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ],
)
def test_settings_pihole_https_bool_parsing(env_value, expected):
    with patch.dict("os.environ", {"PIHOLE_HTTPS": env_value}, clear=False):
        s = Settings()
        assert s.pihole_https is expected


@pytest.mark.parametrize(
    "field,env_var,value",
    [
        ("pihole_host", "PIHOLE_HOST", "192.168.1.1"),
        ("pihole_password", "PIHOLE_PASSWORD", "mypassword"),
        ("log_level", "LOG_LEVEL", "WARNING"),
    ],
)
def test_settings_individual_string_fields(field, env_var, value):
    with patch.dict("os.environ", {env_var: value}, clear=False):
        s = Settings()
        assert getattr(s, field) == value


@pytest.mark.parametrize(
    "field,env_var,value",
    [
        ("pihole_port", "PIHOLE_PORT", 9090),
        ("scrape_interval", "SCRAPE_INTERVAL", 120),
        ("exporter_port", "EXPORTER_PORT", 8080),
    ],
)
def test_settings_individual_int_fields(field, env_var, value):
    with patch.dict("os.environ", {env_var: str(value)}, clear=False):
        s = Settings()
        assert getattr(s, field) == value


@patch.dict("os.environ", {"PIHOLE_PORT": "not-a-number"}, clear=False)
def test_settings_invalid_port_raises_validation_error():
    with pytest.raises(ValidationError):
        Settings()


@patch.dict("os.environ", {"SCRAPE_INTERVAL": "abc"}, clear=False)
def test_settings_invalid_scrape_interval_raises_validation_error():
    with pytest.raises(ValidationError):
        Settings()
