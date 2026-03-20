const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, TabStopType, TabStopPosition,
} = require("docx");

const NAVY = "1B365D";
const LIGHT_BG = "F0F4F8";
const BORDER_COLOR = "E2E8F0";
const WHITE = "FFFFFF";

const border = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, font: "Segoe UI", size: 36, color: NAVY })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, font: "Segoe UI", size: 28, color: NAVY })],
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, font: "Segoe UI", size: 24, color: NAVY })],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text, font: "Segoe UI", size: 22, ...opts })],
  });
}

function bold(text) {
  return new TextRun({ text, font: "Segoe UI", size: 22, bold: true });
}

function normal(text) {
  return new TextRun({ text, font: "Segoe UI", size: 22 });
}

function codePara(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    children: [new TextRun({ text, font: "Cascadia Code", size: 20 })],
    shading: { fill: LIGHT_BG, type: ShadingType.CLEAR },
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60 },
    children: [new TextRun({ text, font: "Segoe UI", size: 22 })],
  });
}

function bulletMixed(children, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60 },
    children,
  });
}

function numberItem(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "numbers", level },
    spacing: { after: 60 },
    children: [new TextRun({ text, font: "Segoe UI", size: 22 })],
  });
}

function numberMixed(children, level = 0) {
  return new Paragraph({
    numbering: { reference: "numbers", level },
    spacing: { after: 60 },
    children,
  });
}

function makeTable(headers, rows, colWidths) {
  const tableWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headers.map((h, i) =>
      new TableCell({
        borders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: cellMargins,
        children: [new Paragraph({ children: [new TextRun({ text: h, font: "Segoe UI", size: 20, bold: true, color: WHITE })] })],
      })
    ),
  });
  const dataRows = rows.map(
    (row) =>
      new TableRow({
        children: row.map((cell, i) =>
          new TableCell({
            borders,
            width: { size: colWidths[i], type: WidthType.DXA },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, font: "Segoe UI", size: 20 })] })],
          })
        ),
      })
  );
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ],
      },
      {
        reference: "numbers",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        ],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: "Segoe UI", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 36, bold: true, font: "Segoe UI", color: NAVY }, paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: "Segoe UI", color: NAVY }, paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: "Segoe UI", color: NAVY }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY, space: 1 } },
              children: [
                new TextRun({ text: "go_backup Client Setup Guide", font: "Segoe UI", size: 18, color: NAVY, bold: true }),
                new TextRun({ children: ["\t"] }),
                new TextRun({ text: "Backup Orchestrator", font: "Segoe UI", size: 18, color: "6B7280" }),
              ],
              tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Page ", font: "Segoe UI", size: 18, color: "6B7280" }),
                new TextRun({ children: [PageNumber.CURRENT], font: "Segoe UI", size: 18, color: "6B7280" }),
              ],
            }),
          ],
        }),
      },
      children: [
        // ===== TITLE PAGE =====
        new Paragraph({ spacing: { before: 3000 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "go_backup", font: "Segoe UI", size: 56, bold: true, color: NAVY })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
          children: [new TextRun({ text: "Client Setup Guide", font: "Segoe UI", size: 40, color: "6B7280" })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [new TextRun({ text: "Cross-Platform Installation, Registration & Scheduling", font: "Segoe UI", size: 24, color: "6B7280" })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [new TextRun({ text: "Version 0.7.0  |  March 2026", font: "Segoe UI", size: 22, color: "9CA3AF" })],
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== OVERVIEW =====
        heading1("1. Overview"),
        para("This guide covers how to set up go_backup clients on Windows, Linux, and macOS machines so they can be managed by the Backup Orchestrator. The process involves:"),
        numberItem("Installing the go_backup binary"),
        numberItem("Registering the client with the orchestrator via MQTT"),
        numberItem("Starting the agent (long-running listener)"),
        numberItem("Configuring the agent to start automatically on boot"),
        numberItem("Verifying scheduled tasks are created and running"),

        para(""),
        para("The orchestrator manages all backup schedules centrally. When you click Sync in the orchestrator, the schedule is pushed to the client, which creates platform-native scheduled tasks (Windows Task Scheduler, cron, or launchd)."),

        // ===== PREREQUISITES =====
        heading1("2. Prerequisites"),
        bullet("Mosquitto MQTT broker running and accessible from the client machine"),
        bullet("Backup Orchestrator running and connected to the broker"),
        bullet("Network connectivity between client and broker (default port 1883)"),
        bullet("DHCP reservation configured for the client (recommended for static IP)"),
        bullet("Administrative/sudo access on the client machine"),

        // ===== INSTALLATION =====
        heading1("3. Installation"),

        heading2("3.1 Windows"),
        numberItem("Download backup-cli-windows-amd64.exe from the GitHub Releases page"),
        numberMixed([bold("Place the binary"), normal(" in a permanent location, e.g.:")]),
        codePara("C:\\Tools\\backup-cli.exe"),
        numberMixed([bold("Add the directory to PATH"), normal(" (optional but recommended)")]),
        para(""),
        para("Alternatively, build from source:"),
        codePara("cd D:\\Work\\Projects\\go_backup"),
        codePara("go build -o backup-cli.exe ./cmd/cli/"),

        heading2("3.2 Linux"),
        numberItem("Download backup-cli-linux-amd64 from the GitHub Releases page"),
        numberMixed([bold("Place the binary"), normal(" in /usr/local/bin:")]),
        codePara("sudo cp backup-cli-linux-amd64 /usr/local/bin/backup-cli"),
        codePara("sudo chmod +x /usr/local/bin/backup-cli"),

        heading2("3.3 macOS"),
        numberItem("Download backup-cli-darwin-arm64 (Apple Silicon) or backup-cli-darwin-amd64 (Intel)"),
        numberMixed([bold("Place the binary"), normal(" in /usr/local/bin:")]),
        codePara("sudo cp backup-cli-darwin-arm64 /usr/local/bin/backup-cli"),
        codePara("sudo chmod +x /usr/local/bin/backup-cli"),
        para("Note: On macOS, you may need to remove the quarantine attribute:"),
        codePara("xattr -d com.apple.quarantine /usr/local/bin/backup-cli"),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== REGISTRATION =====
        heading1("4. Client Registration"),
        para("Registration is a one-time manual process that establishes trust between the client and the orchestrator."),

        heading2("4.1 On the Client Machine"),
        para("Run the register command, pointing to the orchestrator's MQTT broker:"),
        codePara("backup-cli register --broker <BROKER_IP> --port 1883"),
        para(""),
        para("Example:"),
        codePara("backup-cli register --broker 10.11.12.250 --port 1883"),
        para(""),
        para("The client will:"),
        bullet("Generate a unique UUID (stored in agent.db)"),
        bullet("Detect its local IP address"),
        bullet("Send a registration request to the orchestrator via MQTT"),
        bullet("Wait up to 60 seconds for approval"),

        heading2("4.2 On the Orchestrator"),
        para("When the registration request arrives, a dialog pops up showing:"),
        bullet("Hostname"),
        bullet("Client UUID"),
        bullet("IP address"),
        bullet("Operating system"),
        bullet("go_backup version"),
        para(""),
        para("Click Yes to approve. The client will receive confirmation and store the broker credentials locally."),

        heading2("4.3 Verifying Registration"),
        para("On the client, you should see:"),
        codePara("Registration approved! Name: <HOSTNAME>"),
        codePara("MQTT credentials stored in config database."),
        para(""),
        para("On the orchestrator, the client should appear in the Clients view with status Online (once the agent is started)."),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== STARTING THE AGENT =====
        heading1("5. Starting the Agent"),
        para("After registration, start the agent in long-running mode. This keeps a persistent MQTT connection for receiving commands and schedule syncs."),
        codePara("backup-cli agent start --config-db agent.db"),
        para(""),
        para("The agent will:"),
        bullet("Connect to the MQTT broker"),
        bullet("Send heartbeats every 30 seconds"),
        bullet("Listen for backup commands (Trigger)"),
        bullet("Listen for schedule syncs and update local scheduled tasks"),
        bullet("Report backup results back to the orchestrator"),
        bullet("Queue status reports locally if the broker is unreachable"),

        // ===== AUTO-START =====
        heading1("6. Auto-Start on Boot"),
        para("The agent should start automatically when the machine boots. The method varies by platform."),

        heading2("6.1 Windows (Task Scheduler)"),
        para("Create a startup task that runs the agent when the user logs in:"),
        codePara('schtasks /Create /F /TN "GoBackup_Agent" /TR "\\"C:\\Tools\\backup-cli.exe\\" agent start --config-db \\"C:\\Tools\\agent.db\\"" /SC ONLOGON /RL HIGHEST'),
        para(""),
        para("Alternatively, to run as a Windows Service, use NSSM (Non-Sucking Service Manager):"),
        codePara("nssm install GoBackupAgent C:\\Tools\\backup-cli.exe"),
        codePara("nssm set GoBackupAgent AppParameters \"agent start --config-db C:\\Tools\\agent.db\""),
        codePara("nssm set GoBackupAgent AppDirectory C:\\Tools"),
        codePara("nssm start GoBackupAgent"),

        heading2("6.2 Linux (systemd)"),
        para("Create a systemd service file:"),
        codePara("sudo nano /etc/systemd/system/gobackup-agent.service"),
        para(""),
        para("Contents:"),
        codePara("[Unit]"),
        codePara("Description=GoBackup Agent"),
        codePara("After=network-online.target"),
        codePara("Wants=network-online.target"),
        codePara(""),
        codePara("[Service]"),
        codePara("Type=simple"),
        codePara("User=<YOUR_USER>"),
        codePara("ExecStart=/usr/local/bin/backup-cli agent start --config-db /home/<YOUR_USER>/.gobackup/agent.db"),
        codePara("Restart=on-failure"),
        codePara("RestartSec=10"),
        codePara(""),
        codePara("[Install]"),
        codePara("WantedBy=multi-user.target"),
        para(""),
        para("Enable and start:"),
        codePara("sudo systemctl daemon-reload"),
        codePara("sudo systemctl enable gobackup-agent"),
        codePara("sudo systemctl start gobackup-agent"),

        heading2("6.3 macOS (launchd)"),
        para("Create a launch agent plist:"),
        codePara("nano ~/Library/LaunchAgents/com.gobackup.agent.plist"),
        para(""),
        para("Contents:"),
        codePara('<?xml version="1.0" encoding="UTF-8"?>'),
        codePara('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'),
        codePara('  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'),
        codePara('<plist version="1.0">'),
        codePara("<dict>"),
        codePara("  <key>Label</key>"),
        codePara("  <string>com.gobackup.agent</string>"),
        codePara("  <key>ProgramArguments</key>"),
        codePara("  <array>"),
        codePara("    <string>/usr/local/bin/backup-cli</string>"),
        codePara("    <string>agent</string>"),
        codePara("    <string>start</string>"),
        codePara("    <string>--config-db</string>"),
        codePara("    <string>/Users/<YOUR_USER>/.gobackup/agent.db</string>"),
        codePara("  </array>"),
        codePara("  <key>RunAtLoad</key>"),
        codePara("  <true/>"),
        codePara("  <key>KeepAlive</key>"),
        codePara("  <true/>"),
        codePara("  <key>StandardOutPath</key>"),
        codePara("  <string>/tmp/gobackup-agent.log</string>"),
        codePara("  <key>StandardErrorPath</key>"),
        codePara("  <string>/tmp/gobackup-agent.err</string>"),
        codePara("</dict>"),
        codePara("</plist>"),
        para(""),
        para("Load and start:"),
        codePara("launchctl load ~/Library/LaunchAgents/com.gobackup.agent.plist"),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== SCHEDULER CROSS-PLATFORM =====
        heading1("7. Scheduled Task Management"),
        para("When you click Sync in the orchestrator, the schedule is pushed to the client. The agent then creates platform-native scheduled tasks."),

        heading2("7.1 Current Platform Support"),
        makeTable(
          ["Platform", "Scheduler", "Status"],
          [
            ["Windows", "Task Scheduler (schtasks.exe)", "Fully implemented"],
            ["Linux", "crontab", "Requires implementation (see 7.5)"],
            ["macOS", "launchd (launchctl)", "Requires implementation (see 7.5)"],
          ],
          [2500, 4000, 2860]
        ),
        para(""),
        para("Important: The automatic schedule-to-task conversion currently only works on Windows. On Linux and macOS, the agent will receive the schedule sync and store it locally, but will not automatically create cron jobs or launchd plists. See section 7.5 for manual workarounds."),

        heading2("7.2 Windows: Checking Scheduled Tasks"),
        para("List all GoBackup tasks:"),
        codePara("schtasks /query /tn \"GoBackup*\" /fo LIST /v"),
        para(""),
        para("Check a specific task:"),
        codePara("schtasks /query /tn \"GoBackup_1\" /fo LIST /v"),
        para(""),
        para("Key fields to verify:"),
        makeTable(
          ["Field", "Expected Value"],
          [
            ["Scheduled Task State", "Enabled"],
            ["Last Result", "0 (success)"],
            ["Task To Run", "Full absolute path to backup-cli.exe"],
            ["Next Run Time", "Matches your configured schedule"],
          ],
          [3000, 6360]
        ),
        para(""),
        para("Delete a task manually:"),
        codePara("schtasks /delete /tn \"GoBackup_1\" /f"),

        heading2("7.3 Linux: Checking Scheduled Tasks"),
        para("If cron integration is implemented, tasks appear in the user crontab:"),
        codePara("crontab -l"),
        para(""),
        para("Expected output:"),
        codePara("# GoBackup_1"),
        codePara("0 7 * * * /usr/local/bin/backup-cli agent run-schedule --id 1 --config-db /home/user/.gobackup/agent.db"),
        para(""),
        para("Check cron service status:"),
        codePara("sudo systemctl status cron"),
        para(""),
        para("View cron execution logs:"),
        codePara("grep CRON /var/log/syslog | tail -20"),

        heading2("7.4 macOS: Checking Scheduled Tasks"),
        para("If launchd integration is implemented, tasks appear as launch agents:"),
        codePara("launchctl list | grep gobackup"),
        para(""),
        para("Check a specific agent:"),
        codePara("launchctl print gui/$(id -u)/com.gobackup.schedule.1"),
        para(""),
        para("View logs:"),
        codePara("cat /tmp/gobackup-schedule-1.log"),
        para(""),
        para("Manually load/unload:"),
        codePara("launchctl load ~/Library/LaunchAgents/com.gobackup.schedule.1.plist"),
        codePara("launchctl unload ~/Library/LaunchAgents/com.gobackup.schedule.1.plist"),

        heading2("7.5 Manual Workaround for Linux/macOS"),
        para("Until native cron/launchd integration is implemented, you can manually create scheduled tasks that call the agent:"),
        para(""),
        heading3("Linux (crontab)"),
        para("Edit your crontab:"),
        codePara("crontab -e"),
        para(""),
        para("Add an entry using the same cron expression from the orchestrator:"),
        codePara("0 7 * * * /usr/local/bin/backup-cli agent run-schedule --id 1 --config-db /home/user/.gobackup/agent.db >> /var/log/gobackup.log 2>&1"),
        para(""),
        heading3("macOS (launchd)"),
        para("Create a plist for the scheduled backup:"),
        codePara("nano ~/Library/LaunchAgents/com.gobackup.schedule.1.plist"),
        para(""),
        para("Use the CalendarInterval key to set the schedule. Example for daily at 7:00 AM:"),
        codePara("<key>CalendarInterval</key>"),
        codePara("<dict>"),
        codePara("  <key>Hour</key>"),
        codePara("  <integer>7</integer>"),
        codePara("  <key>Minute</key>"),
        codePara("  <integer>0</integer>"),
        codePara("</dict>"),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== TROUBLESHOOTING =====
        heading1("8. Troubleshooting"),

        heading2("8.1 Registration Fails"),
        makeTable(
          ["Symptom", "Cause", "Fix"],
          [
            ["Connection refused", "Broker not running or wrong IP/port", "Verify Mosquitto is running: sc query mosquitto (Windows) or systemctl status mosquitto (Linux)"],
            ["Timeout waiting for response", "Orchestrator not connected to broker", "Check orchestrator status bar shows Broker: connected"],
            ["Timeout waiting for response", "Firewall blocking port 1883", "Open port 1883 on the broker machine firewall"],
          ],
          [2500, 3000, 3860]
        ),

        heading2("8.2 Agent Not Connecting"),
        bullet("Verify the broker address stored in agent.db is correct"),
        bullet("Check network connectivity: ping <BROKER_IP>"),
        bullet("Verify Mosquitto allows anonymous connections (for development)"),
        bullet("Check Mosquitto logs: mosquitto.log or journalctl -u mosquitto"),

        heading2("8.3 Scheduled Task Not Created (Windows)"),
        bullet("Ensure the agent is running with administrative privileges"),
        bullet("Check agent terminal for [scheduler] log messages"),
        bullet("Verify the schedule was synced: look for [agent] received schedule sync"),
        bullet("Ensure enabled=true in the sync payload"),

        heading2("8.4 Backup Runs But No Status in Orchestrator"),
        bullet("The agent queues status reports locally if the broker is unreachable"),
        bullet("Reports are drained automatically when the agent reconnects"),
        bullet("Check agent.db for pending_reports table entries"),

        heading2("8.5 Checking Agent Health"),
        para("Windows:"),
        codePara("Get-Process | Where-Object { $_.ProcessName -like \"*backup*\" }"),
        para(""),
        para("Linux/macOS:"),
        codePara("ps aux | grep backup-cli"),
        codePara("systemctl status gobackup-agent    # Linux with systemd"),
        codePara("launchctl list | grep gobackup     # macOS"),

        new Paragraph({ children: [new PageBreak()] }),

        // ===== QUICK REFERENCE =====
        heading1("9. Quick Reference"),

        heading2("9.1 Common Commands"),
        makeTable(
          ["Action", "Command"],
          [
            ["Register client", "backup-cli register --broker <IP> --port 1883"],
            ["Start agent", "backup-cli agent start --config-db agent.db"],
            ["Run a scheduled backup", "backup-cli agent run-schedule --id <N> --config-db agent.db"],
            ["Manual backup", "backup-cli backup --src <DIR> --dst <DIR> --profile documents"],
            ["Restore from archive", "backup-cli restore --archive <FILE> --dst <DIR> --password <PASS>"],
          ],
          [3200, 6160]
        ),

        heading2("9.2 Important File Locations"),
        makeTable(
          ["Platform", "Agent Config DB", "Binary Location"],
          [
            ["Windows", "Same directory as binary (agent.db)", "C:\\Tools\\backup-cli.exe"],
            ["Linux", "/home/<user>/.gobackup/agent.db", "/usr/local/bin/backup-cli"],
            ["macOS", "/Users/<user>/.gobackup/agent.db", "/usr/local/bin/backup-cli"],
          ],
          [2000, 4200, 3160]
        ),

        heading2("9.3 Cron Expression Cheat Sheet"),
        makeTable(
          ["Expression", "Meaning"],
          [
            ["0 2 * * *", "Daily at 2:00 AM"],
            ["30 6 * * *", "Daily at 6:30 AM"],
            ["0 */12 * * *", "Every 12 hours"],
            ["0 3 * * 0", "Weekly on Sunday at 3:00 AM"],
            ["0 2 * * 1-5", "Weekdays at 2:00 AM"],
            ["0 2 1,15 * *", "1st and 15th of month at 2:00 AM"],
            ["0 2 1 * *", "Monthly on the 1st at 2:00 AM"],
          ],
          [3500, 5860]
        ),

        heading2("9.4 Platform Scheduler Commands"),
        makeTable(
          ["Action", "Windows", "Linux", "macOS"],
          [
            ["List tasks", "schtasks /query /tn \"GoBackup*\" /fo LIST", "crontab -l", "launchctl list | grep gobackup"],
            ["Check status", "schtasks /query /tn \"GoBackup_1\" /fo LIST /v", "grep CRON /var/log/syslog", "launchctl print gui/$(id -u)/com.gobackup.schedule.1"],
            ["Delete task", "schtasks /delete /tn \"GoBackup_1\" /f", "crontab -e (remove line)", "launchctl unload <plist>"],
            ["Service status", "sc query GoBackupAgent", "systemctl status gobackup-agent", "launchctl list | grep gobackup"],
          ],
          [1800, 3200, 2200, 2160]
        ),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("D:\\Work\\Projects\\backup-orchestrator\\docs\\Client_Setup_Guide.docx", buffer);
  console.log("Document created: docs/Client_Setup_Guide.docx");
});
