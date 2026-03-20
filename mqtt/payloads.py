"""
JSON payload schemas for MQTT messages.

All payloads share a common envelope:
{
    "version": 1,
    "type": "<message_type>",
    "timestamp": "ISO8601",
    "payload": { ... }
}
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = 1


# -- Envelope -----------------------------------------------------------------

@dataclass
class Envelope:
    version: int
    type: str
    timestamp: str
    payload: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str | bytes) -> "Envelope":
        d = json.loads(data)
        return cls(
            version=d["version"],
            type=d["type"],
            timestamp=d["timestamp"],
            payload=d["payload"],
        )


def wrap(msg_type: str, payload: Dict[str, Any]) -> str:
    """Wrap a payload dict in the standard envelope and return JSON."""
    env = Envelope(
        version=SCHEMA_VERSION,
        type=msg_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=payload,
    )
    return env.to_json()


def unwrap(data: str | bytes) -> Envelope:
    """Parse a JSON message into an Envelope."""
    return Envelope.from_json(data)


# -- Registration -------------------------------------------------------------

@dataclass
class RegistrationRequest:
    client_uuid: str
    hostname: str
    ip_address: str
    os: str
    go_backup_version: str

    def to_mqtt(self) -> str:
        return wrap("register_request", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "RegistrationRequest":
        return cls(**payload)


@dataclass
class RegistrationResponse:
    approved: bool
    mqtt_username: str = ""
    mqtt_password: str = ""
    client_name: str = ""

    def to_mqtt(self) -> str:
        return wrap("register_response", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "RegistrationResponse":
        return cls(**payload)


# -- Heartbeat ----------------------------------------------------------------

@dataclass
class Heartbeat:
    status: str = "idle"           # idle / backing_up / offline
    uptime_seconds: int = 0
    active_backup: Optional[str] = None  # profile name if backing up

    def to_mqtt(self) -> str:
        return wrap("heartbeat", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "Heartbeat":
        return cls(**payload)


# -- Backup Command -----------------------------------------------------------

@dataclass
class BackupCommandConfig:
    src_dir: str
    dst_dir: str
    profile: str
    password: str = ""
    password_hint: str = ""
    description: str = ""
    workers: int = 4
    blocklist: List[str] = field(default_factory=list)


@dataclass
class BackupCommand:
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = "start_backup"
    config: Optional[Dict[str, Any]] = None

    def to_mqtt(self) -> str:
        return wrap("backup_command", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "BackupCommand":
        return cls(**payload)


# -- Backup Status ------------------------------------------------------------

@dataclass
class BackupStatus:
    command_id: Optional[str] = None   # None for manual/scheduled
    status: str = "success"            # success / failure / in_progress / cancelled
    method: str = "orchestrator"       # orchestrator / manual / scheduled
    profile: str = ""
    started_at: str = ""
    completed_at: Optional[str] = None
    archive_path: Optional[str] = None
    file_count: Optional[int] = None
    error_message: Optional[str] = None

    def to_mqtt(self) -> str:
        return wrap("backup_status", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "BackupStatus":
        return cls(**payload)


# -- Schedule Sync ------------------------------------------------------------

@dataclass
class ScheduleEntry:
    id: int
    profile: str
    src_dir: str
    dst_dir: str
    cron_expr: str
    enabled: bool
    password_hint: str = ""


@dataclass
class ScheduleSync:
    schedules: List[Dict[str, Any]] = field(default_factory=list)

    def to_mqtt(self) -> str:
        return wrap("schedule_sync", asdict(self))

    @classmethod
    def from_payload(cls, payload: dict) -> "ScheduleSync":
        return cls(**payload)
