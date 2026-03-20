"""
Settings view -- broker config, master password, defaults.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QLineEdit, QSpinBox, QPushButton, QTextEdit, QMessageBox, QFormLayout,
)
from gui.theme import (
    NAVY, BG_MAIN, CARD_STYLE, BORDER,
    BUTTON_STYLE, BUTTON_SECONDARY_STYLE, INPUT_STYLE,
    TEXT_PRIMARY, TEXT_SECONDARY, POSITIVE,
    font_heading, font_body,
)


class SettingsView(QWidget):
    """Application settings view."""

    # Emitted when the user clicks Connect — MainWindow handles the actual connection
    connect_requested = Signal(str, int, str, str)  # host, port, username, password

    def __init__(self, db, credential_store=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.credential_store = credential_store
        self.setStyleSheet(f"background: {BG_MAIN};")
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background: {BG_MAIN}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background: {BG_MAIN};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QLabel("Settings")
        header.setFont(font_heading(20))
        header.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        layout.addWidget(header)

        # -- Broker Configuration Card
        broker_card = QFrame()
        broker_card.setObjectName("card")
        broker_card.setStyleSheet(CARD_STYLE)
        bl = QVBoxLayout(broker_card)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(12)

        broker_title = QLabel("MQTT Broker")
        broker_title.setFont(font_heading(14))
        broker_title.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        bl.addWidget(broker_title)

        form = QFormLayout()
        form.setSpacing(8)

        self.broker_host = QLineEdit()
        self.broker_host.setStyleSheet(INPUT_STYLE)
        self.broker_host.setPlaceholderText("localhost")
        form.addRow("Host:", self.broker_host)

        self.broker_port = QSpinBox()
        self.broker_port.setRange(1, 65535)
        self.broker_port.setValue(1883)
        form.addRow("Port:", self.broker_port)

        self.broker_user = QLineEdit()
        self.broker_user.setStyleSheet(INPUT_STYLE)
        self.broker_user.setPlaceholderText("orchestrator")
        form.addRow("Username:", self.broker_user)

        self.broker_pass = QLineEdit()
        self.broker_pass.setStyleSheet(INPUT_STYLE)
        self.broker_pass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.broker_pass)

        bl.addLayout(form)

        broker_btn_row = QHBoxLayout()
        broker_btn_row.addStretch()

        test_btn = QPushButton("Test Connection")
        test_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._on_test_connection)
        broker_btn_row.addWidget(test_btn)

        save_broker_btn = QPushButton("Save")
        save_broker_btn.setStyleSheet(BUTTON_STYLE)
        save_broker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_broker_btn.clicked.connect(self._on_save_broker)
        broker_btn_row.addWidget(save_broker_btn)

        connect_btn = QPushButton("Save && Connect")
        connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {POSITIVE};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 10pt;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #16A34A; }}
        """)
        connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_btn.clicked.connect(self._on_save_and_connect)
        broker_btn_row.addWidget(connect_btn)

        bl.addLayout(broker_btn_row)
        layout.addWidget(broker_card)

        # -- Master Password Card
        pw_card = QFrame()
        pw_card.setObjectName("card")
        pw_card.setStyleSheet(CARD_STYLE)
        pl = QVBoxLayout(pw_card)
        pl.setContentsMargins(20, 16, 20, 16)
        pl.setSpacing(12)

        pw_title = QLabel("Master Password")
        pw_title.setFont(font_heading(14))
        pw_title.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        pl.addWidget(pw_title)

        pw_form = QFormLayout()
        pw_form.setSpacing(8)

        self.current_pw = QLineEdit()
        self.current_pw.setStyleSheet(INPUT_STYLE)
        self.current_pw.setEchoMode(QLineEdit.EchoMode.Password)
        pw_form.addRow("Current:", self.current_pw)

        self.new_pw = QLineEdit()
        self.new_pw.setStyleSheet(INPUT_STYLE)
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        pw_form.addRow("New:", self.new_pw)

        self.confirm_pw = QLineEdit()
        self.confirm_pw.setStyleSheet(INPUT_STYLE)
        self.confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        pw_form.addRow("Confirm:", self.confirm_pw)

        pl.addLayout(pw_form)

        change_pw_btn = QPushButton("Change Password")
        change_pw_btn.setStyleSheet(BUTTON_STYLE)
        change_pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_pw_btn.clicked.connect(self._on_change_password)
        pw_btn_row = QHBoxLayout()
        pw_btn_row.addStretch()
        pw_btn_row.addWidget(change_pw_btn)
        pl.addLayout(pw_btn_row)

        layout.addWidget(pw_card)

        # -- Default Backup Settings Card
        defaults_card = QFrame()
        defaults_card.setObjectName("card")
        defaults_card.setStyleSheet(CARD_STYLE)
        dl = QVBoxLayout(defaults_card)
        dl.setContentsMargins(20, 16, 20, 16)
        dl.setSpacing(12)

        defaults_title = QLabel("Default Backup Settings")
        defaults_title.setFont(font_heading(14))
        defaults_title.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        dl.addWidget(defaults_title)

        df = QFormLayout()
        df.setSpacing(8)

        self.default_workers = QSpinBox()
        self.default_workers.setRange(1, 32)
        self.default_workers.setValue(4)
        df.addRow("Workers:", self.default_workers)

        self.default_blocklist = QTextEdit()
        self.default_blocklist.setMaximumHeight(120)
        self.default_blocklist.setPlaceholderText("One directory name per line...")
        df.addRow("Blocklist:", self.default_blocklist)

        dl.addLayout(df)

        save_defaults_btn = QPushButton("Save Defaults")
        save_defaults_btn.setStyleSheet(BUTTON_STYLE)
        save_defaults_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_defaults_btn.clicked.connect(self._on_save_defaults)
        dd_row = QHBoxLayout()
        dd_row.addStretch()
        dd_row.addWidget(save_defaults_btn)
        dl.addLayout(dd_row)

        layout.addWidget(defaults_card)

        # -- About Card
        about_card = QFrame()
        about_card.setObjectName("card")
        about_card.setStyleSheet(CARD_STYLE)
        al = QVBoxLayout(about_card)
        al.setContentsMargins(20, 16, 20, 16)

        about_title = QLabel("About")
        about_title.setFont(font_heading(14))
        about_title.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        al.addWidget(about_title)

        about_text = QLabel("Backup Orchestrator v0.1.0\nCentralized backup management for go_backup agents.")
        about_text.setFont(font_body(10))
        about_text.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; border: none;")
        about_text.setWordWrap(True)
        al.addWidget(about_text)

        layout.addWidget(about_card)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        """Load settings from database."""
        self.broker_host.setText(self.db.get_setting("broker_host", "localhost"))
        self.broker_port.setValue(int(self.db.get_setting("broker_port", "1883")))
        self.broker_user.setText(self.db.get_setting("broker_username", "orchestrator"))
        self.broker_pass.setText(self.db.get_setting("broker_password", ""))
        self.default_workers.setValue(int(self.db.get_setting("default_workers", "4")))
        self.default_blocklist.setPlainText(self.db.get_setting("default_blocklist", ""))

    def _on_test_connection(self):
        """Test MQTT broker connection."""
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            user = self.broker_user.text().strip()
            pw = self.broker_pass.text().strip()
            if user:
                client.username_pw_set(user, pw)
            client.connect(
                self.broker_host.text().strip() or "localhost",
                self.broker_port.value(),
                keepalive=5,
            )
            client.disconnect()
            QMessageBox.information(self, "Success", "Connected to MQTT broker successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Connection Failed", f"Could not connect to broker:\n{e}")

    def _on_save_broker(self):
        self._save_broker_settings()
        QMessageBox.information(self, "Saved", "Broker settings saved.")

    def _on_save_and_connect(self):
        self._save_broker_settings()
        host = self.broker_host.text().strip() or "localhost"
        port = self.broker_port.value()
        username = self.broker_user.text().strip()
        password = self.broker_pass.text().strip()
        self.connect_requested.emit(host, port, username, password)

    def _save_broker_settings(self):
        self.db.set_setting("broker_host", self.broker_host.text().strip() or "localhost")
        self.db.set_setting("broker_port", str(self.broker_port.value()))
        self.db.set_setting("broker_username", self.broker_user.text().strip())
        self.db.set_setting("broker_password", self.broker_pass.text().strip())

    def _on_save_defaults(self):
        self.db.set_setting("default_workers", str(self.default_workers.value()))
        self.db.set_setting("default_blocklist", self.default_blocklist.toPlainText())
        QMessageBox.information(self, "Saved", "Default settings saved.")

    def _on_change_password(self):
        if not self.credential_store:
            QMessageBox.warning(self, "Error", "Credential store not available.")
            return

        current = self.current_pw.text()
        new = self.new_pw.text()
        confirm = self.confirm_pw.text()

        if new != confirm:
            QMessageBox.warning(self, "Mismatch", "New password and confirmation do not match.")
            return
        if not new:
            QMessageBox.warning(self, "Empty", "New password cannot be empty.")
            return

        if self.credential_store.change_master_password(current, new):
            QMessageBox.information(self, "Changed", "Master password updated successfully.")
            self.current_pw.clear()
            self.new_pw.clear()
            self.confirm_pw.clear()
        else:
            QMessageBox.warning(self, "Failed", "Current password is incorrect.")
