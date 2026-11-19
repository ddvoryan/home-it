"""Deploy the wall/phone panel (panel_custom) to Home Assistant.

What goes where:
- Generic panel code (this repo, homeit/homeassistant/panel/*.js) -> <HA config>/www/home-panel/
  (served at /local/home-panel/, which needs no login, so it must never contain site details).
- The site's panel config (entity ids, names) lives privately in ~/.home-it/homeassistant/home_panel.json
  and is written to <HA config>/home_panel.yaml (JSON is valid YAML), which configuration.yaml includes as
  `panel_custom: !include home_panel.yaml`. HA only sends it to logged-in users.
- Helper scripts the panel calls (Nest fan timer, laser session start/end) are generated from that config
  and saved through HA's script config API.

YAML changes need a Home Assistant restart (`--restart`); code-only changes do not: loader.js never changes
and imports home-panel.js?v=<hash>, reading the hash from version.txt without caching.
"""
from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from homeit import config, synology
from homeit.homeassistant.client import HA
from homeit.synology import ssh

PANEL_SRC = Path(__file__).parent / "panel"
INCLUDE_LINE = "panel_custom: !include home_panel.yaml"


def site_config_path() -> Path:
    return config.config_dir() / "homeassistant" / "home_panel.json"


class Host:
    """File access to HA's /config folder on the NAS (root via sudo, files owned like the folder)."""

    def __init__(self):
        self.syn = config.synology()
        ha = config.homeassistant()
        if not ha.host_config_dir:
            raise SystemExit("Set host_config_dir in the [homeassistant] section of the config file.")
        self.root = ha.host_config_dir.rstrip("/")
        self.pw = synology.password(self.syn)
        r = self.run(f"stat -c '%u %g' {shlex.quote(self.root)}")
        self.uid, self.gid = r.out.split()

    def run(self, cmd: str, timeout: int = 60) -> ssh.Result:
        r = ssh.run(self.syn.ssh_alias, cmd, sudo_password=self.pw, timeout=timeout)
        if not r.ok:
            raise RuntimeError(f"NAS command failed ({r.rc}): {cmd}\n{r.err}")
        return r

    def read(self, rel: str) -> str | None:
        p = shlex.quote(f"{self.root}/{rel}")
        r = ssh.run(self.syn.ssh_alias, f"test -f {p} && cat {p}", sudo_password=self.pw, timeout=60)
        return r.out if r.ok else None

    def write(self, rel: str, data: bytes) -> None:
        tmp = f"/tmp/home-it-{uuid.uuid4().hex}"
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", self.syn.ssh_alias, f"umask 077 && cat > {tmp}"],
                           input=data, capture_output=True, timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if p.returncode != 0:
            raise RuntimeError(f"upload failed: {p.stderr.decode(errors='replace').strip()}")
        dest = shlex.quote(f"{self.root}/{rel}")
        self.run(f"install -D -o {self.uid} -g {self.gid} -m 644 {tmp} {dest}; rc=$?; rm -f {tmp}; exit $rc")


def _scripts(cfg: dict) -> dict[str, dict]:
    """HA scripts the panel relies on, derived from the panel config."""
    out: dict[str, dict] = {}
    for r in cfg.get("rooms", []):
        if r.get("kind") == "climate" and r.get("fan_script"):
            ent = {"entity_id": r["climate"]}
            out[r["fan_script"].split(".", 1)[1]] = {
                "alias": f"Home panel: run the {r.get('name', 'thermostat')} fan for a while",
                "description": "Started by the home panel: fan on, wait, fan off. Managed by home-it.",
                "icon": "mdi:fan-clock", "mode": "restart",
                "fields": {"minutes": {"name": "Minutes", "default": 15, "selector": {"number": {"min": 1, "max": 720, "unit_of_measurement": "min"}}}},
                "sequence": [
                    {"action": "climate.set_fan_mode", "target": ent, "data": {"fan_mode": "on"}},
                    {"delay": {"minutes": "{{ minutes | int(15) }}"}},
                    {"action": "climate.set_fan_mode", "target": ent, "data": {"fan_mode": "off"}},
                ],
            }
        if r.get("kind") == "workshop":
            outlets = {o["key"]: o["switch"] for o in r.get("outlets", [])}
            ex = outlets[r["exhaust"]]
            if r.get("start_script"):
                seq = []
                if r.get("end_script"):
                    seq.append({"action": "script.turn_off", "target": {"entity_id": r["end_script"]}})
                seq.append({"action": "switch.turn_on", "target": {"entity_id": [outlets[k] for k in r.get("session_on", [])]}})
                out[r["start_script"].split(".", 1)[1]] = {
                    "alias": "Workshop: start laser session",
                    "description": "Powers the laser, its PC, air assist and exhaust. Managed by home-it.",
                    "icon": "mdi:laser-pointer", "mode": "single", "sequence": seq,
                }
            if r.get("end_script"):
                out[r["end_script"].split(".", 1)[1]] = {
                    "alias": "Workshop: end laser session",
                    "description": "Laser and air assist off, exhaust keeps clearing fumes, then off. Managed by home-it.",
                    "icon": "mdi:fan-clock", "mode": "restart",
                    "sequence": [
                        {"action": "switch.turn_off", "target": {"entity_id": [outlets[k] for k in r.get("session_off", [])]}},
                        {"action": "switch.turn_on", "target": {"entity_id": ex}},
                        {"delay": {"minutes": int(r.get("exhaust_runon_minutes", 3))}},
                        {"action": "switch.turn_off", "target": {"entity_id": ex}},
                    ],
                }
    return out


def _wait_running(timeout_s: int = 600) -> None:
    t0 = time.time()
    time.sleep(20)
    while time.time() - t0 < timeout_s:
        try:
            with HA(timeout=10) as ha:
                if ha.ws("get_config").get("state") == "RUNNING":
                    print(f"  HA is running again after {int(time.time() - t0)} s")
                    return
        except Exception:  # noqa: BLE001 - HA is still starting
            pass
        time.sleep(15)
    raise SystemExit("HA did not report RUNNING within 10 minutes; check the container log.")


def deploy(restart: bool = False, dry_run: bool = False) -> None:
    site = json.loads(site_config_path().read_text(encoding="utf-8"))
    panel_cfg = site["config"]
    js = (PANEL_SRC / "home-panel.js").read_bytes()
    version = hashlib.sha256(js).hexdigest()[:12]
    loader = (PANEL_SRC / "loader.js").read_bytes()
    # HA serves /local/ with a 31-day cache. The loader URL carries the loader's own hash, so a device that
    # cached an older loader gets a new URL. Changing it is a YAML change, so it needs one HA restart.
    loader_version = hashlib.sha256(loader).hexdigest()[:8]

    entry = {"name": "home-panel", "module_url": f"/local/home-panel/loader.js?v={loader_version}",
             **site.get("panel", {}), "config": panel_cfg}
    yaml_text = ("# Managed by home-it (`homeit ha deploy-panel`); edit ~/.home-it/homeassistant/home_panel.json instead.\n"
                 + json.dumps([entry], indent=2, ensure_ascii=False) + "\n")

    host = Host()
    changed_yaml = False
    cur_cfg = host.read("configuration.yaml") or ""
    if INCLUDE_LINE not in cur_cfg:
        if "panel_custom" in cur_cfg:
            raise SystemExit("configuration.yaml already has a different panel_custom section; merge it by hand.")
        print("- configuration.yaml: adding the panel_custom include (backup kept next to it)")
        if not dry_run:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            host.run(f"cp -p {shlex.quote(host.root + '/configuration.yaml')} {shlex.quote(host.root + f'/configuration.yaml.home-it-{stamp}.bak')}")
            new = cur_cfg.rstrip("\n") + "\n\n# Wall and phone panel (home-it). Entity mapping lives in home_panel.yaml.\n" + INCLUDE_LINE + "\n"
            host.write("configuration.yaml", new.encode())
        changed_yaml = True
    if (host.read("home_panel.yaml") or "") != yaml_text:
        print("- home_panel.yaml: updated")
        if not dry_run:
            host.write("home_panel.yaml", yaml_text.encode())
        changed_yaml = True
    print(f"- www/home-panel: home-panel.js ({len(js) // 1024} KB, version {version}), loader.js, version.txt")
    if not dry_run:
        host.write("www/home-panel/home-panel.js", js)
        host.write("www/home-panel/loader.js", loader)
        host.write("www/home-panel/version.txt", version.encode())  # last, so the new build is in place first

    with HA() as ha:
        for sid, body in _scripts(panel_cfg).items():
            r = ha.http.get(f"{ha.base}/api/config/script/config/{sid}", timeout=30)
            if r.status_code == 200 and r.json() == body:
                continue
            print(f"- script.{sid}: {'updated' if r.status_code == 200 else 'created'}")
            if not dry_run:
                p = ha.http.post(f"{ha.base}/api/config/script/config/{sid}", json=body, timeout=30)
                p.raise_for_status()
        if changed_yaml and not dry_run:
            res = ha.http.post(f"{ha.base}/api/config/core/check_config", timeout=120).json()
            if res.get("result") != "valid":
                raise SystemExit(f"HA config check failed, not restarting:\n{res.get('errors')}")
            print("- HA configuration check: valid")

    if dry_run:
        print("Dry run: nothing written.")
    elif changed_yaml and restart:
        print("- restarting Home Assistant (takes about 6 minutes)")
        with HA() as ha:
            try:
                ha.http.post(f"{ha.base}/api/services/homeassistant/restart", json={}, timeout=10)
            except Exception:  # noqa: BLE001 - the connection drops while HA stops
                pass
        _wait_running()
    elif changed_yaml:
        print("YAML changed: restart Home Assistant to load it (rerun with --restart).")
    else:
        print("Code updated; reload the panel page to pick it up.")
