"""
Data-access layer for the backup orchestrator.

Wraps SQLite and provides typed query helpers for the GUI views.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class Client:
    uuid: str
    name: str
    hostname: Optional[str]
    ip_address: Optional[str]
    os: Optional[str]
    status: str
    last_seen_at: Optional[str]
    registered_at: str
    mqtt_username: Optional[str]
    notes: Optional[str]


@dataclass
class Schedule:
    id: int
    client_uuid: str
    profile: str
    src_dir: str
    dst_dir: str
    cron_expr: str
    enabled: bool
    created_at: str
    updated_at: str


@dataclass
class BackupHistoryEntry:
    id: int
    client_uuid: str
    profile: str
    started_at: str
    completed_at: Optional[str]
    status: str
    method: str
    archive_path: Optional[str]
    file_count: Optional[int]
    error_message: Optional[str]
    schedule_id: Optional[int]


class OrchestratorDatabase:
    """Thread-safe (read) database wrapper for the orchestrator."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _conn(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # -- Schema -------------------------------------------------------------------

    def _ensure_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS clients (
                    uuid          TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    hostname      TEXT,
                    ip_address    TEXT,
                    os            TEXT,
                    status        TEXT NOT NULL DEFAULT 'unknown',
                    last_seen_at  TEXT,
                    registered_at TEXT NOT NULL,
                    mqtt_username TEXT,
                    notes         TEXT
                );

                CREATE TABLE IF NOT EXISTS schedules (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_uuid   TEXT NOT NULL,
                    profile       TEXT NOT NULL,
                    src_dir       TEXT NOT NULL,
                    dst_dir       TEXT NOT NULL,
                    cron_expr     TEXT NOT NULL,
                    enabled       INTEGER NOT NULL DEFAULT 1,
                    created_at    TEXT NOT NULL,
                    updated_at    TEXT NOT NULL,
                    FOREIGN KEY(client_uuid) REFERENCES clients(uuid)
                );

                CREATE TABLE IF NOT EXISTS backup_history (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_uuid   TEXT NOT NULL,
                    profile       TEXT NOT NULL,
                    started_at    TEXT NOT NULL,
                    completed_at  TEXT,
                    status        TEXT NOT NULL,
                    method        TEXT NOT NULL,
                    archive_path  TEXT,
                    file_count    INTEGER,
                    error_message TEXT,
                    schedule_id   INTEGER,
                    FOREIGN KEY(client_uuid) REFERENCES clients(uuid),
                    FOREIGN KEY(schedule_id) REFERENCES schedules(id)
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    # -- Clients ------------------------------------------------------------------

    def get_clients(self) -> List[Client]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM clients ORDER BY name"
            ).fetchall()
            return [self._row_to_client(r) for r in rows]

    def get_client(self, uuid: str) -> Optional[Client]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE uuid = ?", (uuid,)
            ).fetchone()
            return self._row_to_client(row) if row else None

    def add_client(
        self,
        uuid: str,
        name: str,
        hostname: Optional[str] = None,
        ip_address: Optional[str] = None,
        os: Optional[str] = None,
        mqtt_username: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        now = _utcnow()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO clients (uuid, name, hostname, ip_address, os,
                   status, registered_at, mqtt_username, notes)
                   VALUES (?, ?, ?, ?, ?, 'unknown', ?, ?, ?)""",
                (uuid, name, hostname, ip_address, os, now, mqtt_username, notes),
            )
        return uuid

    def update_client(self, uuid: str, **kwargs) -> None:
        if not kwargs:
            return
        allowed = {"name", "hostname", "ip_address", "os", "status",
                    "last_seen_at", "mqtt_username", "notes"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [uuid]
        with self._conn() as conn:
            conn.execute(
                f"UPDATE clients SET {set_clause} WHERE uuid = ?", values
            )

    def remove_client(self, uuid: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM backup_history WHERE client_uuid = ?", (uuid,))
            conn.execute("DELETE FROM schedules WHERE client_uuid = ?", (uuid,))
            conn.execute("DELETE FROM clients WHERE uuid = ?", (uuid,))

    # -- Schedules ----------------------------------------------------------------

    def get_schedules(self, client_uuid: Optional[str] = None) -> List[Schedule]:
        with self._conn() as conn:
            if client_uuid:
                rows = conn.execute(
                    "SELECT * FROM schedules WHERE client_uuid = ? ORDER BY id",
                    (client_uuid,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM schedules ORDER BY client_uuid, id"
                ).fetchall()
            return [self._row_to_schedule(r) for r in rows]

    def add_schedule(
        self,
        client_uuid: str,
        profile: str,
        src_dir: str,
        dst_dir: str,
        cron_expr: str,
    ) -> int:
        now = _utcnow()
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO schedules (client_uuid, profile, src_dir, dst_dir,
                   cron_expr, enabled, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (client_uuid, profile, src_dir, dst_dir, cron_expr, now, now),
            )
            return cursor.lastrowid

    def update_schedule(self, schedule_id: int, **kwargs) -> None:
        if not kwargs:
            return
        allowed = {"profile", "src_dir", "dst_dir", "cron_expr", "enabled"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        fields["updated_at"] = _utcnow()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [schedule_id]
        with self._conn() as conn:
            conn.execute(
                f"UPDATE schedules SET {set_clause} WHERE id = ?", values
            )

    def remove_schedule(self, schedule_id: int) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    # -- Backup History -----------------------------------------------------------

    def get_backup_history(
        self,
        client_uuid: Optional[str] = None,
        limit: int = 100,
    ) -> List[BackupHistoryEntry]:
        with self._conn() as conn:
            if client_uuid:
                rows = conn.execute(
                    "SELECT * FROM backup_history WHERE client_uuid = ? "
                    "ORDER BY started_at DESC LIMIT ?",
                    (client_uuid, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM backup_history ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_history(r) for r in rows]

    def add_backup_history(
        self,
        client_uuid: str,
        profile: str,
        started_at: str,
        status: str,
        method: str,
        completed_at: Optional[str] = None,
        archive_path: Optional[str] = None,
        file_count: Optional[int] = None,
        error_message: Optional[str] = None,
        schedule_id: Optional[int] = None,
    ) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO backup_history (client_uuid, profile, started_at,
                   completed_at, status, method, archive_path, file_count,
                   error_message, schedule_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (client_uuid, profile, started_at, completed_at, status, method,
                 archive_path, file_count, error_message, schedule_id),
            )
            return cursor.lastrowid

    def update_backup_history(self, history_id: int, **kwargs) -> None:
        if not kwargs:
            return
        allowed = {"completed_at", "status", "archive_path", "file_count", "error_message"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [history_id]
        with self._conn() as conn:
            conn.execute(
                f"UPDATE backup_history SET {set_clause} WHERE id = ?", values
            )

    # -- Settings -----------------------------------------------------------------

    def get_setting(self, key: str, default: str = "") -> str:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO app_settings (key, value, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP""",
                (key, value, value),
            )

    # -- Row mappers --------------------------------------------------------------

    @staticmethod
    def _row_to_client(row: sqlite3.Row) -> Client:
        return Client(
            uuid=row["uuid"],
            name=row["name"],
            hostname=row["hostname"],
            ip_address=row["ip_address"],
            os=row["os"],
            status=row["status"],
            last_seen_at=row["last_seen_at"],
            registered_at=row["registered_at"],
            mqtt_username=row["mqtt_username"],
            notes=row["notes"],
        )

    @staticmethod
    def _row_to_schedule(row: sqlite3.Row) -> Schedule:
        return Schedule(
            id=row["id"],
            client_uuid=row["client_uuid"],
            profile=row["profile"],
            src_dir=row["src_dir"],
            dst_dir=row["dst_dir"],
            cron_expr=row["cron_expr"],
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_history(row: sqlite3.Row) -> BackupHistoryEntry:
        return BackupHistoryEntry(
            id=row["id"],
            client_uuid=row["client_uuid"],
            profile=row["profile"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            status=row["status"],
            method=row["method"],
            archive_path=row["archive_path"],
            file_count=row["file_count"],
            error_message=row["error_message"],
            schedule_id=row["schedule_id"],
        )


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
