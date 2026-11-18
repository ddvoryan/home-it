"""Home Assistant inventory: integrations, their health, devices, entities and what needs re-auth.

Read-only. Writes a JSON snapshot and a markdown summary to ~/.home-it/data/homeassistant/.
Those files contain site details (IPs, serials, account names) and must never go in git.
"""
from __future__ import annotations

import collections
import json
from datetime import datetime, timezone
from pathlib import Path

from homeit import config
from homeit.homeassistant.client import HA

BAD_STATES = {"setup_error", "setup_retry", "migration_error", "failed_unload", "not_loaded"}


def collect() -> dict:
    with HA() as ha:
        snap = {
            "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ha_version": ha.version,
            "config": ha.ws("get_config"),
            "user": ha.ws("auth/current_user"),
            "entries": ha.ws("config_entries/get"),
            "flows": ha.ws("config_entries/flow/progress"),
            "devices": ha.ws("config/device_registry/list"),
            "entities": ha.ws("config/entity_registry/list"),
            "areas": ha.ws("config/area_registry/list"),
            "states": ha.ws("get_states"),
            "issues": ha.ws("repairs/list_issues").get("issues", []),
            "dashboards": ha.ws("lovelace/dashboards/list"),
        }
    return snap


def summarize(s: dict) -> str:
    entries = {e["entry_id"]: e for e in s["entries"]}
    area = {a["area_id"]: a["name"] for a in s["areas"]}
    state_of = {st["entity_id"]: st["state"] for st in s["states"]}

    devs_by = collections.defaultdict(list)
    for d in s["devices"]:
        devs_by[d.get("primary_config_entry") or (d.get("config_entries") or [None])[0]].append(d)

    ent_tot, ent_on, ent_unavail = collections.Counter(), collections.Counter(), collections.Counter()
    for e in s["entities"]:
        k = e.get("config_entry_id")
        ent_tot[k] += 1
        if not e.get("disabled_by"):
            ent_on[k] += 1
            if state_of.get(e["entity_id"]) == "unavailable":
                ent_unavail[k] += 1

    reauth = [f for f in s["flows"] if (f.get("context") or {}).get("source") in ("reauth", "reconfigure")]
    discovered = [f for f in s["flows"] if (f.get("context") or {}).get("source") not in ("reauth", "reconfigure")]
    issues = [i for i in s["issues"] if not i.get("dismissed_version") and not i.get("ignored")]
    bad = [e for e in s["entries"] if e.get("state") in BAD_STATES and not e.get("disabled_by")]

    cfg = s["config"]
    L = [f"# Home Assistant inventory - {cfg.get('location_name')}",
         f"_Collected {s['collected_at']} - HA {s['ha_version']} - as user `{s['user'].get('name')}`"
         f" (admin={s['user'].get('is_admin')})_", "",
         f"**{len(s['entries'])} integrations, {len(s['devices'])} devices, {len(s['entities'])} entities "
         f"({sum(ent_on.values())} enabled, {sum(ent_unavail.values())} unavailable), "
         f"{len(s['dashboards'])} extra dashboards.**", "",
         "## Needs attention", ""]
    if not (reauth or bad or issues or discovered):
        L.append("Nothing. 🎉")
    for f in reauth:
        e = entries.get((f.get("context") or {}).get("entry_id"), {})
        L.append(f"- 🔑 **Re-authenticate** `{f['handler']}` - {e.get('title', '?')} "
                 f"(Settings → Devices & services → {f['handler']} → Reconfigure/Re-authenticate)")
    for e in bad:
        L.append(f"- ⚠️ `{e['domain']}` - {e['title']}: **{e['state']}** {('- ' + e['reason']) if e.get('reason') else ''}")
    for i in issues:
        L.append(f"- 🛠 Repair `{i['domain']}`: {i.get('translation_key') or i['issue_id']} (severity {i.get('severity')})")
    for f in discovered:
        L.append(f"- ➕ Discovered, not set up: `{f['handler']}` ({(f.get('context') or {}).get('source')})")

    L += ["", "## Integrations", "",
          "| Integration | Title | State | Devices | Entities on/total | Unavailable | Source |",
          "|---|---|---|---|---|---|---|"]
    for e in sorted(s["entries"], key=lambda e: (e["domain"], e["title"])):
        k = e["entry_id"]
        st = "disabled" if e.get("disabled_by") else e.get("state")
        flag = "" if st in ("loaded", "disabled") else " ⚠️"
        L.append(f"| {e['domain']} | {e['title'][:40]} | {st}{flag} | {len(devs_by.get(k, []))} | "
                 f"{ent_on[k]}/{ent_tot[k]} | {ent_unavail[k] or ''} | {e.get('source')} |")

    L += ["", "## Devices by integration", ""]
    for e in sorted(s["entries"], key=lambda e: e["domain"]):
        ds = devs_by.get(e["entry_id"], [])
        if not ds:
            continue
        L.append(f"### {e['domain']} - {e['title'][:50]} ({len(ds)})")
        for d in sorted(ds, key=lambda d: (d.get("name_by_user") or d.get("name") or "")):
            L.append(f"- {d.get('name_by_user') or d.get('name')} - {d.get('manufacturer') or ''} "
                     f"{d.get('model') or ''} - area: {area.get(d.get('area_id'), '-')}"
                     f"{' - DISABLED' if d.get('disabled_by') else ''}")
        L.append("")

    L += ["## Dashboards", ""] + [f"- {d.get('title')} (`{d.get('url_path')}`, mode {d.get('mode')})"
                                    for d in s["dashboards"]]
    return "\n".join(L) + "\n"


def main(json_only: bool = False, out: str | None = None) -> None:
    snap = collect()
    d = config.data_dir() / "homeassistant"
    d.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (d / f"snapshot-{stamp}.json").write_text(json.dumps(snap, indent=1), encoding="utf-8")
    if json_only:
        print(json.dumps(snap, indent=1))
        return
    md = summarize(snap)
    (d / "latest.md").write_text(md, encoding="utf-8")
    if out:
        Path(out).write_text(md, encoding="utf-8")
    print(md)
