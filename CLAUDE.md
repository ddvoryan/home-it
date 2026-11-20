# home-it: notes for Claude

## Hard rules
- **This repository is PUBLIC.** Never commit hostnames, IPs, usernames, emails, serial numbers,
  cert fingerprints, snapshots/reports, or anything from `~/.home-it/`. Use placeholders in docs.
  Grep the staged diff for these before every commit.
- Secrets only come from `homeit.secrets` (OS keyring). Never put them on a command line, in a URL,
  in env vars, or in files.
- Site config: `~/.home-it/config.toml`. Data: `~/.home-it/data/`. Not `%APPDATA%` (MSIX redirection, see docs/synology.md).

## Running
- Python venv at `.venv`: `.\.venv\Scripts\python.exe -m homeit <group> <cmd>`.
- Set `PYTHONIOENCODING=utf-8` when printing reports to a Windows console.
- NAS shell: `ssh nas '<cmd>'` (key auth, BatchMode). For root: `homeit.synology.ssh.run(..., sudo_password=...)`.

## Action policy on the NAS (agreed with the owner)
- Monitoring and inventory: always OK.
- **Routine actions OK without asking, report afterwards**: restart an unhealthy or crashed container,
  pull and recreate a container on an updated image (`update-images`, which includes pruning
  *dangling* images left behind by previous updates).
- **Ask first**: DSM or package updates, changing DSM settings, storage, shares, users, Hyper Backup
  task edits, deleting containers, tagged images, volumes or data, and anything touching Plex (a separate project).
- Scheduled runs: the hourly `check` and the Claude relay/digest tasks are **read-only**. Only two weekly
  jobs change anything: `update-images`, and `usb-sync`, which may rewrite the USB backup task's folder
  list from the owner's rules in site config (approved by the owner 2026-11-19). Changing those rules,
  or any other Hyper Backup edit, is still ask-first.

## Recurring jobs
- Task Scheduler `\home-it\NAS hourly check` (`check`), `\home-it\NAS USB backup folder sync` (Sun 02:30)
  and `\home-it\NAS weekly image update` (Sun 04:00).
- Claude scheduled tasks `nas-alert-relay` (every 2h, 08:15-22:15) and `nas-morning-digest` (07:30) deliver
  alerts by push notification and email to the owner only.
- Interactive checks: the `synology-health` skill in `.claude/skills/`.
