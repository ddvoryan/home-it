"""Minimal DSM Web API client.

- TLS: DSM ships a self-signed "Synology Inc. CA" cert, so instead of disabling
  verification we pin the server certificate's SHA-256 fingerprint.
- Auth: SYNO.API.Auth login via POST (credentials never appear in a URL),
  session id + SynoToken, and logout on exit.
"""
from __future__ import annotations

import hashlib
import json
import socket
import ssl
from typing import Any

import requests
from requests.adapters import HTTPAdapter

AUTH_ERRORS = {
    400: "invalid username or password",
    401: "account disabled",
    402: "permission denied",
    403: "2-step verification code required (disable 2FA for the service account)",
    404: "2-step verification failed",
    406: "OTP enforcement: 2FA must be set up for this account",
    407: "this client IP is blocked (DSM auto-block)",
    408: "password expired; change it in DSM",
    409: "password must be changed",
    410: "password must be changed",
}


class DSMError(RuntimeError):
    def __init__(self, api: str, method: str, code: int | None, detail: Any = None):
        self.api, self.method, self.code, self.detail = api, method, code, detail
        msg = f"{api}.{method} failed (code {code})"
        if api == "SYNO.API.Auth" and code in AUTH_ERRORS:
            msg += f": {AUTH_ERRORS[code]}"
        super().__init__(msg)


def fetch_cert_sha256(host: str, port: int) -> str:
    """Return the hex SHA-256 of the server's leaf certificate (for pinning)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=10) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as s:
            return hashlib.sha256(s.getpeercert(binary_form=True)).hexdigest()


class _PinnedAdapter(HTTPAdapter):
    def __init__(self, fingerprint: str, **kw):
        self._fp = fingerprint.replace(":", "").lower()
        super().__init__(**kw)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_fingerprint"] = self._fp
        super().init_poolmanager(*args, **kwargs)


class DSM:
    def __init__(self, host: str, port: int, username: str, password: str,
                 cert_sha256: str, timeout: int = 30, session_name: str = "home-it"):
        self.base = f"https://{host}:{port}/webapi"
        self.username, self._password = username, password
        self.timeout, self.session_name = timeout, session_name
        self.s = requests.Session()
        self.s.verify = False  # trust comes from the fingerprint pin below
        self.s.mount(f"https://{host}:{port}", _PinnedAdapter(cert_sha256))
        self.sid: str | None = None
        self.apis: dict[str, dict] = {}

    # -- lifecycle -------------------------------------------------------
    def __enter__(self) -> "DSM":
        self.login()
        return self

    def __exit__(self, *exc) -> None:
        self.logout()

    def load_api_info(self) -> dict[str, dict]:
        r = self.s.get(f"{self.base}/query.cgi", timeout=self.timeout, params={
            "api": "SYNO.API.Info", "version": 1, "method": "query", "query": "all"})
        r.raise_for_status()
        self.apis = r.json()["data"]
        return self.apis

    def login(self) -> None:
        if not self.apis:
            self.load_api_info()
        info = self.apis["SYNO.API.Auth"]
        r = self.s.post(f"{self.base}/{info['path']}", timeout=self.timeout, data={
            "api": "SYNO.API.Auth", "version": min(6, info["maxVersion"]),
            "method": "login", "account": self.username, "passwd": self._password,
            "session": self.session_name, "format": "sid", "enable_syno_token": "yes",
        })
        r.raise_for_status()
        body = r.json()
        if not body.get("success"):
            raise DSMError("SYNO.API.Auth", "login", body.get("error", {}).get("code"))
        self.sid = body["data"]["sid"]
        token = body["data"].get("synotoken")
        if token:
            self.s.headers["X-SYNO-TOKEN"] = token

    def logout(self) -> None:
        if not self.sid:
            return
        try:
            self.call("SYNO.API.Auth", "logout", 1, session=self.session_name)
        except Exception:
            pass
        self.sid = None

    # -- calls -----------------------------------------------------------
    def has(self, api: str) -> bool:
        return api in self.apis

    def call(self, api: str, method: str, version: int | None = None, **params) -> Any:
        """POST a call. dict/list/bool params are JSON-encoded as DSM expects."""
        if api not in self.apis:
            raise DSMError(api, method, None, "API not present on this DSM")
        info = self.apis[api]
        v = info["maxVersion"] if version is None else min(version, info["maxVersion"])
        data = {"api": api, "method": method, "version": v}
        for k, val in params.items():
            data[k] = json.dumps(val) if isinstance(val, (dict, list, bool)) else val
        if self.sid:
            data["_sid"] = self.sid
        r = self.s.post(f"{self.base}/{info['path']}", data=data, timeout=self.timeout)
        r.raise_for_status()
        body = r.json()
        if not body.get("success"):
            err = body.get("error", {})
            raise DSMError(api, method, err.get("code"), err)
        return body.get("data")
