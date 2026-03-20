"""
Dashboard view -- client status overview and recent backup activity.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from gui.theme import (
    NAVY, BG_MAIN, BG_CARD, CARD_STYLE, TABLE_STYLE, BORDER,
    POSITIVE, NEGATIVE, WARNING, TEXT_PRIMARY, TEXT_SECONDARY,
    font_heading, font_body,
)
from gui.widgets.stat_card import StatCard
from gui.widgets.status_indicator import StatusIndicator


class DashboardView(QWidget):
    """Main dashboard showing client overview and recent activity."""

    def __init__(self, db, mqtt_worker=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.mqtt_worker = mqtt_worker
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

        # -- Header
        header_row = QHBoxLayout()
        header = QLabel("Dashboard")
        header.setFont(font_heading(20))
        header.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        header_row.addWidget(header)
        from gui.widgets.help_window import make_help_button
        header_row.addWidget(make_help_button("Dashboard", self))
        header_row.addStretch()
        layout.addLayout(header_row)

        # -- Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_clients = StatCard("Total Clients", "0")
        self.card_active = StatCard("Active Backups", "0")
        self.card_24h = StatCard("Last 24h", "0 / 0")
        self.card_next = StatCard("Next Scheduled", "--")

        for card in (self.card_clients, self.card_active, self.card_24h, self.card_next):
            cards_row.addWidget(card)

        layout.addLayout(cards_row)

        # -- Client status section
        section_label = QLabel("Client Status")
        section_label.setFont(font_heading(14))
        section_label.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        layout.addWidget(section_label)

        self.clients_container = QVBoxLayout()
        self.clients_container.setSpacing(8)
        self._placeholder_label = QLabel("No clients registered yet.")
        self._placeholder_label.setFont(font_body(10))
        self._placeholder_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; padding: 20px;"
        )
        self._placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clients_container.addWidget(self._placeholder_label)
        layout.addLayout(self.clients_container)

        # -- Recent activity section
        activity_label = QLabel("Recent Activity")
        activity_label.setFont(font_heading(14))
        activity_label.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        layout.addWidget(activity_label)

        self.activity_table = QTableWidget(0, 6)
        self.activity_table.setHorizontalHeaderLabels(
            ["Time", "Client", "Profile", "Status", "Method", "Files"]
        )
        self.activity_table.setStyleSheet(TABLE_STYLE)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.verticalHeader().setVisible(False)
        h = self.activity_table.horizontalHeader()
        h.setStretchLastSection(True)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.activity_table.setColumnWidth(0, 140)
        self.activity_table.setColumnWidth(2, 100)
        self.activity_table.setColumnWidth(3, 90)
        self.activity_table.setColumnWidth(4, 100)
        self.activity_table.setColumnWidth(5, 70)
        self.activity_table.setMinimumHeight(250)

        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_card.setStyleSheet(CARD_STYLE)
        ac_layout = QVBoxLayout(activity_card)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        ac_layout.addWidget(self.activity_table)
        layout.addWidget(activity_card)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        """Reload data from database and update all widgets."""
        self._refresh_stat_cards()
        self._refresh_client_status()
        self._refresh_activity_table()

    def _refresh_stat_cards(self):
        clients = self.db.get_clients()
        online = sum(1 for c in clients if c.status == "online")
        self.card_clients.set_value(f"{online} / {len(clients)}")
        self.card_clients.set_label("Clients Online")

        active = sum(1 for c in clients if c.status == "backing_up")
        self.card_active.set_value(str(active))

        history = self.db.get_backup_history(limit=100)
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = [h for h in history if h.started_at and h.started_at >= cutoff.isoformat()]
        successes = sum(1 for h in recent if h.status == "success")
        failures = sum(1 for h in recent if h.status == "failure")
        self.card_24h.set_value(f"{successes} / {failures}")
        self.card_24h.set_label("Success / Fail (24h)")

    def _refresh_client_status(self):
        # Clear existing client cards (except placeholder)
        while self.clients_container.count() > 0:
            item = self.clients_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        clients = self.db.get_clients()
        if not clients:
            self._placeholder_label = QLabel("No clients registered yet.")
            self._placeholder_label.setFont(font_body(10))
            self._placeholder_label.setStyleSheet(
                f"color: {TEXT_SECONDARY}; background: transparent; border: none; padding: 20px;"
            )
            self._placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.clients_container.addWidget(self._placeholder_label)
            return

        row = QHBoxLayout()
        row.setSpacing(12)
        for i, client in enumerate(clients):
            card = self._make_client_card(client)
            row.addWidget(card)
            if (i + 1) % 4 == 0:
                self.clients_container.addLayout(row)
                row = QHBoxLayout()
                row.setSpacing(12)
        if row.count() > 0:
            row.addStretch()
            self.clients_container.addLayout(row)

    def _make_client_card(self, client) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(CARD_STYLE)
        card.setMinimumWidth(200)
        card.setMaximumWidth(300)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Name + status row
        top_row = QHBoxLayout()
        name = QLabel(client.name)
        name.setFont(font_heading(12))
        name.setStyleSheet(f"color: {NAVY}; background: transparent; border: none;")
        dot = StatusIndicator(client.status, size=10)
        top_row.addWidget(name)
        top_row.addStretch()
        top_row.addWidget(dot)
        layout.addLayout(top_row)

        # Details
        details = []
        if client.hostname:
            details.append(f"Host: {client.hostname}")
        if client.ip_address:
            details.append(f"IP: {client.ip_address}")
        if client.last_seen_at:
            details.append(f"Seen: {client.last_seen_at[:16]}")

        for d in details:
            lbl = QLabel(d)
            lbl.setFont(font_body(9))
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; border: none;")
            layout.addWidget(lbl)

        return card

    def _refresh_activity_table(self):
        history = self.db.get_backup_history(limit=10)
        self.activity_table.setRowCount(len(history))

        STATUS_COLORS = {
            "success": POSITIVE, "failure": NEGATIVE,
            "in_progress": WARNING, "cancelled": TEXT_SECONDARY,
        }

        for row, entry in enumerate(history):
            # Look up client name
            clients = self.db.get_clients()
            client_name = entry.client_uuid[:8]
            for c in clients:
                if c.uuid == entry.client_uuid:
                    client_name = c.name
                    break

            items = [
                entry.started_at[:16] if entry.started_at else "--",
                client_name,
                entry.profile,
                entry.status,
                entry.method,
                str(entry.file_count or "--"),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 3:  # status column
                    color = STATUS_COLORS.get(entry.status, TEXT_SECONDARY)
                    item.setForeground(QTableWidgetItem(text).foreground())
                    from PySide6.QtGui import QColor as QC
                    item.setForeground(QC(color))
                self.activity_table.setItem(row, col, item)
