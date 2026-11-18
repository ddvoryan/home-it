"""Synology DSM integration (SSH + DSM Web API)."""
from __future__ import annotations

from homeit import config, secrets
from homeit.synology.api import DSM


def password(cfg: config.SynologyConfig | None = None) -> str:
    cfg = cfg or config.synology()
    return secrets.get(cfg.keyring_service, cfg.username)


def dsm(cfg: config.SynologyConfig | None = None) -> DSM:
    """Unauthenticated-until-entered DSM client: `with dsm() as d: d.call(...)`."""
    cfg = cfg or config.synology()
    if not cfg.cert_sha256:
        raise SystemExit("cert_sha256 not set in config; run: python -m homeit synology pin-cert")
    return DSM(cfg.host, cfg.dsm_port, cfg.username, password(cfg), cfg.cert_sha256)
