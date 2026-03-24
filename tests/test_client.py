import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from pihole_exporter.client import PiholeClient

# --- __init__ ---


@pytest.mark.parametrize(
    "use_https,expected_scheme",
    [
        (False, "http://"),
        (True, "https://"),
    ],
)
def test_client_url_scheme(use_https, expected_scheme):
    client = PiholeClient(
        host="pihole.local", port=80, password="", use_https=use_https
    )
    assert client.base_url.startswith(expected_scheme)


def test_client_url_includes_host_and_port():
    client = PiholeClient(host="pihole.local", port=8080, password="", use_https=False)
    assert client.base_url == "http://pihole.local:8080"


def test_client_initial_sid_is_none(http_client):
    assert http_client._sid is None
    assert http_client._sid_expiry == 0.0


# --- authenticate ---


def test_authenticate_returns_sid(http_client):
    with patch.object(http_client._http, "post") as mock_post:
        mock_post.return_value = MagicMock(
            **{"json.return_value": {"session": {"sid": "abc123", "validity": 1800}}}
        )
        sid = http_client.authenticate()
    assert sid == "abc123"
    assert http_client._sid == "abc123"


def test_authenticate_posts_correct_url_and_payload(http_client):
    with patch.object(http_client._http, "post") as mock_post:
        mock_post.return_value = MagicMock(
            **{"json.return_value": {"session": {"sid": "x", "validity": 1800}}}
        )
        http_client.authenticate()
        mock_post.assert_called_once_with(
            "http://localhost:80/api/auth",
            json={"password": "secret"},
        )


def test_authenticate_sets_expiry_with_safety_margin(http_client):
    with patch.object(http_client._http, "post") as mock_post:
        mock_post.return_value = MagicMock(
            **{"json.return_value": {"session": {"sid": "x", "validity": 1800}}}
        )
        before = time.time()
        http_client.authenticate()
        after = time.time()
    # expiry = time.time() + 1800 - 60 = time.time() + 1740
    assert before + 1740 <= http_client._sid_expiry <= after + 1740


def test_authenticate_raises_on_http_error(http_client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )
    with (
        patch.object(http_client._http, "post", return_value=mock_resp),
        pytest.raises(httpx.HTTPStatusError),
    ):
        http_client.authenticate()


# --- _ensure_auth ---


def test_ensure_auth_skips_if_no_password(passwordless_client):
    with patch.object(passwordless_client, "authenticate") as mock_auth:
        passwordless_client._ensure_auth()
        mock_auth.assert_not_called()


def test_ensure_auth_calls_authenticate_when_no_sid(http_client):
    with patch.object(http_client, "authenticate") as mock_auth:
        http_client._ensure_auth()
        mock_auth.assert_called_once()


def test_ensure_auth_skips_when_session_valid(http_client):
    http_client._sid = "valid"
    http_client._sid_expiry = time.time() + 1000
    with patch.object(http_client, "authenticate") as mock_auth:
        http_client._ensure_auth()
        mock_auth.assert_not_called()


def test_ensure_auth_reauthenticates_when_session_expired(http_client):
    http_client._sid = "expired"
    http_client._sid_expiry = time.time() - 1
    with patch.object(http_client, "authenticate") as mock_auth:
        http_client._ensure_auth()
        mock_auth.assert_called_once()


# --- get ---


def test_get_sends_sid_header(http_client):
    http_client._sid = "mysid"
    http_client._sid_expiry = time.time() + 1000
    with patch.object(http_client._http, "get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, **{"json.return_value": {"ok": True}}
        )

        result = http_client.get("/api/stats/summary")

        assert result == {"ok": True}
        mock_get.assert_called_once_with(
            "http://localhost:80/api/stats/summary",
            headers={"X-FTL-SID": "mysid"},
        )


def test_get_retries_on_401_with_new_sid(http_client):
    """On 401, re-authenticates and retries the request with new SID."""
    http_client._sid = "oldsid"
    http_client._sid_expiry = time.time() + 1000

    resp_401 = MagicMock(status_code=401)
    resp_ok = MagicMock(status_code=200, **{"json.return_value": {"data": "ok"}})

    def set_new_sid():
        http_client._sid = "newsid"

    with (
        patch.object(
            http_client._http, "get", side_effect=[resp_401, resp_ok]
        ) as mock_get,
        patch.object(http_client, "authenticate", side_effect=set_new_sid),
    ):
        result = http_client.get("/api/stats/summary")

    assert result == {"data": "ok"}
    assert mock_get.call_count == 2
    # Second call should use the new SID
    second_call_headers = mock_get.call_args_list[1][1]["headers"]
    assert second_call_headers["X-FTL-SID"] == "newsid"


def test_get_no_retry_on_401_without_password(passwordless_client):
    """No re-authentication when no password is configured."""
    with patch.object(passwordless_client._http, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=401)
        passwordless_client.get("/api/stats/summary")
        assert mock_get.call_count == 1


def test_get_no_sid_header_without_password(passwordless_client):
    with patch.object(passwordless_client._http, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, **{"json.return_value": {}})
        passwordless_client.get("/api/stats/summary")
        called_headers = mock_get.call_args[1]["headers"]
        assert "X-FTL-SID" not in called_headers


# --- endpoint shortcuts ---


@pytest.mark.parametrize(
    "method,expected_endpoint",
    [
        ("get_summary", "/api/stats/summary"),
        ("get_upstreams", "/api/stats/upstreams"),
        ("get_query_types", "/api/stats/query_types"),
        ("get_version", "/api/info/version"),
    ],
)
def test_endpoint_methods_call_correct_path(
    method, expected_endpoint, passwordless_client
):
    with patch.object(passwordless_client, "get", return_value={}) as mock_get:
        getattr(passwordless_client, method)()
        mock_get.assert_called_once_with(expected_endpoint)
