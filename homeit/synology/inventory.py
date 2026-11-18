"""Synology health / config / Container Manager inventory.

Read-only. Collects from the DSM Web API (structured health, storage, backups,
updates, Container Manager) plus SSH+sudo (SMART attributes, docker inspect /
stats), evaluates findings, saves a redacted JSON snapshot and a Markdown
report under ~/.home-it/data/synology/, and prints the report.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeit import config, synology
from homeit.synology import ssh

SENSITIVE_KEY = re.compile(r"(pass|secret|token|apikey|api_key|refresh|cookie|sid|otp)", re.I)
SMART_IDS = {5: "reallocated", 9: "power_on_hours", 187: "reported_uncorrect", 188: "cmd_timeout",
             194: "temp_c", 197: "pending", 198: "offline_uncorrect", 199: "udma_crc"}
SEV_ORDER = {"critical": 0, "warning": 1, "info": 2}


# --------------------------------------------------------------------------- helpers
def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if SENSITIVE_KEY.search(str(k)) and isinstance(v, (str, int)) and v not in ("", None):
                out[k] = "<redacted>"
            elif k == "Env" and isinstance(v, list):  # container env: keep names only
                out[k] = sorted({str(e).split("=", 1)[0] for e in v})
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def _vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def _gb(b) -> float:
    return round(int(b) / 1e9, 1)


def _pct(used, total) -> float:
    return round(100 * int(used) / int(total), 1) if int(total) else 0.0


def _try(fn, errors: list, label: str):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - collection must be best-effort
        errors.append(f"{label}: {e}")
        return None


# --------------------------------------------------------------------------- collection
def collect() -> dict:
    cfg = config.synology()
    errors: list[str] = []
    snap: dict[str, Any] = {"collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "host": cfg.host, "errors": errors}
    pw = synology.password(cfg)

    with synology.dsm(cfg) as d:
        c = lambda api, m, v, **p: _try(lambda: d.call(api, m, v, **p), errors, f"{api}.{m}")  # noqa: E731
        snap["system"] = c("SYNO.Core.System", "info", 1)
        snap["system_status"] = c("SYNO.Core.System.Status", "get", 1)
        snap["utilization"] = c("SYNO.Core.System.Utilization", "get", 1)
        snap["storage"] = c("SYNO.Storage.CGI.Storage", "load_info", 1)
        snap["usb"] = c("SYNO.Core.ExternalDevice.Storage.USB", "list", 1, additional=["all"])
        snap["dsm_update"] = c("SYNO.Core.Upgrade.Server", "check", 2)
        snap["dsm_update_settings"] = c("SYNO.Core.Upgrade.Setting", "get", 1)
        snap["pkg_update_settings"] = c("SYNO.Core.Package.Setting", "get", 1)
        installed = c("SYNO.Core.Package", "list", 2, additional=["status", "startable"]) or {}
        catalog = c("SYNO.Core.Package.Server", "list", 2, blforcereload=False, blloadothers=False) or {}
        snap["packages"] = _packages(installed, catalog)
        tasks = (c("SYNO.Backup.Task", "list", 1) or {}).get("task_list", [])
        snap["backups"] = []
        for t in tasks:
            st = c("SYNO.Backup.Task", "status", 1, task_id=t["task_id"], blOnline=False,
                   additional=["last_bkp_time", "next_bkp_time", "last_bkp_result", "last_bkp_success_time"]) or {}
            snap["backups"].append({"name": t["name"], "type": t.get("type"), "state": t.get("state"),
                                    "status": st.get("status"), "last_result": st.get("last_bkp_result"),
                                    "last_error": st.get("last_bkp_error"), "last_run": st.get("last_bkp_time"),
                                    "last_success": st.get("last_bkp_success_time"), "next_run": st.get("next_bkp_time"),
                                    "schedule_days": ((st.get("schedule") or {}).get("schedule") or {}).get("week_name")})
        snap["security_advisor"] = c("SYNO.Core.SecurityScan.Status", "system_get", 1)
        snap["firewall"] = c("SYNO.Core.Security.Firewall", "get", 1)
        snap["quickconnect"] = c("SYNO.Core.QuickConnect", "get", 2)
        snap["shares"] = [s.get("name") for s in (c("SYNO.Core.Share", "list", 1) or {}).get("shares", [])]
        snap["cm_containers"] = (c("SYNO.Docker.Container", "list", 1, limit=-1, offset=0, type="all") or {}).get("containers", [])
        snap["cm_images"] = (c("SYNO.Docker.Image", "list", 1, limit=-1, offset=0, show_dsm=False) or {}).get("images", [])
        snap["cm_projects"] = list((c("SYNO.Docker.Project", "list", 1) or {}).values())

    # ---- SSH side
    disks = [x["id"] for x in (snap.get("storage") or {}).get("disks", [])]
    snap["smart"] = _smart(cfg, pw, disks, errors)
    snap["mdstat"] = _try(lambda: ssh.run(cfg.ssh_alias, "cat /proc/mdstat").out, errors, "mdstat")
    snap["docker"] = _docker(cfg, pw, errors)
    return snap


def _packages(installed: dict, catalog: dict) -> list[dict]:
    latest = {p["package"]: p["version"] for p in catalog.get("packages", []) if not p.get("beta")}
    out = []
    for p in installed.get("packages", []):
        add = p.get("additional", {})
        avail = latest.get(p["id"])
        out.append({"id": p["id"], "name": p.get("name"), "version": p.get("version"),
                    "status": add.get("status"), "available": avail,
                    "update": bool(avail and _vtuple(avail) > _vtuple(p.get("version")))})
    return sorted(out, key=lambda x: x["name"] or x["id"])


def _smart(cfg, pw, disks: list[str], errors: list) -> dict:
    if not disks:
        return {}
    cmd = "; ".join(f"echo '##{dk}'; smartctl -H -A /dev/{dk}" for dk in disks)
    r = _try(lambda: ssh.run(cfg.ssh_alias, cmd, sudo_password=pw, timeout=120), errors, "smartctl")
    if not r:
        return {}
    res, cur = {}, None
    row = re.compile(r"^\s*(\d+)\s+\S+\s+0x[0-9a-fA-F]+\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+\S+\s+(\d+)")
    for line in r.out.splitlines():
        if line.startswith("##"):
            cur = line[2:].strip()
            res[cur] = {}
        elif cur and "overall-health" in line:
            res[cur]["health"] = line.rsplit(":", 1)[-1].strip()
        elif cur and (m := row.match(line)) and int(m.group(1)) in SMART_IDS:
            res[cur][SMART_IDS[int(m.group(1))]] = int(m.group(2))
    return res


def _docker(cfg, pw, errors: list) -> dict:
    D = cfg.docker_bin
    run = lambda cmd, t=180: ssh.run(cfg.ssh_alias, cmd, sudo_password=pw, timeout=t)  # noqa: E731
    out: dict[str, Any] = {}
    r = _try(lambda: run(f"{D} inspect $({D} ps -aq)"), errors, "docker inspect")
    out["inspect"] = json.loads(r.out) if r and r.ok else []
    r = _try(lambda: run(f"{D} stats --no-stream --format '{{{{json .}}}}'"), errors, "docker stats")
    out["stats"] = {s["Name"]: s for s in (json.loads(l) for l in (r.out.splitlines() if r and r.ok else []) if l.strip())}
    r = _try(lambda: run(f"{D} version --format '{{{{.Server.Version}}}}'"), errors, "docker version")
    out["version"] = r.out.strip() if r else None
    r = _try(lambda: run(f"{D} system df --format '{{{{json .}}}}'"), errors, "docker df")
    out["df"] = [json.loads(l) for l in (r.out.splitlines() if r and r.ok else []) if l.strip()]
    # Image labels are the source of truth for versions: watchtower copies the OLD
    # container's labels when it recreates a container, so Config.Labels go stale.
    r = _try(lambda: run(f"{D} image inspect --format '{{{{json .}}}}' $({D} images -q)"), errors, "image inspect")
    imgs = {}
    for line in (r.out.splitlines() if r and r.ok else []):
        if line.strip():
            i = json.loads(line)
            imgs[i["Id"]] = {"created": i.get("Created", "")[:10],
                             "version": ((i.get("Config") or {}).get("Labels") or {}).get("org.opencontainers.image.version")}
    out["images"] = imgs
    r = _try(lambda: run(f"{D} images -f dangling=true -q | wc -l"), errors, "dangling")
    out["dangling_images"] = int(r.out.strip() or 0) if r and r.ok else None
    return out


# --------------------------------------------------------------------------- analysis
def containers(snap: dict) -> list[dict]:
    upg = {f"{i['repository']}:{t}": i.get("upgradable") for i in snap.get("cm_images", []) for t in i.get("tags", [])}
    stats = snap["docker"].get("stats", {})
    rows = []
    for c in snap["docker"].get("inspect", []):
        name = c["Name"].lstrip("/")
        st, hc, cf = c["State"], c["HostConfig"], c["Config"]
        ports = sorted({f"{b[0].get('HostPort')}->{p}" for p, b in (hc.get("PortBindings") or {}).items() if b})
        started = st.get("StartedAt", "")[:19]
        rows.append({
            "name": name, "image": cf.get("Image"), "state": st.get("Status"),
            "health": (st.get("Health") or {}).get("Status", "none"), "exit_code": st.get("ExitCode"),
            "restart_policy": (hc.get("RestartPolicy") or {}).get("Name") or "no",
            "restart_count": c.get("RestartCount", 0), "started": started if not started.startswith("0001") else None,
            "network": hc.get("NetworkMode"), "ports": ports, "privileged": hc.get("Privileged"),
            "docker_sock": any("docker.sock" in b for b in (hc.get("Binds") or [])),
            "mounts": [m.get("Source") for m in c.get("Mounts", [])],
            "update_available": upg.get(cf.get("Image")),
            "version_label": snap["docker"].get("images", {}).get(c.get("Image"), {}).get("version"),
            "image_built": snap["docker"].get("images", {}).get(c.get("Image"), {}).get("created"),
            "cpu": stats.get(name, {}).get("CPUPerc"), "mem": stats.get(name, {}).get("MemUsage"),
        })
    return sorted(rows, key=lambda r: (r["state"] != "running", r["name"]))


def _parse_dt(s: str | None) -> datetime | None:
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(s or "", fmt)
        except ValueError:
            pass
    return None


def findings(snap: dict, rows: list[dict], prev_running: set[str] | None = None) -> list[dict]:
    """Evaluate the snapshot. Each finding has a stable `key` (no changing numbers)
    so the hourly check can tell new / escalated / resolved issues apart.
    `prev_running`: containers running at the previous check (detects crashes)."""
    f: list[dict] = []

    def add(sev, area, msg, key, value=None):
        f.append({"severity": sev, "area": area, "message": msg, "key": key, "value": value})

    now = datetime.now()
    if snap.get("fatal"):
        add("critical", "Connectivity", f"NAS check failed: {snap['fatal']}", "collect_failed")
        return f
    sysinfo, status = snap.get("system") or {}, snap.get("system_status") or {}
    if status.get("is_system_crashed"):
        add("critical", "System", "DSM reports the system partition as crashed", "sys_crashed")
    if sysinfo.get("temperature_warning") or sysinfo.get("sys_tempwarn"):
        add("warning", "System", f"System temperature warning ({sysinfo.get('sys_temp')} C)", "sys_temp")

    st = snap.get("storage") or {}
    for p in st.get("storagePools", []):
        if p.get("status") != "normal":
            add("critical", "Storage", f"Storage pool {p['id']} status: {p.get('status')}", f"pool:{p['id']}:{p.get('status')}")
    for v in st.get("volumes", []):
        u = _pct(v["size"]["used"], v["size"]["total"])
        if v.get("status") != "normal":
            add("critical", "Storage", f"{v['vol_path']} status: {v.get('status')}", f"vol_status:{v['vol_path']}")
        if u >= 90:
            add("critical", "Storage", f"{v['vol_path']} is {u}% full", f"vol_full:{v['vol_path']}", u)
        elif u >= 80:
            add("warning", "Storage", f"{v['vol_path']} is {u}% full", f"vol_full:{v['vol_path']}", u)
    sched = (st.get("env") or {}).get("data_scrubbing", {})
    last_scrub = max((p.get("last_done_time") or 0 for p in st.get("storagePools", [])), default=0)
    if sched.get("sche_status") == "paused":
        add("warning", "Storage", "Scheduled data scrubbing is PAUSED", "scrub_paused")
    if last_scrub and now - datetime.fromtimestamp(last_scrub) > timedelta(days=180):
        add("warning", "Storage", f"Last data scrub completed {datetime.fromtimestamp(last_scrub):%Y-%m-%d} (>180 days ago)", "scrub_stale")
    if "_" in (snap.get("mdstat") or "") or "recovery" in (snap.get("mdstat") or ""):
        add("critical", "Storage", "An md RAID array is degraded or rebuilding (see /proc/mdstat)", "md_degraded")
    for dk in st.get("disks", []):
        sm = (snap.get("smart") or {}).get(dk["id"], {})
        label = f"{dk.get('name')} ({dk['id']}, {dk.get('model')})"
        if dk.get("status") != "normal" or dk.get("smart_status") not in ("normal", None):
            add("critical", "Disks", f"{label}: status={dk.get('status')} smart={dk.get('smart_status')}", f"disk_status:{dk['id']}")
        if sm.get("health") and sm["health"] != "PASSED":
            add("critical", "Disks", f"{label}: SMART self-assessment {sm['health']}", f"smart_health:{dk['id']}")
        for k in ("reallocated", "pending", "offline_uncorrect", "reported_uncorrect"):
            if sm.get(k):
                add("warning", "Disks", f"{label}: SMART {k} = {sm[k]}", f"smart:{dk['id']}:{k}", sm[k])
        if (dk.get("temp") or 0) >= 50:
            add("warning", "Disks", f"{label}: temperature {dk['temp']} C", f"disk_temp:{dk['id']}")
    for dev in (snap.get("usb") or {}).get("devices", []):
        for part in dev.get("partitions", []):
            u = _pct(part["used_size_mb"], part["total_size_mb"])
            if u >= 90:
                add("warning", "USB", f"{dev.get('product')} ({part.get('share_name')}) is {u}% full", f"usb_full:{part.get('share_name')}", u)

    for b in snap.get("backups", []):
        last_ok = _parse_dt(b.get("last_success"))
        if b.get("last_result") not in ("done", None):
            since = f" since {last_ok:%Y-%m-%d}" if last_ok else ""
            add("critical", "Backup", f"Hyper Backup '{b['name']}' last run {b.get('last_result')}: "
                                      f"{b.get('last_error') or 'no detail'} (no successful run{since})", f"backup_failed:{b['name']}")
        elif last_ok and now - last_ok > timedelta(days=8):
            add("warning", "Backup", f"Hyper Backup '{b['name']}' last success {last_ok:%Y-%m-%d}", f"backup_stale:{b['name']}")

    upd = (snap.get("dsm_update") or {}).get("update", {})
    if upd.get("available"):
        ver = upd.get("version") or upd.get("version_details") or ""
        add("warning", "Updates", f"DSM update available: {ver or upd}", f"dsm_update:{ver}")
    for p in snap.get("packages", []):
        if p["update"]:
            add("warning", "Updates", f"Package update: {p['name']} {p['version']} -> {p['available']}", f"pkg_update:{p['id']}:{p['available']}")
    sa = snap.get("security_advisor") or {}
    if sa.get("sysStatus") not in ("safe", None):
        bad = [k for k, v in (sa.get("items") or {}).items() if v.get("failSeverity") != "safe"]
        sev = "warning" if any((v.get("fail") or {}).get(x) for v in (sa.get("items") or {}).values() for x in ("danger", "risk")) else "info"
        add(sev, "Security", f"Security Advisor status '{sa.get('sysStatus')}' (categories: {', '.join(bad)})", f"secadv:{','.join(sorted(bad))}")
    if (snap.get("firewall") or {}).get("enable_firewall") is False:
        add("info", "Security", "DSM firewall is disabled", "firewall_off")

    for r in rows:
        n = r["name"]
        if r["state"] == "running" and r["health"] == "unhealthy":
            add("warning", "Containers", f"{n} is running but UNHEALTHY", f"ctr_unhealthy:{n}")
        if r["state"] == "restarting" or r["restart_count"] > 5:
            add("warning", "Containers", f"{n} is restart-looping (restarts={r['restart_count']})", f"ctr_restarting:{n}")
        if r["state"] == "exited" and r["exit_code"] not in (0, None):
            add("warning", "Containers", f"{n} exited with code {r['exit_code']}", f"ctr_exit:{n}")
        elif prev_running and n in prev_running and r["state"] != "running":
            add("warning", "Containers", f"{n} was running at the last check and is now '{r['state']}'", f"ctr_down:{n}")
        if r["state"] == "running" and r["restart_policy"] == "no":
            add("info", "Containers", f"{n} has no restart policy (may not come back after reboot/crash)", f"ctr_norestart:{n}")
        if r["docker_sock"] and r["state"] == "running":
            add("info", "Containers", f"{n} mounts the Docker socket (root-equivalent access)", f"ctr_sock:{n}")
        if r["privileged"]:
            add("info", "Containers", f"{n} runs privileged", f"ctr_priv:{n}")
    never = [r["name"] for r in rows if r["state"] == "created"]
    if never:
        add("info", "Containers", "Created but never started: " + ", ".join(never), "ctr_never_started")
    ups = [r["name"] for r in rows if r["update_available"]]
    if ups:
        add("info", "Containers", f"Image updates available for {len(ups)}: " + ", ".join(ups), "img_updates")
    stopped_proj = [p["name"] for p in snap.get("cm_projects", []) if p.get("status") != "RUNNING"]
    if stopped_proj:
        add("info", "Containers", "Container Manager projects not running: " + ", ".join(stopped_proj), "proj_stopped")
    return sorted(f, key=lambda x: (SEV_ORDER[x["severity"]], x["area"]))


# --------------------------------------------------------------------------- report
def render(snap: dict, rows: list[dict], fnd: list) -> str:
    s, st = snap.get("system") or {}, snap.get("storage") or {}
    u = snap.get("utilization") or {}
    mem = u.get("memory", {})
    cpu = u.get("cpu", {})
    L = [f"# Synology report - {s.get('model')} `{snap['host']}`", "",
         f"Collected {snap['collected_at']}  |  {s.get('firmware_ver')}  |  uptime {s.get('up_time')} (h:m:s)  |  "
         f"sys temp {s.get('sys_temp')} C  |  CPU {cpu.get('user_load', 0) + cpu.get('system_load', 0) + cpu.get('other_load', 0)}%  |  "
         f"RAM {mem.get('real_usage')}% (swap {mem.get('swap_usage')}%)", ""]
    crit = sum(1 for x in fnd if x["severity"] == "critical"); warn = sum(1 for x in fnd if x["severity"] == "warning")
    L += [f"## Findings - {crit} critical, {warn} warning, {len(fnd) - crit - warn} info", ""]
    icon = {"critical": "🔴", "warning": "🟠", "info": "🔵"}
    L += [f"- {icon[x['severity']]} **{x['area']}** - {x['message']}" for x in fnd] or ["- ✅ No issues found"]

    L += ["", "## Storage", "", "| Pool / Volume | Type | Status | Used | Size |", "|---|---|---|---|---|"]
    for p in st.get("storagePools", []):
        L.append(f"| {p['id']} | {p.get('device_type')} | {p.get('status')} | | {_gb(p['size']['total'])/1000:.1f} TB |")
    for v in st.get("volumes", []):
        L.append(f"| {v['vol_path']} | {v.get('fs_type')} | {v.get('status')} | {_pct(v['size']['used'], v['size']['total'])}% | "
                 f"{_gb(v['size']['total'])/1000:.1f} TB |")
    for dev in (snap.get("usb") or {}).get("devices", []):
        for part in dev.get("partitions", []):
            L.append(f"| USB {part.get('share_name')} ({dev.get('product')}) | {part.get('filesystem')} | {part.get('status')} | "
                     f"{_pct(part['used_size_mb'], part['total_size_mb'])}% | {part['total_size_mb']/1e6:.1f} TB |")
    L += ["", "| Drive | Model | Temp | Status | Power-on (y) | Realloc | Pending | Uncorr |", "|---|---|---|---|---|---|---|---|"]
    for dk in sorted(st.get("disks", []), key=lambda x: x.get("name", "")):
        sm = (snap.get("smart") or {}).get(dk["id"], {})
        poh = sm.get("power_on_hours")
        L.append(f"| {dk.get('name')} ({dk['id']}) | {dk.get('model')} | {dk.get('temp')} C | {dk.get('status')}/{sm.get('health', '?')} | "
                 f"{round(poh / 8766, 1) if poh else '?'} | {sm.get('reallocated', '?')} | {sm.get('pending', '?')} | {sm.get('offline_uncorrect', '?')} |")

    L += ["", "## Backups (Hyper Backup)", "", "| Task | Type | Last result | Last run | Last success | Next run |", "|---|---|---|---|---|---|"]
    for b in snap.get("backups", []):
        L.append(f"| {b['name']} | {b['type']} | {b['last_result']} | {b['last_run']} | {b['last_success']} | {b['next_run']} |")

    upd = (snap.get("dsm_update") or {}).get("update", {})
    ds = snap.get("dsm_update_settings") or {}
    ps = snap.get("pkg_update_settings") or {}
    L += ["", "## Updates", "",
          f"- DSM: {'**update available**' if upd.get('available') else 'up to date'}  (auto-install: {ds.get('upgrade_type', '?')}, auto-download: {ds.get('auto_download')})",
          f"- Packages auto-update: {'all' if ps.get('autoupdateall') else 'important only' if ps.get('autoupdateimportant') else 'off'}",
          "", "| Package | Installed | Available | Status |", "|---|---|---|---|"]
    for p in snap.get("packages", []):
        L.append(f"| {p['name']} | {p['version']} | {('**' + p['available'] + '**') if p['update'] else (p['available'] or '-')} | {p['status']} |")

    dk = snap["docker"]
    running = sum(r["state"] == "running" for r in rows)
    L += ["", f"## Container Manager - {running}/{len(rows)} running  (Docker {dk.get('version')})", "",
          "| Container | State | Health | Restart | Image | Version | Built | Update | CPU | Mem | Ports / Net |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        net = ", ".join(r["ports"]) or r["network"]
        L.append(f"| {r['name']} | {r['state']} | {r['health']} | {r['restart_policy']} | {r['image']} | {r['version_label'] or ''} | {r['image_built'] or ''} | "
                 f"{'⬆' if r['update_available'] else ''} | {r['cpu'] or ''} | {(r['mem'] or '').split(' /')[0]} | {net} |")
    if snap.get("cm_projects"):
        L += ["", "Projects: " + ", ".join(f"{p['name']} ({p.get('status')}, {p.get('path')})" for p in snap["cm_projects"])]
    if dk.get("df"):
        L += ["", "Disk usage: " + "; ".join(f"{x['Type']} {x['Size']} ({x['Reclaimable']} reclaimable)" for x in dk["df"])]
    if snap["errors"]:
        L += ["", "## Collection errors", ""] + [f"- {e}" for e in snap["errors"]]
    return "\n".join(L) + "\n"


def out_dir() -> Path:
    d = config.data_dir() / "synology"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(prev_running: set[str] | None = None) -> tuple[dict, list[dict], list[dict], str]:
    """Collect + analyse + persist. Never raises for NAS-side failures: a failed
    collection becomes a critical 'collect_failed' finding instead."""
    try:
        snap = collect()
    except Exception as e:  # noqa: BLE001
        snap = {"collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "host": "?", "errors": [], "fatal": f"{type(e).__name__}: {e}", "docker": {}}
    rows = containers(snap) if not snap.get("fatal") else []
    fnd = findings(snap, rows, prev_running)
    snap["containers"], snap["findings"] = rows, fnd
    clean = redact(snap)
    d = out_dir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (d / f"snapshot-{stamp}.json").write_text(json.dumps(clean, indent=1, default=str), encoding="utf-8")
    report = render(clean, rows, fnd) if not snap.get("fatal") else f"# Synology report\n\nCollection FAILED: {snap['fatal']}\n"
    (d / f"report-{stamp}.md").write_text(report, encoding="utf-8")
    (d / "latest.md").write_text(report, encoding="utf-8")
    return clean, rows, fnd, report


def main(json_only: bool = False, out: str | None = None) -> None:
    t0 = time.time()
    clean, _rows, _fnd, report = run()
    if out:
        Path(out).write_text(report, encoding="utf-8")
    print(json.dumps(clean, indent=1, default=str) if json_only else report)
    print(f"(done in {time.time() - t0:.0f}s; saved under {out_dir()})")
