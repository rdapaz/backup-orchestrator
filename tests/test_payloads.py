"""Tests for MQTT payload serialization."""

import json
import pytest
from mqtt.payloads import (
    wrap, unwrap, Envelope,
    RegistrationRequest, RegistrationResponse,
    Heartbeat, BackupCommand, BackupStatus, ScheduleSync,
    SCHEMA_VERSION,
)


class TestEnvelope:
    def test_wrap_unwrap_round_trip(self):
        payload = {"key": "value", "num": 42}
        encoded = wrap("test_type", payload)
        env = unwrap(encoded)

        assert env.version == SCHEMA_VERSION
        assert env.type == "test_type"
        assert env.payload == payload
        assert env.timestamp  # non-empty

    def test_from_bytes(self):
        encoded = wrap("test", {"a": 1})
        env = unwrap(encoded.encode("utf-8"))
        assert env.type == "test"


class TestRegistration:
    def test_request_round_trip(self):
        req = RegistrationRequest(
            client_uuid="uuid-123",
            hostname="WS1",
            ip_address="192.168.1.10",
            os="windows/amd64",
            go_backup_version="1.0.0",
        )
        encoded = req.to_mqtt()
        env = unwrap(encoded)
        assert env.type == "register_request"
        decoded = RegistrationRequest.from_payload(env.payload)
        assert decoded.client_uuid == "uuid-123"
        assert decoded.hostname == "WS1"

    def test_response_round_trip(self):
        resp = RegistrationResponse(
            approved=True,
            mqtt_username="client_abc",
            mqtt_password="secret",
            client_name="Workstation ABC",
        )
        encoded = resp.to_mqtt()
        env = unwrap(encoded)
        assert env.type == "register_response"
        decoded = RegistrationResponse.from_payload(env.payload)
        assert decoded.approved is True
        assert decoded.mqtt_password == "secret"


class TestHeartbeat:
    def test_round_trip(self):
        hb = Heartbeat(status="idle", uptime_seconds=3600)
        encoded = hb.to_mqtt()
        env = unwrap(encoded)
        decoded = Heartbeat.from_payload(env.payload)
        assert decoded.status == "idle"
        assert decoded.uptime_seconds == 3600


class TestBackupCommand:
    def test_round_trip(self):
        cmd = BackupCommand(
            action="start_backup",
            config={
                "src_dir": r"C:\Users",
                "dst_dir": r"D:\Backups",
                "profile": "documents",
                "workers": 4,
            },
        )
        encoded = cmd.to_mqtt()
        env = unwrap(encoded)
        decoded = BackupCommand.from_payload(env.payload)
        assert decoded.action == "start_backup"
        assert decoded.config["profile"] == "documents"
        assert decoded.command_id  # auto-generated


class TestBackupStatus:
    def test_round_trip(self):
        status = BackupStatus(
            status="success",
            method="orchestrator",
            profile="documents",
            started_at="2026-03-21T10:00:00Z",
            completed_at="2026-03-21T10:05:00Z",
            file_count=1523,
        )
        encoded = status.to_mqtt()
        env = unwrap(encoded)
        decoded = BackupStatus.from_payload(env.payload)
        assert decoded.status == "success"
        assert decoded.file_count == 1523


class TestScheduleSync:
    def test_round_trip(self):
        sync = ScheduleSync(schedules=[
            {"id": 1, "profile": "documents", "src_dir": "/a", "dst_dir": "/b",
             "cron_expr": "0 2 * * *", "enabled": True},
            {"id": 2, "profile": "photos", "src_dir": "/c", "dst_dir": "/d",
             "cron_expr": "0 * * * *", "enabled": False},
        ])
        encoded = sync.to_mqtt()
        env = unwrap(encoded)
        decoded = ScheduleSync.from_payload(env.payload)
        assert len(decoded.schedules) == 2
        assert decoded.schedules[0]["profile"] == "documents"
