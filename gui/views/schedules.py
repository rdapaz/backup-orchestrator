"""
Schedules view -- manage backup schedules per client.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QFileDialog,
)
from gui.theme import (
    NAVY, BG_MAIN, CARD_STYLE, TABLE_STYLE, BORDER,
    BUTTON_STYLE, BUTTON_SECONDARY_STYLE, INPUT_STYLE, COMBO_STYLE,
    TEXT_PRIMARY, TEXT_SECONDARY, POSITIVE,
    font_heading, font_body,
)

PROFILES = ["all", "documents", "jetbrains", "databases", "photos"]

CRON_PRESETS = {
    "Daily at 2am":          "0 2 * * *",
    "Every 12 hours":        "0 */12 * * *",
    "Weekly (Sunday 3am)":   "0 3 * * 0",
    "Every 2 weeks":         "0 2 1,15 * *",
    "Monthly (1st at 2am)":  "0 2 1 * *",
    "Custom":                "",
}


class AddScheduleDialog(QDialog):
    """Dialog for adding a new backup schedule."""

    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Schedule")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Client selector
        self.client_combo = QComboBox()
        self.client_combo.setStyleSheet(COMBO_STYLE)
        for c in clients:
            self.client_combo.addItem(c.name, c.uuid)
        layout.addRow("Client:", self.client_combo)

        # Profile
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(COMBO_STYLE)
        self.profile_combo.addItems(PROFILES)
        layout.addRow("Profile:", self.profile_combo)

        # Source directory
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setStyleSheet(INPUT_STYLE)
        self.src_edit.setPlaceholderText(r"e.g. C:\Users\user")
        src_row.addWidget(self.src_edit)
        src_browse = QPushButton("Browse...")
        src_browse.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        src_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        src_browse.clicked.connect(lambda: self._browse_dir(self.src_edit))
        src_row.addWidget(src_browse)
        layout.addRow("Source Dir:", src_row)

        # Destination directory
        dst_row = QHBoxLayout()
        self.dst_edit = QLineEdit()
        self.dst_edit.setStyleSheet(INPUT_STYLE)
        self.dst_edit.setPlaceholderText(r"e.g. D:\Backups")
        dst_row.addWidget(self.dst_edit)
        dst_browse = QPushButton("Browse...")
        dst_browse.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        dst_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        dst_browse.clicked.connect(lambda: self._browse_dir(self.dst_edit))
        dst_row.addWidget(dst_browse)
        layout.addRow("Dest Dir:", dst_row)

        # Cron expression
        self.cron_preset = QComboBox()
        self.cron_preset.setStyleSheet(COMBO_STYLE)
        self.cron_preset.addItems(CRON_PRESETS.keys())
        self.cron_preset.currentTextChanged.connect(self._on_preset_changed)
        layout.addRow("Frequency:", self.cron_preset)

        cron_row = QHBoxLayout()
        self.cron_edit = QLineEdit()
        self.cron_edit.setStyleSheet(INPUT_STYLE)
        self.cron_edit.setPlaceholderText("0 2 * * *")
        self.cron_edit.setText("0 2 * * *")
        cron_row.addWidget(self.cron_edit)
        from gui.widgets.help_window import make_help_button
        cron_row.addWidget(make_help_button("Cron Expression Format", self))
        layout.addRow("Cron Expr:", cron_row)

        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(INPUT_STYLE)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Leave empty for auto-generated")
        layout.addRow("Password:", self.password_edit)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: #F3F4F6; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Add Schedule")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(save_btn)

        layout.addRow(btn_row)

    def _on_preset_changed(self, text: str):
        cron = CRON_PRESETS.get(text, "")
        if cron:
            self.cron_edit.setText(cron)
            self.cron_edit.setReadOnly(True)
        else:
            self.cron_edit.setReadOnly(False)
            self.cron_edit.clear()
            self.cron_edit.setFocus()

    def _browse_dir(self, line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if path:
            line_edit.setText(path)

    def _validate_and_accept(self):
        if not self.src_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Source directory is required.")
            return
        if not self.dst_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Destination directory is required.")
            return
        if not self.cron_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Cron expression is required.")
            return
        self.accept()


class EditScheduleDialog(QDialog):
    """Dialog for editing an existing backup schedule."""

    def __init__(self, schedule, client_name: str, password: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Schedule")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Client (read-only)
        client_label = QLineEdit(client_name)
        client_label.setStyleSheet(INPUT_STYLE)
        client_label.setReadOnly(True)
        layout.addRow("Client:", client_label)

        # Profile
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(COMBO_STYLE)
        self.profile_combo.addItems(PROFILES)
        idx = self.profile_combo.findText(schedule.profile)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        layout.addRow("Profile:", self.profile_combo)

        # Source directory
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit(schedule.src_dir)
        self.src_edit.setStyleSheet(INPUT_STYLE)
        src_row.addWidget(self.src_edit)
        src_browse = QPushButton("Browse...")
        src_browse.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        src_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        src_browse.clicked.connect(lambda: self._browse_dir(self.src_edit))
        src_row.addWidget(src_browse)
        layout.addRow("Source Dir:", src_row)

        # Destination directory
        dst_row = QHBoxLayout()
        self.dst_edit = QLineEdit(schedule.dst_dir)
        self.dst_edit.setStyleSheet(INPUT_STYLE)
        dst_row.addWidget(self.dst_edit)
        dst_browse = QPushButton("Browse...")
        dst_browse.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        dst_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        dst_browse.clicked.connect(lambda: self._browse_dir(self.dst_edit))
        dst_row.addWidget(dst_browse)
        layout.addRow("Dest Dir:", dst_row)

        # Cron expression
        self.cron_preset = QComboBox()
        self.cron_preset.setStyleSheet(COMBO_STYLE)
        self.cron_preset.addItems(CRON_PRESETS.keys())
        # Match existing cron to a preset, or select Custom
        preset_match = next(
            (name for name, expr in CRON_PRESETS.items() if expr == schedule.cron_expr),
            "Custom",
        )
        self.cron_preset.setCurrentText(preset_match)
        self.cron_preset.currentTextChanged.connect(self._on_preset_changed)
        layout.addRow("Frequency:", self.cron_preset)

        cron_row = QHBoxLayout()
        self.cron_edit = QLineEdit(schedule.cron_expr)
        self.cron_edit.setStyleSheet(INPUT_STYLE)
        if preset_match != "Custom":
            self.cron_edit.setReadOnly(True)
        cron_row.addWidget(self.cron_edit)
        from gui.widgets.help_window import make_help_button
        cron_row.addWidget(make_help_button("Cron Expression Format", self))
        layout.addRow("Cron Expr:", cron_row)

        # Enabled
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(schedule.enabled)
        layout.addRow("", self.enabled_check)

        # Password
        self.password_edit = QLineEdit(password)
        self.password_edit.setStyleSheet(INPUT_STYLE)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Leave empty to keep current")
        layout.addRow("Password:", self.password_edit)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: #F3F4F6; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(save_btn)

        layout.addRow(btn_row)

    def _browse_dir(self, line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if path:
            line_edit.setText(path)

    def _on_preset_changed(self, text: str):
        cron = CRON_PRESETS.get(text, "")
        if cron:
            self.cron_edit.setText(cron)
            self.cron_edit.setReadOnly(True)
        else:
            self.cron_edit.setReadOnly(False)
            self.cron_edit.clear()
            self.cron_edit.setFocus()

    def _validate_and_accept(self):
        if not self.src_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Source directory is required.")
            return
        if not self.dst_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Destination directory is required.")
            return
        if not self.cron_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Cron expression is required.")
            return
        self.accept()


class SchedulesView(QWidget):
    """Schedule management view."""

    def __init__(self, db, credential_store=None, mqtt_worker=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.credential_store = credential_store
        self.mqtt_worker = mqtt_worker
        self.setStyleSheet(f"background: {BG_MAIN};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- Header
        header_row = QHBoxLayout()
        header = QLabel("Schedules")
        header.setFont(font_heading(20))
        header.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        header_row.addWidget(header)
        from gui.widgets.help_window import make_help_button
        header_row.addWidget(make_help_button("Schedules", self))
        header_row.addStretch()

        self.add_btn = QPushButton("Add Schedule")
        self.add_btn.setStyleSheet(BUTTON_STYLE)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add_schedule)
        header_row.addWidget(self.add_btn)

        layout.addLayout(header_row)

        # -- Schedules table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet(CARD_STYLE)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Client", "Profile", "Source", "Destination", "Frequency", "Enabled", "Actions"]
        )
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 310)

        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, stretch=1)

    def refresh(self):
        """Reload schedules from database."""
        schedules = self.db.get_schedules()
        clients = {c.uuid: c.name for c in self.db.get_clients()}

        self.table.setRowCount(len(schedules))
        for row, sched in enumerate(schedules):
            client_name = clients.get(sched.client_uuid, sched.client_uuid[:8])
            items = [
                client_name,
                sched.profile,
                sched.src_dir,
                sched.dst_dir,
                sched.cron_expr,
                "Yes" if sched.enabled else "No",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 5:
                    item.setForeground(QColor(POSITIVE if sched.enabled else TEXT_SECONDARY))
                self.table.setItem(row, col, item)

            # Actions cell with trigger button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 8px; font-size: 9pt; }")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, sid=sched.id: self._on_edit(sid))
            actions_layout.addWidget(edit_btn)

            trigger_btn = QPushButton("Trigger")
            trigger_btn.setStyleSheet(BUTTON_STYLE + "QPushButton { padding: 2px 8px; font-size: 9pt; }")
            trigger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            trigger_btn.setProperty("schedule_id", sched.id)
            trigger_btn.clicked.connect(lambda checked, sid=sched.id: self._on_trigger(sid))
            actions_layout.addWidget(trigger_btn)

            sync_btn = QPushButton("Sync")
            sync_btn.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 8px; font-size: 9pt; }")
            sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sync_btn.clicked.connect(lambda checked, cid=sched.client_uuid: self._on_sync(cid))
            actions_layout.addWidget(sync_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {NEGATIVE}; color: white; border: none;
                    border-radius: 4px; padding: 2px 8px; font-size: 9pt;
                }}
                QPushButton:hover {{ background-color: #DC2626; }}
            """)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(
                lambda checked, sid=sched.id, cid=sched.client_uuid: self._on_delete(sid, cid)
            )
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 6, actions_widget)

    def _on_edit(self, schedule_id: int):
        """Open edit dialog for an existing schedule."""
        schedules = self.db.get_schedules()
        sched = next((s for s in schedules if s.id == schedule_id), None)
        if not sched:
            return

        clients = {c.uuid: c.name for c in self.db.get_clients()}
        client_name = clients.get(sched.client_uuid, sched.client_uuid[:8])

        # Get current password
        password = ""
        if self.credential_store and self.credential_store.is_unlocked():
            password = self.credential_store.retrieve(f"backup:{schedule_id}") or ""

        dialog = EditScheduleDialog(sched, client_name, password, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.db.update_schedule(
                schedule_id,
                profile=dialog.profile_combo.currentText(),
                src_dir=dialog.src_edit.text().strip(),
                dst_dir=dialog.dst_edit.text().strip(),
                cron_expr=dialog.cron_edit.text().strip(),
                enabled=dialog.enabled_check.isChecked(),
            )

            # Update password if changed
            new_password = dialog.password_edit.text().strip()
            if new_password and self.credential_store and self.credential_store.is_unlocked():
                self.credential_store.store(f"backup:{schedule_id}", new_password)

            self.refresh()

    def _on_add_schedule(self):
        clients = self.db.get_clients()
        if not clients:
            QMessageBox.information(self, "No Clients", "Register at least one client before adding schedules.")
            return

        dialog = AddScheduleDialog(clients, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_uuid = dialog.client_combo.currentData()
            password = dialog.password_edit.text().strip()

            schedule_id = self.db.add_schedule(
                client_uuid=client_uuid,
                profile=dialog.profile_combo.currentText(),
                src_dir=dialog.src_edit.text().strip(),
                dst_dir=dialog.dst_edit.text().strip(),
                cron_expr=dialog.cron_edit.text().strip(),
            )

            # Store password in credential store if provided
            if password and self.credential_store and self.credential_store.is_unlocked():
                self.credential_store.store(f"backup:{schedule_id}", password)

            self.refresh()

    def _on_trigger(self, schedule_id: int):
        """Trigger an on-demand backup for this schedule."""
        if not self.mqtt_worker:
            QMessageBox.warning(self, "Not Connected", "MQTT is not connected.")
            return

        schedules = self.db.get_schedules()
        sched = next((s for s in schedules if s.id == schedule_id), None)
        if not sched:
            return

        # Retrieve password from credential store
        password = ""
        if self.credential_store and self.credential_store.is_unlocked():
            password = self.credential_store.retrieve(f"backup:{schedule_id}") or ""

        self.mqtt_worker.publish_command(sched.client_uuid, {
            "action": "start_backup",
            "config": {
                "src_dir": sched.src_dir,
                "dst_dir": sched.dst_dir,
                "profile": sched.profile,
                "password": password,
            },
        })
        QMessageBox.information(self, "Triggered", f"Backup command sent to client.")

    def _on_sync(self, client_uuid: str, silent: bool = False):
        """Sync all schedules for a client to the remote agent."""
        if not self.mqtt_worker:
            if not silent:
                QMessageBox.warning(self, "Not Connected", "MQTT is not connected.")
            return

        schedules = self.db.get_schedules()
        client_schedules = [s for s in schedules if s.client_uuid == client_uuid and s.enabled]

        schedule_list = []
        for s in client_schedules:
            password = ""
            if self.credential_store and self.credential_store.is_unlocked():
                password = self.credential_store.retrieve(f"backup:{s.id}") or ""
            schedule_list.append({
                "id": s.id,
                "profile": s.profile,
                "src_dir": s.src_dir,
                "dst_dir": s.dst_dir,
                "cron_expr": s.cron_expr,
                "enabled": True,
                "password": password,
            })

        self.mqtt_worker.publish_schedule_sync(client_uuid, schedule_list)
        if not silent:
            QMessageBox.information(
                self, "Synced",
                f"Pushed {len(schedule_list)} schedule(s) to client."
            )

    def _on_delete(self, schedule_id: int, client_uuid: str):
        """Delete a schedule and sync the change to the client."""
        reply = QMessageBox.question(
            self,
            "Delete Schedule",
            "Are you sure you want to delete this schedule?\n\n"
            "This will also remove the scheduled task on the client.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove from database
        self.db.remove_schedule(schedule_id)

        # Remove stored password
        if self.credential_store and self.credential_store.is_unlocked():
            self.credential_store.store(f"backup:{schedule_id}", "")

        # Sync remaining schedules to the client (this removes the deleted task)
        if self.mqtt_worker:
            self._on_sync(client_uuid, silent=True)

        self.refresh()
        QMessageBox.information(self, "Deleted", "Schedule deleted and client synced.")
