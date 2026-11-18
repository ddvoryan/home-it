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

    sec = g.add_parser("secret").add_subparsers(dest="cmd", required=True)
    s = sec.add_parser("set"); s.add_argument("service"); s.add_argument("username"); s.set_defaults(fn=_secret_set)
    s = sec.add_parser("check"); s.add_argument("service"); s.add_argument("username"); s.set_defaults(fn=_secret_check)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
