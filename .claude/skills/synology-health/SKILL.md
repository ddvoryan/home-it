---
name: synology-health
description: Check the Synology NAS health on demand - storage, disks/SMART, Hyper Backup, DSM/package updates, Container Manager - and explain findings. Use when the user asks how the NAS is doing, about a NAS alert, container status, backups, or wants a fix for a NAS finding.
---

# Synology health check

Tooling: this repo (`homeit.synology`). Run everything from the repo root in PowerShell with
`$env:PYTHONIOENCODING='utf-8'` and `.\.venv\Scripts\python.exe -m homeit synology <cmd>`.

## Steps
1. `probe`: confirms SSH, sudo and DSM API. If it fails, diagnose first:
   - `[ssh] FAIL`: is the key still in `authorized_keys`, does `from=` match the client's subnet, `chmod 755 ~`?
   - `[api] FAIL ... code 400/403/407`: wrong password / 2FA got enabled / client IP auto-blocked.
   - cert mismatch: run `pin-cert`, and ask the user before re-pinning.
2. `inventory`: fresh report (about 40s). The newest copy is always `~/.home-it/data/synology/latest.md`.
3. `alerts --history 48`: what changed recently (hourly check + weekly updates).
4. Summarise for the user: critical and warning items first, each with a concrete fix. Mention info items only if asked or relevant.

## Deeper digging (read-only)
- Container logs: `homeit.synology.ssh.run(alias, f"{docker_bin} logs --tail 100 <name>", sudo_password=...)`.
  Write a small script file and run it with `python -I`. Don't inline nested quotes through PowerShell.
- Raw snapshot JSON (redacted): `~/.home-it/data/synology/snapshot-*.json`.
- Weekly update results: `~/.home-it/data/synology/updates/update-*.json`.

## Acting on findings
Follow the action policy in the repo's `CLAUDE.md`:
- OK without asking (report afterwards): restarting a crashed/unhealthy container, and image updates via
  `update-images` (it tags `homeit-prev`, verifies health, and rolls back automatically). `--only <name>` targets one container.
- Ask first: DSM/package updates, Hyper Backup task edits, scrub schedule, shares/users/settings, deleting anything, Plex.

## Recurring jobs (already set up; don't recreate)
- Task Scheduler `\home-it\NAS hourly check` → `check`, and `\home-it\NAS weekly image update` (Sun 04:00) → `update-images`.
- Claude scheduled tasks `nas-alert-relay` (every 2h, 08:15-22:15) and `nas-morning-digest` (07:30).
- Logs: `~/.home-it/logs/homeit.log`.
