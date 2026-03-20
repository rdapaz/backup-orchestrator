# Backup Orchestrator Help

Centralised backup management for go_backup agents over MQTT.

---

## Dashboard

The Dashboard gives you an at-a-glance overview of your backup infrastructure.

- **Clients Online** -- how many registered agents are currently sending heartbeats
- **Total Schedules** -- number of configured backup schedules across all clients
- **Recent Backups** -- last 24 hours of backup activity
- **Client List** -- quick status of each registered client with last-seen timestamp

Clients are considered **online** if a heartbeat has been received within the last 60 seconds. The agent sends heartbeats every 30 seconds.

---

## Clients

The Clients view shows all registered backup agents with their connection status, IP address, OS, and last-seen time.

### Registering a New Client

**On the client machine:**

1. Build the CLI (if not already built):
```
cd D:\Work\Projects\go_backup
go build -o backup-cli.exe ./cmd/cli/
```

2. Register against the orchestrator's MQTT broker:
```
backup-cli.exe register --broker <BROKER_IP> --port 1883
```

3. The orchestrator will show an approval dialog. Click **Yes** to approve.

4. Start the agent in long-running mode:
```
backup-cli.exe agent start --config-db agent.db
```

**On the orchestrator:**

- The registration request appears as a pop-up dialog
- Review the hostname, UUID, IP, and OS details
- Click **Yes** to approve or **No** to deny
- Approved clients appear in the Clients list immediately

### Client Status

| Status | Meaning |
|--------|---------|
| Online | Heartbeat received within last 60 seconds |
| Offline | No recent heartbeat |
| Backing Up | Backup currently in progress |

### Re-registration

If a client's IP changes or you need to update its details, simply run `register` again from the client. The orchestrator will show the approval dialog and update the existing record.

---

## Schedules

Schedules define what gets backed up, when, and where. Each schedule is tied to a specific client.

### Creating a Schedule

1. Click **Add Schedule**
2. Select the target client
3. Choose a backup profile (see below)
4. Enter the source directory (on the client machine)
5. Enter the destination directory (where archives are saved)
6. Select a frequency preset or enter a custom cron expression
7. Optionally set an archive password (auto-generated if left empty)

### Editing a Schedule

Click the **Edit** button on any schedule row to modify its settings.

### Backup Profiles

| Profile | What it backs up |
|---------|------------------|
| all | Everything in the source directory |
| documents | Document files (.doc, .pdf, .xlsx, etc.) |
| jetbrains | JetBrains IDE settings and projects |
| databases | Database files and dumps |
| photos | Image files (.jpg, .png, .raw, etc.) |

### Sync vs Trigger

- **Sync** -- pushes the schedule configuration to the client agent. The agent updates Windows Task Scheduler to match. Always sync after creating or editing a schedule.
- **Trigger** -- runs the backup immediately (on-demand), regardless of the schedule.

### Cron Expression Format

Cron expressions use 5 fields: `minute hour day-of-month month day-of-week`

| Expression | Meaning |
|-----------|---------|
| `0 2 * * *` | Daily at 2:00 AM |
| `30 6 * * *` | Daily at 6:30 AM |
| `0 */12 * * *` | Every 12 hours |
| `0 3 * * 0` | Weekly on Sunday at 3:00 AM |
| `0 2 * * 1-5` | Weekdays at 2:00 AM |
| `0 2 1,15 * *` | 1st and 15th of each month at 2:00 AM |
| `0 2 1 * *` | Monthly on the 1st at 2:00 AM |
| `*/30 * * * *` | Every 30 minutes |

**Field values:**

| Field | Allowed Values |
|-------|---------------|
| Minute | 0-59 |
| Hour | 0-23 |
| Day of Month | 1-31 |
| Month | 1-12 |
| Day of Week | 0-7 (0 and 7 = Sunday) |

**Special characters:**

- `*` -- any value
- `*/N` -- every N units
- `1,15` -- specific values
- `1-5` -- range

---

## History

The History view shows all backup results reported by clients, whether triggered manually, by schedule, or by the orchestrator.

### Columns

| Column | Description |
|--------|-------------|
| Started | When the backup began (UTC) |
| Completed | When the backup finished (UTC) |
| Client | Which client ran the backup |
| Profile | Backup profile used |
| Status | success or failure |
| Method | How the backup was initiated |
| Files | Number of files in the archive |
| Error | Error message (if failed) |

### Backup Methods

| Method | Meaning |
|--------|---------|
| orchestrator | Triggered via the Trigger button in the UI |
| scheduled | Fired by Windows Task Scheduler |
| manual | Run directly via CLI or GUI on the client |

### Export

Click **Export CSV** to save the filtered history to a CSV file.

---

## Settings

### MQTT Broker

Configure the connection to the Mosquitto MQTT broker.

- **Host** -- broker hostname or IP (usually `localhost` if running on the same machine)
- **Port** -- broker port (default: 1883)
- **Username / Password** -- leave blank for anonymous access (development mode)

**Save** -- saves settings without connecting
**Save & Connect** -- saves and immediately connects (or reconnects)
**Test Connection** -- tests connectivity without saving

The orchestrator auto-connects on startup if broker settings are saved.

### Master Password

The master password protects the encrypted credential store where backup archive passwords are kept. You set this on first launch and need it each time you start the orchestrator.

**Changing the master password:**

1. Enter your current password
2. Enter and confirm the new password
3. Click **Change Password**

### Default Backup Settings

- **Workers** -- number of concurrent file-processing workers (default: 4)
- **Blocklist** -- directory names to exclude from backups (one per line)

---

## Architecture

### Communication Flow

```
Client (go_backup agent)  <--MQTT-->  Mosquitto Broker  <--MQTT-->  Orchestrator (PySide6)
```

### MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `backup/registration/request` | Client -> Orchestrator | New client registration |
| `backup/registration/response/<uuid>` | Orchestrator -> Client | Approval/denial |
| `backup/heartbeat/<uuid>` | Client -> Orchestrator | Periodic status |
| `backup/command/<uuid>` | Orchestrator -> Client | On-demand backup trigger |
| `backup/schedules/<uuid>` | Orchestrator -> Client | Schedule sync (retained) |
| `backup/status/<uuid>` | Client -> Orchestrator | Backup result reports |

### Offline Resilience

If the client cannot reach the broker when a backup completes:

1. The status report is queued in the local SQLite database (`agent.db`)
2. On the next successful connection, queued reports are drained and sent
3. The orchestrator receives them and populates the History view

### Security Model

- Archive passwords are encrypted at rest using AES-256-GCM
- The encryption key is derived from the master password via Argon2id
- Passwords are only held in memory while the credential store is unlocked
- MQTT authentication can be added via Mosquitto's password file

---

## Troubleshooting

### Checking if the Agent is Running

On the client machine:
```
backup-cli.exe agent start --config-db agent.db
```

The agent logs to stdout. You should see:
```
[agent] connected to broker
[agent] connected, client_uuid=<uuid>
```

### Checking Windows Scheduled Tasks

List all GoBackup tasks:
```
schtasks /query /tn "GoBackup*" /fo LIST /v
```

Check a specific task:
```
schtasks /query /tn "GoBackup_1" /fo LIST /v
```

Key fields to check:
- **Last Run Time** -- when it last fired
- **Last Result** -- `0` means success, anything else is an error
- **Task To Run** -- verify the path is absolute
- **Scheduled Task State** -- should be `Enabled`

### Checking Mosquitto

Verify the service is running:
```
sc query mosquitto
```

Restart the service (requires admin):
```
Restart-Service mosquitto
```

Test pub/sub manually:
```
mosquitto_sub -h localhost -t "backup/#" -v
mosquitto_pub -h localhost -t "backup/test" -m "hello"
```

### Common Issues

**Client shows "offline" in the orchestrator:**
- Is the agent running? (`backup-cli.exe agent start`)
- Is the broker running? (`sc query mosquitto`)
- Is the orchestrator connected? (check status bar at bottom)

**Scheduled task fails with exit code 2:**
- Check that `--config-db` path is absolute in the task definition
- Re-register and re-sync to fix relative paths

**Schedule sync shows `enabled=false`:**
- Old retained message on the broker. Click Sync again to overwrite.

**Client not receiving commands:**
- The agent must be running in long-running mode (`agent start`)
- One-shot `agent run-schedule` only runs a single backup and exits

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` | Dashboard |
| `Ctrl+2` | Clients |
| `Ctrl+3` | Schedules |
| `Ctrl+4` | History |
| `Ctrl+5` | Settings |
