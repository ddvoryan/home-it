"""Site configuration.

Site-specific values (hostnames, usernames, cert pins) live OUTSIDE the repo so
this public repository never contains details of the home network.

Location: ~/.home-it/config.toml (override with HOMEIT_CONFIG).
See config.example.toml in the repo root for the schema.

Note: deliberately NOT under %APPDATA%/%LOCALAPPDATA% -- on Windows, packaged
(MSIX) apps get those paths silently redirected into a private per-app copy,
so files written from one app would be invisible to the user's shell or to
Task Scheduler jobs.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


def config_dir() -> Path:
    return Path(os.environ.get("HOMEIT_HOME") or Path.home() / ".home-it")


def data_dir() -> Path:
    """Local, non-repo storage for snapshots/reports (may contain serials, IPs)."""
    d = config_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return Path(os.environ.get("HOMEIT_CONFIG") or config_dir() / "config.toml")


@dataclass(frozen=True)
class SynologyConfig:
    host: str
    username: str
    ssh_alias: str = "nas"
    dsm_port: int = 5001
    cert_sha256: str | None = None  # pinned DSM TLS cert fingerprint (hex)
    keyring_service: str = "home-it/synology"
    docker_bin: str = "/usr/local/bin/docker"
    update_exclude: tuple[str, ...] = ()  # container names the weekly image update must skip

    def __post_init__(self):
        object.__setattr__(self, "update_exclude", tuple(self.update_exclude))


@dataclass(frozen=True)
class HomeAssistantConfig:
    url: str                                  # e.g. http://my-nas:8123 (no trailing slash)
    keyring_service: str = "home-it/homeassistant"
    token_name: str = "homeit"                # keyring "username" the long-lived token is stored under
    verify_tls: bool = True                   # only relevant for https URLs
    host_config_dir: str = ""                 # HA's /config folder as seen on the NAS (for `ha deploy-panel`)


def load() -> dict:
    p = config_path()
    if not p.exists():
        raise FileNotFoundError(
            f"No config at {p}. Copy config.example.toml there and fill it in."
        )
    with p.open("rb") as f:
        return tomllib.load(f)


def synology() -> SynologyConfig:
    return SynologyConfig(**load()["synology"])


def homeassistant() -> HomeAssistantConfig:
    c = load().get("homeassistant")
    if not c:
        raise SystemExit(f"No [homeassistant] section in {config_path()}; see config.example.toml")
    return HomeAssistantConfig(**c)
