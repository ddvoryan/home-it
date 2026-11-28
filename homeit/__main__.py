"""home-it CLI.  Usage:  python -m homeit <group> <command> [...]"""
from __future__ import annotations

import argparse
import sys

from homeit import config, secrets


def _syn_set_password(_a):
    cfg = config.synology()
    secrets.set_interactive(cfg.keyring_service, cfg.username)


def _syn_pin_cert(_a):
    from homeit.synology.api import fetch_cert_sha256
    cfg = config.synology()
    fp = fetch_cert_sha256(cfg.host, cfg.dsm_port)
    print(f"current : {fp}")
    print(f"pinned  : {cfg.cert_sha256}")
    if cfg.cert_sha256 and fp == cfg.cert_sha256.replace(':', '').lower():
        print("OK: matches pin")
    else:
        print(f"MISMATCH or unpinned. If the DSM cert was intentionally renewed, set "
              f"cert_sha256 in {config.config_path()}")
        sys.exit(2)


def _syn_probe(_a):
    from homeit import synology
    from homeit.synology import ssh
    cfg = config.synology()
    ok = True
    r = ssh.run(cfg.ssh_alias, "id; hostname")
    print(f"[ssh]  {'OK' if r.ok else 'FAIL'}  {r.out.strip() or r.err}")
    ok &= r.ok
    pw = synology.password(cfg)
    r = ssh.run(cfg.ssh_alias, "id -u", sudo_password=pw)
    print(f"[sudo] {'OK' if r.ok and r.out.strip() == '0' else 'FAIL'}  {r.out.strip() or r.err}")
    ok &= r.ok
    try:
        with synology.dsm(cfg) as d:
            info = d.call("SYNO.Core.System", "info", 1)
            print(f"[api]  OK  {info.get('model')} DSM {info.get('firmware_ver')}")
    except Exception as e:  # noqa: BLE001
        print(f"[api]  FAIL  {e}")
        ok = False
    sys.exit(0 if ok else 1)


def _syn_inventory(a):
    from homeit.synology import inventory
    inventory.main(json_only=a.json, out=a.out)


def _syn_check(_a):
    from homeit.synology import monitor
    monitor.check()


def _syn_alerts(a):
    from homeit.synology import monitor
    monitor.alerts(ack=a.ack, as_json=a.json, history_hours=a.history)


def _syn_update_images(a):
    from homeit.synology import updates
    updates.main(dry_run=a.dry_run, only=a.only, force_rollback=a.force_rollback, cleanup_only=a.cleanup_previous)


def _syn_usb_sync(a):
    from homeit.synology import usbsync
    usbsync.main(dry_run=a.dry_run, force=a.force)


def _redirect_if_windowless():
    """Under pythonw (Task Scheduler) there is no console: log to ~/.home-it/logs/homeit.log."""
    if sys.stdout is None or sys.stderr is None:
        d = config.config_dir() / "logs"
        d.mkdir(parents=True, exist_ok=True)
        log = d / "homeit.log"
        if log.exists() and log.stat().st_size > 5_000_000:
            log.replace(d / "homeit.log.1")
        sys.stdout = sys.stderr = open(log, "a", encoding="utf-8", buffering=1)
        print(f"\n=== {' '.join(sys.argv[1:])}")


def _ha_set_token(_a):
    cfg = config.homeassistant()
    print("Paste the long-lived access token (input is hidden).")
    secrets.set_interactive(cfg.keyring_service, cfg.token_name)


def _ha_probe(_a):
    from homeit.homeassistant.client import HA
    try:
        with HA() as ha:
            u = ha.ws("auth/current_user")
            n = len(ha.ws("config_entries/get"))
            print(f"[ha] OK  HA {ha.version} as '{u.get('name')}' (admin={u.get('is_admin')}), {n} integrations")
    except Exception as e:  # noqa: BLE001
        print(f"[ha] FAIL  {e}")
        sys.exit(1)


def _ha_inventory(a):
    from homeit.homeassistant import inventory
    inventory.main(json_only=a.json, out=a.out)


def _ha_deploy_panel(a):
    from homeit.homeassistant import panel
    panel.deploy(restart=a.restart, dry_run=a.dry_run)


def _secret_set(a):
    secrets.set_interactive(a.service, a.username)


def _secret_check(a):
    print("present" if secrets.exists(a.service, a.username) else "missing")


def main(argv=None):
    p = argparse.ArgumentParser(prog="homeit")
    g = p.add_subparsers(dest="group", required=True)

    syn = g.add_parser("synology").add_subparsers(dest="cmd", required=True)
    syn.add_parser("set-password", help="store the DSM service-account password in the keyring").set_defaults(fn=_syn_set_password)
    syn.add_parser("pin-cert", help="compare DSM TLS cert with the pinned fingerprint").set_defaults(fn=_syn_pin_cert)
    syn.add_parser("probe", help="test SSH, sudo and DSM API connectivity").set_defaults(fn=_syn_probe)
    inv = syn.add_parser("inventory", help="collect a health/config/container snapshot")
    inv.add_argument("--json", action="store_true", help="print raw JSON instead of the summary")
    inv.add_argument("--out", help="also write the summary markdown to this path")
    inv.set_defaults(fn=_syn_inventory)
    syn.add_parser("check", help="hourly: inventory + queue alerts for new/escalated/resolved findings").set_defaults(fn=_syn_check)
    al = syn.add_parser("alerts", help="show (or --ack) queued alerts")
    al.add_argument("--ack", action="store_true", help="mark all pending alerts as delivered")
    al.add_argument("--json", action="store_true")
    al.add_argument("--history", type=int, metavar="HOURS", help="show delivered + pending alerts from the last N hours")
    al.set_defaults(fn=_syn_alerts)
    up = syn.add_parser("update-images", help="weekly: update container images with health check + rollback")
    up.add_argument("--dry-run", action="store_true", help="only list targets")
    up.add_argument("--only", nargs="+", metavar="NAME", help="limit to these containers")
    up.add_argument("--force-rollback", action="store_true", help=argparse.SUPPRESS)
    up.add_argument("--cleanup-previous", action="store_true",
                    help="only remove leftover homeit-prev rollback images, update nothing")
    up.set_defaults(fn=_syn_update_images)
    us = syn.add_parser("usb-sync", help="weekly: rebuild the single-version USB backup task's folder list from rules")
    us.add_argument("--dry-run", action="store_true", help="show what would change")
    us.add_argument("--force", action="store_true", help="allow removing more than max_drop_pct of entries")
    us.set_defaults(fn=_syn_usb_sync)

    ha = g.add_parser("ha", help="Home Assistant").add_subparsers(dest="cmd", required=True)
    ha.add_parser("set-token", help="store the HA long-lived access token in the keyring").set_defaults(fn=_ha_set_token)
    ha.add_parser("probe", help="test the HA API token and WebSocket").set_defaults(fn=_ha_probe)
    dp = ha.add_parser("deploy-panel", help="upload the wall/phone panel, its config and helper scripts")
    dp.add_argument("--restart", action="store_true", help="restart HA if the YAML changed (about 6 minutes)")
    dp.add_argument("--dry-run", action="store_true", help="show what would change")
    dp.set_defaults(fn=_ha_deploy_panel)
    inv = ha.add_parser("inventory", help="integrations, health, devices, re-auth needs")
    inv.add_argument("--json", action="store_true", help="print the raw snapshot")
    inv.add_argument("--out", help="also write the summary markdown to this path")
    inv.set_defaults(fn=_ha_inventory)

    sec = g.add_parser("secret").add_subparsers(dest="cmd", required=True)
    s = sec.add_parser("set"); s.add_argument("service"); s.add_argument("username"); s.set_defaults(fn=_secret_set)
    s = sec.add_parser("check"); s.add_argument("service"); s.add_argument("username"); s.set_defaults(fn=_secret_check)

    _redirect_if_windowless()
    a = p.parse_args(argv)
    try:
        a.fn(a)
    except Exception:
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
