"""
Encrypted credential store using Argon2id + AES-256-GCM.

Manages backup passwords and MQTT credentials, encrypted at rest.
The master password is never stored -- only a derived key is held
in memory while the application is running.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


# Argon2id parameters
_ARGON2_MEMORY = 65536   # 64 MB
_ARGON2_TIME = 3         # iterations
_ARGON2_PARALLELISM = 4
_ARGON2_KEY_LENGTH = 32  # AES-256
_SALT_LENGTH = 32
_NONCE_LENGTH = 12       # AES-GCM standard nonce


class CredentialStore:
    """Encrypted credential vault backed by SQLite."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._key: Optional[bytes] = None
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
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

    def _ensure_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS store_meta (
                    key   TEXT PRIMARY KEY,
                    value BLOB NOT NULL
                );

                CREATE TABLE IF NOT EXISTS credentials (
                    id         TEXT PRIMARY KEY,
                    enc_value  BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    # -- Public API ---------------------------------------------------------------

    def is_new(self) -> bool:
        """True if no master password has been set yet."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM store_meta WHERE key = 'salt'"
            ).fetchone()
            return row is None

    def is_unlocked(self) -> bool:
        return self._key is not None

    def unlock(self, master_password: str) -> bool:
        """
        Derive the encryption key from the master password.

        On first call (no salt stored), creates the salt and stores a
        verification token. On subsequent calls, verifies the password
        against the stored token.

        Returns True if unlock succeeded.
        """
        with self._conn() as conn:
            salt_row = conn.execute(
                "SELECT value FROM store_meta WHERE key = 'salt'"
            ).fetchone()

            if salt_row is None:
                # First time -- create salt and verification token
                salt = os.urandom(_SALT_LENGTH)
                key = self._derive_key(master_password, salt)

                # Store salt
                conn.execute(
                    "INSERT INTO store_meta (key, value) VALUES ('salt', ?)",
                    (salt,),
                )

                # Store encrypted verification token
                verify_token = self._encrypt(key, b"BACKUP_ORCHESTRATOR_VERIFY")
                conn.execute(
                    "INSERT INTO store_meta (key, value) VALUES ('verify', ?)",
                    (verify_token,),
                )

                self._key = key
                return True
            else:
                # Existing store -- verify password
                salt = salt_row["value"]
                key = self._derive_key(master_password, salt)

                verify_row = conn.execute(
                    "SELECT value FROM store_meta WHERE key = 'verify'"
                ).fetchone()

                if verify_row is None:
                    return False

                try:
                    decrypted = self._decrypt(key, verify_row["value"])
                    if decrypted == b"BACKUP_ORCHESTRATOR_VERIFY":
                        self._key = key
                        return True
                except Exception:
                    pass

                return False

    def lock(self):
        """Clear the derived key from memory."""
        self._key = None

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Re-encrypt all credentials with a new master password.

        Returns True on success, False if old password is wrong.
        """
        with self._conn() as conn:
            salt_row = conn.execute(
                "SELECT value FROM store_meta WHERE key = 'salt'"
            ).fetchone()
            if salt_row is None:
                return False

            old_salt = salt_row["value"]
            old_key = self._derive_key(old_password, old_salt)

            # Verify old password
            verify_row = conn.execute(
                "SELECT value FROM store_meta WHERE key = 'verify'"
            ).fetchone()
            try:
                decrypted = self._decrypt(old_key, verify_row["value"])
                if decrypted != b"BACKUP_ORCHESTRATOR_VERIFY":
                    return False
            except Exception:
                return False

            # Generate new salt and key
            new_salt = os.urandom(_SALT_LENGTH)
            new_key = self._derive_key(new_password, new_salt)

            # Re-encrypt all credentials
            rows = conn.execute("SELECT id, enc_value FROM credentials").fetchall()
            for row in rows:
                plaintext = self._decrypt(old_key, row["enc_value"])
                new_enc = self._encrypt(new_key, plaintext)
                conn.execute(
                    "UPDATE credentials SET enc_value = ?, updated_at = ? WHERE id = ?",
                    (new_enc, _utcnow(), row["id"]),
                )

            # Update salt and verification token
            conn.execute(
                "UPDATE store_meta SET value = ? WHERE key = 'salt'",
                (new_salt,),
            )
            new_verify = self._encrypt(new_key, b"BACKUP_ORCHESTRATOR_VERIFY")
            conn.execute(
                "UPDATE store_meta SET value = ? WHERE key = 'verify'",
                (new_verify,),
            )

            self._key = new_key
            return True

    def store(self, key: str, plaintext: str) -> None:
        """Encrypt and store a credential."""
        if not self._key:
            raise RuntimeError("Credential store is locked")

        enc = self._encrypt(self._key, plaintext.encode("utf-8"))
        now = _utcnow()

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO credentials (id, enc_value, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET enc_value = ?, updated_at = ?""",
                (key, enc, now, now, enc, now),
            )

    def retrieve(self, key: str) -> Optional[str]:
        """Decrypt and return a credential, or None if not found."""
        if not self._key:
            raise RuntimeError("Credential store is locked")

        with self._conn() as conn:
            row = conn.execute(
                "SELECT enc_value FROM credentials WHERE id = ?", (key,)
            ).fetchone()

            if row is None:
                return None

            plaintext = self._decrypt(self._key, row["enc_value"])
            return plaintext.decode("utf-8")

    def delete(self, key: str) -> None:
        """Remove a credential."""
        with self._conn() as conn:
            conn.execute("DELETE FROM credentials WHERE id = ?", (key,))

    def list_keys(self) -> List[str]:
        """Return all credential keys."""
        with self._conn() as conn:
            rows = conn.execute("SELECT id FROM credentials ORDER BY id").fetchall()
            return [row["id"] for row in rows]

    # -- Cryptographic helpers ----------------------------------------------------

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = Argon2id(
            salt=salt,
            length=_ARGON2_KEY_LENGTH,
            iterations=_ARGON2_TIME,
            lanes=_ARGON2_PARALLELISM,
            memory_cost=_ARGON2_MEMORY,
        )
        return kdf.derive(password.encode("utf-8"))

    @staticmethod
    def _encrypt(key: bytes, plaintext: bytes) -> bytes:
        """Encrypt with AES-256-GCM. Returns nonce + ciphertext."""
        nonce = os.urandom(_NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    @staticmethod
    def _decrypt(key: bytes, data: bytes) -> bytes:
        """Decrypt AES-256-GCM. Expects nonce + ciphertext."""
        nonce = data[:_NONCE_LENGTH]
        ciphertext = data[_NONCE_LENGTH:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
