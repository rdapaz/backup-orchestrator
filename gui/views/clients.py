"""
Clients view -- manage registered backup agents.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QMessageBox,
)
from gui.theme import (
    NAVY, BG_MAIN, CARD_STYLE, TABLE_STYLE, BORDER,
    BUTTON_STYLE, BUTTON_DANGER_STYLE, INPUT_STYLE, COMBO_STYLE,
    POSITIVE, NEGATIVE, WARNING, TEXT_PRIMARY, TEXT_SECONDARY,
    font_heading, font_body,
)
from gui.widgets.status_indicator import StatusIndicator


class AddClientDialog(QDialog):
    """Dialog for manually adding a client."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Client")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(INPUT_STYLE)
        self.name_edit.setPlaceholderText("e.g. Workstation 01")
        layout.addRow("Name:", self.name_edit)

        self.hostname_edit = QLineEdit()
        self.hostname_edit.setStyleSheet(INPUT_STYLE)
        self.hostname_edit.setPlaceholderText("e.g. DESKTOP-ABC123")
        layout.addRow("Hostname:", self.hostname_edit)

        self.ip_edit = QLineEdit()
        self.ip_edit.setStyleSheet(INPUT_STYLE)
        self.ip_edit.setPlaceholderText("e.g. 192.168.1.50")
        layout.addRow("IP Address:", self.ip_edit)

        self.os_edit = QLineEdit()
        self.os_edit.setStyleSheet(INPUT_STYLE)
        self.os_edit.setPlaceholderText("e.g. windows/amd64")
        layout.addRow("OS:", self.os_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes...")
        layout.addRow("Notes:", self.notes_edit)

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

        save_btn = QPushButton("Add Client")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        layout.addRow(btn_row)


class ClientsView(QWidget):
    """Client management view with table and CRUD actions."""

    def __init__(self, db, mqtt_worker=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.mqtt_worker = mqtt_worker
        self.setStyleSheet(f"background: {BG_MAIN};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- Header row
        header_row = QHBoxLayout()
        header = QLabel("Clients")
        header.setFont(font_heading(20))
        header.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        header_row.addWidget(header)
        header_row.addStretch()

        self.add_btn = QPushButton("Add Client")
        self.add_btn.setStyleSheet(BUTTON_STYLE)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add_client)
        header_row.addWidget(self.add_btn)

        layout.addLayout(header_row)

        # -- Filter row
        filter_card = QFrame()
        filter_card.setObjectName("card")
        filter_card.setStyleSheet(CARD_STYLE)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 8, 16, 8)

        self.status_filter = QComboBox()
        self.status_filter.setStyleSheet(COMBO_STYLE)
        self.status_filter.addItems(["All Status", "Online", "Offline", "Backing Up", "Unknown"])
        self.status_filter.currentIndexChanged.connect(lambda: self.refresh())
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # -- Client table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet(CARD_STYLE)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Hostname", "IP Address", "OS", "Status", "Last Seen", "UUID"]
        )
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 140)
        self.table.setColumnWidth(6, 100)

        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, stretch=1)

    def refresh(self):
        """Reload clients from database."""
        clients = self.db.get_clients()

        # Apply filter
        status_map = {1: "online", 2: "offline", 3: "backing_up", 4: "unknown"}
        filter_idx = self.status_filter.currentIndex()
        if filter_idx > 0:
            target_status = status_map.get(filter_idx, "")
            clients = [c for c in clients if c.status == target_status]

        self.table.setRowCount(len(clients))

        STATUS_COLORS = {
            "online": POSITIVE, "offline": NEGATIVE,
            "backing_up": WARNING, "unknown": TEXT_SECONDARY,
        }

        for row, client in enumerate(clients):
            items = [
                client.name,
                client.hostname or "--",
                client.ip_address or "--",
                client.os or "--",
                client.status,
                client.last_seen_at[:16] if client.last_seen_at else "--",
                client.uuid[:8] + "...",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 4:  # status
                    item.setForeground(QColor(STATUS_COLORS.get(client.status, TEXT_SECONDARY)))
                self.table.setItem(row, col, item)

    def _on_add_client(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation", "Client name is required.")
                return

            import uuid
            self.db.add_client(
                uuid=str(uuid.uuid4()),
                name=name,
                hostname=dialog.hostname_edit.text().strip() or None,
                ip_address=dialog.ip_edit.text().strip() or None,
                os=dialog.os_edit.text().strip() or None,
                notes=dialog.notes_edit.toPlainText().strip() or None,
            )
            self.refresh()
