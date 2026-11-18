# Synology setup runbook

One-time setup to let the `homeit.synology` tooling (and Claude) reach a DSM 7.x NAS.

## 1. DSM side (web UI)

1. **Control Panel → User & Group → Create** a dedicated service account (e.g. `svc-account`).
   - Member of **administrators** (DSM only allows SSH for admins; most health APIs need it too).
   - Shared folders: *No access* is fine, because root-level reads go through `sudo`.
   - **No 2FA** on this account (unattended API logins can't answer OTP). If 2FA is enforced
     for administrators, exempt the account. Compensate with the LAN-only key and DSM auto-block.
2. **User & Group → Advanced → Enable user home service** (needed for `~/.ssh`).
3. **Control Panel → Terminal & SNMP → Enable SSH**.

## 2. Workstation side

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519_nas -N '""' -C "svc@$env:COMPUTERNAME"
```

`~/.ssh/config`:

```
Host nas
    HostName <nas-hostname>
    User <svc-account>
    IdentityFile ~/.ssh/id_ed25519_nas
    IdentitiesOnly yes
    StrictHostKeyChecking yes
```

Create `~/.home-it/config.toml` from `config.example.toml`, then:

```powershell
.\.venv\Scripts\python.exe -m homeit synology pin-cert       # prints the fingerprint to pin
.\.venv\Scripts\python.exe -m homeit synology set-password   # stores password in Credential Manager
```

Install the key (asks for the password once):

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519_nas.pub | ssh -o PubkeyAuthentication=no <svc-account>@<nas-hostname> "mkdir -p ~/.ssh; chmod 755 ~; chmod 700 ~/.ssh; tr -d '\r' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys"
```

Then restrict the key to the LAN by prefixing its line in `authorized_keys` with
`from="<lan-cidr>",no-agent-forwarding,no-X11-forwarding,no-port-forwarding`, and verify with
`python -m homeit synology probe`.

## Gotchas learned the hard way

- **`chmod 755 ~` is required.** DSM home folders default to looser permissions and sshd's StrictModes
  then silently ignores `authorized_keys`.
- **Don't write config under `%APPDATA%` from the Claude desktop app.** It is an MSIX-packaged app,
  and Windows redirects new files it creates under AppData into a private per-app copy, invisible to
  your own shell and Task Scheduler. That's why config lives in `~/.home-it/`.
- **Piping scripts to the NAS from Windows**: send bytes, not text. Text-mode stdin turns LF into CRLF
  and `sh` chokes (`$'\r': command not found`). Avoid nested quoting through PowerShell → ssh → sh. Pipe a script to `sh -s` instead.
- **When editing `authorized_keys` remotely, arm a dead-man switch**: a background
  `sleep 90; restore backup unless marker removed`, then confirm a *fresh* login before disarming it.
- **`synopkg` is in `/usr/syno/bin`**, which `sudo`'s `secure_path` doesn't include. Use full paths.
- **Seagate Exos drives report non-standard SMART attribute names** (`Retired_Sectors_Count`,
  `Pending-Sparing_Count`, ...). Parse by attribute ID (5, 9, 194, 197, 198, 199), not by name.
- **Watchtower copies the old container's labels** when it recreates a container, so
  `Config.Labels["org.opencontainers.image.version"]` goes stale. Read versions from the image.
- **The DSM cert is self-signed and expires.** When DSM renews it, `pin-cert` will report a mismatch.
  Verify the change was expected, then update `cert_sha256`.
- The Hyper Backup task API returns cloud-target **refresh tokens**. The inventory deliberately
  doesn't call `SYNO.Backup.Task get`, and redacts token-like keys anyway.

## Recurring jobs

Register the Task Scheduler jobs (run as your user, *only when logged on*, because Credential Manager
secrets are only readable inside your session):

```powershell
$repo = '<path-to-home-it>'; $pyw = "$repo\.venv\Scripts\pythonw.exe"
$prin = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
$set  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskPath '\home-it\' -TaskName 'NAS hourly check' -Principal $prin -Settings $set `
  -Action (New-ScheduledTaskAction -Execute $pyw -Argument '-m homeit synology check' -WorkingDirectory $repo) `
  -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650))
Register-ScheduledTask -TaskPath '\home-it\' -TaskName 'NAS weekly image update' -Principal $prin -Settings $set `
  -Action (New-ScheduledTaskAction -Execute $pyw -Argument '-m homeit synology update-images' -WorkingDirectory $repo) `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 4:00)
```

`pythonw` has no console, so output goes to `~/.home-it/logs/homeit.log`, and `ssh` is started with
`CREATE_NO_WINDOW` so no window flashes up every hour.

## Useful DSM Web API calls (DSM 7.4)

| Purpose | API · method · version |
|---|---|
| Model, DSM version, temp, uptime | `SYNO.Core.System` · `info` · 1 |
| CPU / RAM / net / disk I/O | `SYNO.Core.System.Utilization` · `get` · 1 |
| Pools, volumes, disks, scrub schedule | `SYNO.Storage.CGI.Storage` · `load_info` · 1 |
| DSM update available | `SYNO.Core.Upgrade.Server` · `check` · 2 |
| Installed packages | `SYNO.Core.Package` · `list` · 2 (`additional=["status"]`) |
| Package catalog (latest versions) | `SYNO.Core.Package.Server` · `list` · 2 |
| Hyper Backup tasks / status | `SYNO.Backup.Task` · `list` / `status` · 1 |
| Security Advisor summary | `SYNO.Core.SecurityScan.Status` · `system_get` · 1 |
| Containers / images (`upgradable`) / projects | `SYNO.Docker.Container` / `.Image` / `.Project` · `list` · 1 |
