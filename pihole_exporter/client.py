"""HTTP client for the Pi-hole v6 API with session management."""

import time

import httpx

from pihole_exporter.logger import LOGGER


class PiholeClient:
    """HTTP client for the Pi-hole v6 API with session management."""

    def __init__(self, host: str, port: int, password: str, use_https: bool) -> None:
        scheme = "https" if use_https else "http"
        self.base_url = f"{scheme}://{host}:{port}"
        self.password = password
        self._sid: str | None = None
        self._sid_expiry: float = 0.0

    def authenticate(self) -> str:
        """POST /api/auth → returns the session ID."""
        resp = httpx.post(
            f"{self.base_url}/api/auth",
            json={"password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        session = data.get("session", {})
        sid = session.get("sid", "")
        validity = session.get("validity", 1800)
        self._sid = sid
        self._sid_expiry = time.time() + validity - 60  # 60s safety margin
        LOGGER.debug("Authentication successful, session valid for %ds", validity)
        return sid

    def _ensure_auth(self) -> None:
        """Ensure a valid session exists."""
        if not self.password:
            return
        if self._sid is None or time.time() >= self._sid_expiry:
            self.authenticate()

    def get(self, endpoint: str) -> dict:
        """GET an endpoint with session header, retry once on 401."""
        self._ensure_auth()
        headers = {}
        if self._sid:
            headers["X-FTL-SID"] = self._sid

        resp = httpx.get(
            f"{self.base_url}{endpoint}",
            headers=headers,
            timeout=10,
        )

        if resp.status_code == 401 and self.password:
            LOGGER.debug("Session expired, re-authenticating...")
            self.authenticate()
            headers["X-FTL-SID"] = self._sid
            resp = httpx.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=10,
            )

        resp.raise_for_status()
        return resp.json()

    def get_summary(self) -> dict:
        return self.get("/api/stats/summary")

    def get_upstreams(self) -> dict:
        return self.get("/api/stats/upstreams")

    def get_query_types(self) -> dict:
        return self.get("/api/stats/query_types")

    def get_version(self) -> dict:
        return self.get("/api/info/version")

    def get_top_clients(self) -> dict:
        return self.get("/api/stats/top_clients")
