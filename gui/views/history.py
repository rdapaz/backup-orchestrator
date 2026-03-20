"""
History view -- browse backup execution history.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QDateEdit, QFileDialog, QMessageBox, QDialog,
    QFormLayout, QLineEdit,
)
from PySide6.QtCore import QDate
from gui.theme import (
    NAVY, BG_MAIN, CARD_STYLE, TABLE_STYLE, BORDER,
    BUTTON_STYLE, BUTTON_SECONDARY_STYLE, INPUT_STYLE, COMBO_STYLE,
    POSITIVE, NEGATIVE, WARNING, TEXT_PRIMARY, TEXT_SECONDARY,
    font_heading, font_body,
)


class HistoryView(QWidget):
    """Backup history browser with filters and CSV export."""

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
        header = QLabel("Backup History")
        header.setFont(font_heading(20))
        header.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        header_row.addWidget(header)
        from gui.widgets.help_window import make_help_button
        header_row.addWidget(make_help_button("History", self))
        header_row.addStretch()

        export_btn = QPushButton("Export CSV")
        export_btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._on_export)
        header_row.addWidget(export_btn)

        layout.addLayout(header_row)

        # -- Filter card
        filter_card = QFrame()
        filter_card.setObjectName("card")
        filter_card.setStyleSheet(CARD_STYLE)
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(16, 8, 16, 8)
        fl.setSpacing(12)

        fl.addWidget(QLabel("Client:"))
        self.client_filter = QComboBox()
        self.client_filter.setStyleSheet(COMBO_STYLE)
        self.client_filter.addItem("All Clients", None)
        self.client_filter.currentIndexChanged.connect(lambda: self.refresh())
        fl.addWidget(self.client_filter)

        fl.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.setStyleSheet(COMBO_STYLE)
        self.status_filter.addItems(["All", "Success", "Failure", "In Progress", "Cancelled"])
        self.status_filter.currentIndexChanged.connect(lambda: self.refresh())
        fl.addWidget(self.status_filter)

        fl.addWidget(QLabel("Profile:"))
        self.profile_filter = QComboBox()
        self.profile_filter.setStyleSheet(COMBO_STYLE)
        self.profile_filter.addItems(["All", "all", "documents", "jetbrains", "databases", "photos"])
        self.profile_filter.currentIndexChanged.connect(lambda: self.refresh())
        fl.addWidget(self.profile_filter)

        fl.addStretch()
        layout.addWidget(filter_card)

        # -- History table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet(CARD_STYLE)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Started", "Completed", "Client", "Profile", "Status", "Method", "Files", "Error", "Actions"]
        )
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 60)
        self.table.setColumnWidth(8, 80)

        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, stretch=1)

    def refresh(self):
        """Reload history from database with filters applied."""
        # Populate client filter if empty
        if self.client_filter.count() <= 1:
            self.client_filter.blockSignals(True)
            clients = self.db.get_clients()
            for c in clients:
                self.client_filter.addItem(c.name, c.uuid)
            self.client_filter.blockSignals(False)

        client_uuid = self.client_filter.currentData()
        history = self.db.get_backup_history(client_uuid=client_uuid, limit=500)

        # Apply status filter
        status_map = {1: "success", 2: "failure", 3: "in_progress", 4: "cancelled"}
        status_idx = self.status_filter.currentIndex()
        if status_idx > 0:
            target = status_map.get(status_idx, "")
            history = [h for h in history if h.status == target]

        # Apply profile filter
        profile_idx = self.profile_filter.currentIndex()
        if profile_idx > 0:
            target_profile = self.profile_filter.currentText()
            history = [h for h in history if h.profile == target_profile]

        clients = {c.uuid: c.name for c in self.db.get_clients()}

        STATUS_COLORS = {
            "success": POSITIVE, "failure": NEGATIVE,
            "in_progress": WARNING, "cancelled": TEXT_SECONDARY,
        }

        self.table.setRowCount(len(history))
        for row, entry in enumerate(history):
            client_name = clients.get(entry.client_uuid, entry.client_uuid[:8])
            items = [
                entry.started_at[:16] if entry.started_at else "--",
                entry.completed_at[:16] if entry.completed_at else "--",
                client_name,
                entry.profile,
                entry.status,
                entry.method,
                str(entry.file_count or "--"),
                entry.error_message or "",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 4:
                    item.setForeground(QColor(STATUS_COLORS.get(entry.status, TEXT_SECONDARY)))
                self.table.setItem(row, col, item)

            # Restore button (only for successful backups with an archive path)
            if entry.status == "success" and entry.archive_path:
                restore_btn = QPushButton("Restore")
                restore_btn.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 8px; font-size: 9pt; }")
                restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                restore_btn.clicked.connect(
                    lambda checked, hid=entry.id, path=entry.archive_path, cuuid=entry.client_uuid:
                        self._on_restore(hid, path, cuuid)
                )
                self.table.setCellWidget(row, 8, restore_btn)

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "backup_history.csv", "CSV Files (*.csv)")
        if not path:
            return

        import csv
        history = self.db.get_backup_history(limit=10000)
        clients = {c.uuid: c.name for c in self.db.get_clients()}

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Started", "Completed", "Client", "Profile", "Status", "Method", "Files", "Error"])
            for entry in history:
                writer.writerow([
                    entry.started_at or "",
                    entry.completed_at or "",
                    clients.get(entry.client_uuid, entry.client_uuid),
                    entry.profile,
                    entry.status,
                    entry.method,
                    entry.file_count or "",
                    entry.error_message or "",
                ])

        QMessageBox.information(self, "Exported", f"History exported to {path}")

    def _on_restore(self, history_id: int, archive_path: str, client_uuid: str):
        """Initiate a restore for a backup entry."""
        # Try to retrieve the stored password
        stored_password = ""
        if self.credential_store and self.credential_store.is_unlocked():
            stored_password = self.credential_store.retrieve(f"archive:{history_id}") or ""

        # Show restore dialog
        dialog = RestoreDialog(archive_path, stored_password, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        password = dialog.password_edit.text().strip()
        dst_dir = dialog.dst_edit.text().strip()

        if not password:
            QMessageBox.warning(self, "Password Required", "Archive password is required for restore.")
            return
        if not dst_dir:
            QMessageBox.warning(self, "Destination Required", "Restore destination directory is required.")
            return

        if not self.mqtt_worker:
            QMessageBox.warning(self, "Not Connected", "MQTT is not connected.")
            return

        # Send restore command to the client
        self.mqtt_worker.publish_command(client_uuid, {
            "action": "start_restore",
            "config": {
                "archive_path": archive_path,
                "dst_dir": dst_dir,
                "password": password,
            },
        })
        QMessageBox.information(self, "Restore Initiated",
                                f"Restore command sent to client.\n\nArchive: {archive_path}\nDestination: {dst_dir}")


class RestoreDialog(QDialog):
    """Dialog for configuring a restore operation."""

    def __init__(self, archive_path: str, password: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Restore Backup")
        self.setMinimumWidth(550)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Archive path (read-only)
        archive_edit = QLineEdit(archive_path)
        archive_edit.setStyleSheet(INPUT_STYLE)
        archive_edit.setReadOnly(True)
        layout.addRow("Archive:", archive_edit)

        # Password
        self.password_edit = QLineEdit(password)
        self.password_edit.setStyleSheet(INPUT_STYLE)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        if password:
            self.password_edit.setPlaceholderText("Password retrieved from credential store")
        else:
            self.password_edit.setPlaceholderText("Enter archive password")
        layout.addRow("Password:", self.password_edit)

        # Show password toggle
        self.show_pass_btn = QPushButton("Show")
        self.show_pass_btn.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        self.show_pass_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_pass_btn.clicked.connect(self._toggle_password_visibility)
        layout.addRow("", self.show_pass_btn)

        # Destination directory
        self.dst_edit = QLineEdit()
        self.dst_edit.setStyleSheet(INPUT_STYLE)
        self.dst_edit.setPlaceholderText(r"e.g. C:\Users\user\Restored")
        layout.addRow("Restore To:", self.dst_edit)

        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(BUTTON_SECONDARY_STYLE + "QPushButton { padding: 2px 12px; font-size: 9pt; }")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)
        layout.addRow("", browse_btn)

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

        restore_btn = QPushButton("Restore")
        restore_btn.setStyleSheet(BUTTON_STYLE)
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(self.accept)
        btn_row.addWidget(restore_btn)

        layout.addRow(btn_row)

    def _toggle_password_visibility(self):
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pass_btn.setText("Hide")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pass_btn.setText("Show")

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Restore Destination")
        if path:
            self.dst_edit.setText(path)
