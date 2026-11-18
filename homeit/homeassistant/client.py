"""Minimal Home Assistant client: REST + WebSocket API with a long-lived access token.

- Auth: a long-lived access token (LLAT) belonging to a dedicated HA user, read from
  the OS keyring. It is sent only in the Authorization header / WebSocket auth
  message, never in a URL, argv, env var or log line.
- Transport: whatever `url` in the site config says. On this NAS DSM forbids SSH
  port-forwarding, so a LAN http URL is expected; prefer https once HA sits behind
  a TLS reverse proxy.
"""
from __future__ import annotations

import itertools
import json
from typing import Any

import requests
import websocket  # websocket-client

from homeit import config, secrets


class HAError(RuntimeError):
    pass


def token(cfg: config.HomeAssistantConfig | None = None) -> str:
    cfg = cfg or config.homeassistant()
    return secrets.get(cfg.keyring_service, cfg.token_name)


class HA:
    """`with HA() as ha: ha.ws("config_entries/get")`; REST via `ha.get("/api/config")`."""

    def __init__(self, cfg: config.HomeAssistantConfig | None = None, timeout: int = 30):
        self.cfg = cfg or config.homeassistant()
        self.base = self.cfg.url.rstrip("/")
        self.timeout = timeout
        self._token = token(self.cfg)
        self.http = requests.Session()
        self.http.headers["Authorization"] = f"Bearer {self._token}"
        self.http.verify = self.cfg.verify_tls
        self._ws: websocket.WebSocket | None = None
        self._ids = itertools.count(1)
        self.version: str | None = None

    # ---- REST -------------------------------------------------------------
    def get(self, path: str) -> Any:
        r = self.http.get(self.base + path, timeout=self.timeout)
        if r.status_code == 401:
            raise HAError("401 Unauthorized: token missing, revoked or wrong user "
                          "(re-run: python -m homeit ha set-token)")
        r.raise_for_status()
        return r.json()

    # ---- WebSocket --------------------------------------------------------
    def __enter__(self) -> "HA":
        ws_url = ("wss://" if self.base.startswith("https") else "ws://") + \
            self.base.split("://", 1)[1] + "/api/websocket"
        sslopt = None if self.cfg.verify_tls else {"cert_reqs": 0}
        self._ws = websocket.create_connection(ws_url, timeout=self.timeout, sslopt=sslopt)
        hello = json.loads(self._ws.recv())
        if hello.get("type") != "auth_required":
            raise HAError(f"unexpected greeting: {hello.get('type')}")
        self._ws.send(json.dumps({"type": "auth", "access_token": self._token}))
        res = json.loads(self._ws.recv())
        if res.get("type") != "auth_ok":
            raise HAError(f"WebSocket auth failed: {res.get('message', res.get('type'))}")
        self.version = res.get("ha_version")
        return self

    def __exit__(self, *exc) -> None:
        if self._ws:
            self._ws.close()
            self._ws = None

    def ws(self, type_: str, **payload) -> Any:
        if not self._ws:
            raise HAError("WebSocket not open; use `with HA() as ha:`")
        mid = next(self._ids)
        self._ws.send(json.dumps({"id": mid, "type": type_, **payload}))
        while True:
            msg = json.loads(self._ws.recv())
            if msg.get("id") != mid:
                continue  # stray event/ack from an earlier call
            if msg.get("type") == "result":
                if not msg.get("success"):
                    err = msg.get("error") or {}
                    raise HAError(f"{type_}: {err.get('code')}: {err.get('message')}")
                return msg.get("result")
