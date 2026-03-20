"""
Main application window with sidebar navigation.
"""

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QMessageBox,
)
from gui.workers.mqtt_worker import MqttWorker
from mqtt.payloads import RegistrationResponse

from gui.theme import NAVY, BG_MAIN, font_heading, font_body
from gui.views.dashboard import DashboardView
from gui.views.clients import ClientsView
from gui.views.schedules import SchedulesView
from gui.views.history import HistoryView
from gui.views.settings import SettingsView


class NavButton(QPushButton):
    """Sidebar navigation button."""

    def __init__(self, icon_char: str, text: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_char}   {text}")
        self.setCheckable(True)
        self.setFlat(True)
        self.setFont(QFont("Segoe UI", 10))
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0 16px;
                border: none;
                border-radius: 8px;
                color: #9CA3AF;
                background: transparent;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }}
            QPushButton:checked {{
                background: rgba(255, 255, 255, 0.12);
                color: white;
                font-weight: 600;
            }}
        """)


class MainWindow(QMainWindow):
    """Main app window with sidebar + stacked views."""

    def __init__(self, db, credential_store=None, mqtt_worker=None):
        super().__init__()
        self.db = db
        self.credential_store = credential_store
        self.mqtt_worker = mqtt_worker

        self.setWindowTitle("Backup Orchestrator")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self._settings = QSettings("daPaz", "BackupOrchestrator")

        self._build_ui()
        self._setup_shortcuts()
        self._restore_geometry()
        self._select_nav(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # -- Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {NAVY};
                border-right: 1px solid rgba(255,255,255,0.1);
            }}
        """)

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(4)

        # App title
        app_title = QLabel("Backup Orchestrator")
        app_title.setFont(font_heading(14))
        app_title.setStyleSheet(
            "color: white; background: transparent; border: none; padding-bottom: 20px;"
        )
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(app_title)

        # Nav buttons
        self.nav_buttons: list[NavButton] = []
        nav_items = [
            ("\U0001F4CA", "Dashboard"),      # chart
            ("\U0001F4BB", "Clients"),         # laptop
            ("\U0001F4C5", "Schedules"),       # calendar
            ("\U0001F4DC", "History"),         # scroll
            ("\U00002699", "Settings"),        # gear
        ]

        for icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, b=btn: self._on_nav_clicked(b))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Connection status
        self.connection_label = QLabel("Broker: disconnected")
        self.connection_label.setFont(font_body(8))
        self.connection_label.setStyleSheet(
            "color: #EF4444; background: transparent; border: none; padding: 8px;"
        )
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_label.setWordWrap(True)
        sb_layout.addWidget(self.connection_label)

        root_layout.addWidget(sidebar)

        # -- Content area
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {BG_MAIN};")

        self.dashboard_view = DashboardView(self.db, self.mqtt_worker)
        self.clients_view = ClientsView(self.db, self.mqtt_worker)
        self.schedules_view = SchedulesView(self.db, self.credential_store, self.mqtt_worker)
        self.history_view = HistoryView(self.db)
        self.settings_view = SettingsView(self.db, self.credential_store)
        self.settings_view.connect_requested.connect(self._on_connect_requested)

        self.stack.addWidget(self.dashboard_view)    # 0
        self.stack.addWidget(self.clients_view)      # 1
        self.stack.addWidget(self.schedules_view)    # 2
        self.stack.addWidget(self.history_view)      # 3
        self.stack.addWidget(self.settings_view)     # 4

        root_layout.addWidget(self.stack, stretch=1)

    def _setup_shortcuts(self):
        for i in range(5):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda idx=i: self._navigate_to(idx))

    def _navigate_to(self, index: int):
        self._select_nav(index)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _select_nav(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _on_nav_clicked(self, clicked_btn: NavButton):
        idx = self.nav_buttons.index(clicked_btn)
        self._select_nav(idx)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _on_connect_requested(self, host: str, port: int, username: str, password: str):
        """Handle Save & Connect from Settings -- start or restart the MQTT worker."""
        # Stop existing worker if running
        if self.mqtt_worker and self.mqtt_worker.isRunning():
            self.mqtt_worker.stop()
            self.mqtt_worker.wait(3000)

        self.mqtt_worker = MqttWorker(host, port, username, password)
        self.mqtt_worker.connection_changed.connect(self.set_connection_status)
        self.mqtt_worker.client_registered.connect(self._on_client_registered)
        self.mqtt_worker.heartbeat_received.connect(self._on_heartbeat)
        self.mqtt_worker.backup_status_received.connect(self._on_backup_status)
        self.mqtt_worker.start()

        # Update views with the new worker
        self.dashboard_view.mqtt_worker = self.mqtt_worker
        self.clients_view.mqtt_worker = self.mqtt_worker
        self.schedules_view.mqtt_worker = self.mqtt_worker

    def _on_client_registered(self, payload: dict):
        """Handle a client registration request -- show approval dialog."""
        client_uuid = payload.get("client_uuid", "unknown")
        hostname = payload.get("hostname", "unknown")
        ip_address = payload.get("ip_address", "unknown")
        os_info = payload.get("os", "unknown")
        version = payload.get("go_backup_version", "unknown")

        print(f"[MQTT] Registration request from {hostname} ({client_uuid})")

        reply = QMessageBox.question(
            self,
            "Client Registration",
            f"A new client wants to register:\n\n"
            f"  Hostname: {hostname}\n"
            f"  UUID: {client_uuid}\n"
            f"  IP: {ip_address}\n"
            f"  OS: {os_info}\n"
            f"  Version: {version}\n\n"
            f"Approve this client?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Add or update client in database
            existing = self.db.get_client(client_uuid)
            if not existing:
                self.db.add_client(
                    uuid=client_uuid,
                    name=hostname,
                    hostname=hostname,
                    ip_address=ip_address,
                    os=os_info,
                )
            else:
                self.db.update_client(
                    client_uuid,
                    hostname=hostname,
                    ip_address=ip_address,
                    os=os_info,
                )

            # Send approval response
            resp = RegistrationResponse(
                approved=True,
                mqtt_username="",
                mqtt_password="",
                client_name=hostname,
            )
            if self.mqtt_worker:
                self.mqtt_worker.publish_registration_response(client_uuid, resp)
                print(f"[MQTT] Approved registration for {hostname}")

            # Refresh views
            if hasattr(self.clients_view, "refresh"):
                self.clients_view.refresh()
            if hasattr(self.dashboard_view, "refresh"):
                self.dashboard_view.refresh()
        else:
            # Send denial
            resp = RegistrationResponse(approved=False)
            if self.mqtt_worker:
                self.mqtt_worker.publish_registration_response(client_uuid, resp)
                print(f"[MQTT] Denied registration for {hostname}")

    def _on_heartbeat(self, client_uuid: str, payload: dict):
        from datetime import datetime, timezone
        status = payload.get("status", "idle")
        db_status = "online" if status == "idle" else status
        self.db.update_client(client_uuid, status=db_status,
                              last_seen_at=datetime.now(timezone.utc).isoformat())

    def _on_backup_status(self, client_uuid: str, payload: dict):
        self.db.add_backup_history(
            client_uuid=client_uuid,
            profile=payload.get("profile", "unknown"),
            started_at=payload.get("started_at", ""),
            completed_at=payload.get("completed_at"),
            status=payload.get("status", "unknown"),
            method=payload.get("method", "unknown"),
            archive_path=payload.get("archive_path"),
            file_count=payload.get("file_count"),
            error_message=payload.get("error_message"),
        )

    def set_connection_status(self, connected: bool):
        if connected:
            self.connection_label.setText("Broker: connected")
            self.connection_label.setStyleSheet(
                "color: #22C55E; background: transparent; border: none; padding: 8px;"
            )
        else:
            self.connection_label.setText("Broker: disconnected")
            self.connection_label.setStyleSheet(
                "color: #EF4444; background: transparent; border: none; padding: 8px;"
            )

    # -- Window geometry persistence
    def _restore_geometry(self):
        geometry = self._settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self._settings.value("window/state")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())
        super().closeEvent(event)
