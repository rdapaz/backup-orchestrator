"""Tests for OrchestratorDatabase."""

import os
import tempfile
import pytest
from gui.models.database import OrchestratorDatabase


@pytest.fixture
def db(tmp_path):
    return OrchestratorDatabase(tmp_path / "test.db")


class TestClients:
    def test_add_and_get(self, db):
        db.add_client(uuid="test-uuid-1", name="Workstation 1", hostname="WS1", ip_address="192.168.1.10")
        clients = db.get_clients()
        assert len(clients) == 1
        assert clients[0].uuid == "test-uuid-1"
        assert clients[0].name == "Workstation 1"
        assert clients[0].hostname == "WS1"
        assert clients[0].status == "unknown"

    def test_get_single(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        client = db.get_client("uuid-1")
        assert client is not None
        assert client.name == "WS1"

        assert db.get_client("nonexistent") is None

    def test_update(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        db.update_client("uuid-1", status="online", ip_address="10.0.0.1")
        client = db.get_client("uuid-1")
        assert client.status == "online"
        assert client.ip_address == "10.0.0.1"

    def test_remove(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        db.remove_client("uuid-1")
        assert db.get_clients() == []

    def test_remove_cascades(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        db.add_schedule(client_uuid="uuid-1", profile="documents", src_dir="/src", dst_dir="/dst", cron_expr="0 2 * * *")
        db.add_backup_history(client_uuid="uuid-1", profile="documents", started_at="2026-01-01T00:00:00Z", status="success", method="manual")
        db.remove_client("uuid-1")
        assert db.get_schedules() == []
        assert db.get_backup_history() == []


class TestSchedules:
    def test_add_and_get(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        sid = db.add_schedule(
            client_uuid="uuid-1", profile="documents",
            src_dir=r"C:\Users", dst_dir=r"D:\Backups",
            cron_expr="0 2 * * *",
        )
        assert sid > 0
        schedules = db.get_schedules()
        assert len(schedules) == 1
        assert schedules[0].profile == "documents"
        assert schedules[0].enabled is True

    def test_filter_by_client(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        db.add_client(uuid="uuid-2", name="WS2")
        db.add_schedule(client_uuid="uuid-1", profile="documents", src_dir="/a", dst_dir="/b", cron_expr="0 * * * *")
        db.add_schedule(client_uuid="uuid-2", profile="photos", src_dir="/c", dst_dir="/d", cron_expr="0 * * * *")

        s1 = db.get_schedules(client_uuid="uuid-1")
        assert len(s1) == 1
        assert s1[0].profile == "documents"

    def test_update(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        sid = db.add_schedule(client_uuid="uuid-1", profile="all", src_dir="/a", dst_dir="/b", cron_expr="0 * * * *")
        db.update_schedule(sid, enabled=False, cron_expr="0 2 * * *")
        s = db.get_schedules()[0]
        assert s.enabled is False
        assert s.cron_expr == "0 2 * * *"

    def test_remove(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        sid = db.add_schedule(client_uuid="uuid-1", profile="all", src_dir="/a", dst_dir="/b", cron_expr="0 * * * *")
        db.remove_schedule(sid)
        assert db.get_schedules() == []


class TestBackupHistory:
    def test_add_and_get(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        hid = db.add_backup_history(
            client_uuid="uuid-1", profile="documents",
            started_at="2026-03-21T10:00:00Z",
            status="success", method="orchestrator",
            file_count=100,
        )
        assert hid > 0
        history = db.get_backup_history()
        assert len(history) == 1
        assert history[0].file_count == 100
        assert history[0].status == "success"

    def test_update(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        hid = db.add_backup_history(
            client_uuid="uuid-1", profile="documents",
            started_at="2026-03-21T10:00:00Z",
            status="in_progress", method="orchestrator",
        )
        db.update_backup_history(hid, status="success", completed_at="2026-03-21T10:05:00Z", file_count=50)
        h = db.get_backup_history()[0]
        assert h.status == "success"
        assert h.file_count == 50

    def test_filter_by_client(self, db):
        db.add_client(uuid="uuid-1", name="WS1")
        db.add_client(uuid="uuid-2", name="WS2")
        db.add_backup_history(client_uuid="uuid-1", profile="a", started_at="2026-01-01", status="success", method="manual")
        db.add_backup_history(client_uuid="uuid-2", profile="b", started_at="2026-01-02", status="success", method="manual")
        h1 = db.get_backup_history(client_uuid="uuid-1")
        assert len(h1) == 1


class TestSettings:
    def test_get_default(self, db):
        assert db.get_setting("nonexistent", "fallback") == "fallback"

    def test_set_and_get(self, db):
        db.set_setting("broker_host", "10.0.0.1")
        assert db.get_setting("broker_host") == "10.0.0.1"

    def test_upsert(self, db):
        db.set_setting("key", "value1")
        db.set_setting("key", "value2")
        assert db.get_setting("key") == "value2"
