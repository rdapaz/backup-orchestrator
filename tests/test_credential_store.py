"""Tests for CredentialStore."""

import pytest
from gui.models.credential_store import CredentialStore


@pytest.fixture
def store(tmp_path):
    return CredentialStore(tmp_path / "creds.db")


class TestUnlock:
    def test_new_store(self, store):
        assert store.is_new() is True
        assert store.is_unlocked() is False

    def test_first_unlock_sets_password(self, store):
        assert store.unlock("master123") is True
        assert store.is_unlocked() is True
        assert store.is_new() is False

    def test_correct_password_unlocks(self, store):
        store.unlock("master123")
        store.lock()
        assert store.is_unlocked() is False
        assert store.unlock("master123") is True
        assert store.is_unlocked() is True

    def test_wrong_password_fails(self, store):
        store.unlock("master123")
        store.lock()
        assert store.unlock("wrong") is False
        assert store.is_unlocked() is False


class TestStoreRetrieve:
    def test_round_trip(self, store):
        store.unlock("pw")
        store.store("mqtt:client1", "secret-password")
        assert store.retrieve("mqtt:client1") == "secret-password"

    def test_missing_key(self, store):
        store.unlock("pw")
        assert store.retrieve("nonexistent") is None

    def test_overwrite(self, store):
        store.unlock("pw")
        store.store("key", "v1")
        store.store("key", "v2")
        assert store.retrieve("key") == "v2"

    def test_delete(self, store):
        store.unlock("pw")
        store.store("key", "val")
        store.delete("key")
        assert store.retrieve("key") is None

    def test_list_keys(self, store):
        store.unlock("pw")
        store.store("b", "1")
        store.store("a", "2")
        assert store.list_keys() == ["a", "b"]

    def test_locked_raises(self, store):
        with pytest.raises(RuntimeError):
            store.store("key", "val")
        with pytest.raises(RuntimeError):
            store.retrieve("key")


class TestChangePassword:
    def test_change_password(self, store):
        store.unlock("old")
        store.store("key1", "secret1")
        store.store("key2", "secret2")

        assert store.change_master_password("old", "new") is True

        # Lock and re-unlock with new password
        store.lock()
        assert store.unlock("old") is False
        assert store.unlock("new") is True

        # Verify data survived
        assert store.retrieve("key1") == "secret1"
        assert store.retrieve("key2") == "secret2"

    def test_wrong_old_password_fails(self, store):
        store.unlock("correct")
        assert store.change_master_password("wrong", "new") is False


class TestUnicodeAndEdgeCases:
    def test_unicode_credential(self, store):
        store.unlock("pw")
        store.store("key", "p@ssw0rd-with-emojis-and-unicode")
        assert store.retrieve("key") == "p@ssw0rd-with-emojis-and-unicode"

    def test_empty_string(self, store):
        store.unlock("pw")
        store.store("key", "")
        assert store.retrieve("key") == ""

    def test_long_credential(self, store):
        store.unlock("pw")
        long_val = "x" * 10000
        store.store("key", long_val)
        assert store.retrieve("key") == long_val
