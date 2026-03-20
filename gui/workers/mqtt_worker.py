"""
MQTT worker thread -- runs paho-mqtt client loop in a QThread.

Emits Qt signals so the main thread can safely update the UI.
"""

import json
import logging
from typing import Optional

from PySide6.QtCore import QThread, Signal

import paho.mqtt.client as mqtt

from mqtt import topics
from mqtt.payloads import (
    wrap, unwrap, BackupCommand, BackupCommandConfig, ScheduleSync,
    RegistrationResponse, SCHEMA_VERSION,
)

log = logging.getLogger(__name__)


class MqttWorker(QThread):
    """Background MQTT client thread."""

    # Signals emitted to the main thread
    client_registered = Signal(dict)         # registration request payload
    heartbeat_received = Signal(str, dict)   # (client_uuid, heartbeat payload)
    backup_status_received = Signal(str, dict)  # (client_uuid, status payload)
    connection_changed = Signal(bool)        # connected / disconnected

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: str = "",
        password: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._username = username
        self._password = password
        self._client: Optional[mqtt.Client] = None
        self._running = False

    def run(self):
        """Start the MQTT client loop (blocking)."""
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        if self._username:
            self._client.username_pw_set(self._username, self._password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(self._broker_host, self._broker_port, keepalive=30)
        except Exception as e:
            log.error("MQTT connect failed: %s", e)
            self.connection_changed.emit(False)
            return

        self._running = True
        self._client.loop_forever()

    def stop(self):
        """Disconnect and stop the loop."""
        self._running = False
        if self._client:
            self._client.disconnect()

    def update_config(self, host: str, port: int, username: str, password: str):
        """Update broker connection parameters (requires restart)."""
        self._broker_host = host
        self._broker_port = port
        self._username = username
        self._password = password

    # -- MQTT callbacks -----------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            log.info("Connected to MQTT broker")
            self.connection_changed.emit(True)

            # Subscribe to orchestrator topics
            client.subscribe(topics.REGISTRATION_REQUEST, qos=1)
            client.subscribe(topics.HEARTBEAT_WILDCARD, qos=0)
            client.subscribe(topics.STATUS_WILDCARD, qos=1)
        else:
            log.error("MQTT connect failed: reason_code=%s", reason_code)
            self.connection_changed.emit(False)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        log.info("Disconnected from MQTT broker (reason=%s)", reason_code)
        self.connection_changed.emit(False)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        try:
            envelope = unwrap(msg.payload)
        except Exception as e:
            log.warning("Failed to parse MQTT message on %s: %s", msg.topic, e)
            return

        if envelope.version > SCHEMA_VERSION:
            log.warning("Ignoring message with version %d (we support %d)",
                       envelope.version, SCHEMA_VERSION)
            return

        msg_type = envelope.type

        if msg_type == "register_request":
            self.client_registered.emit(envelope.payload)

        elif msg_type == "heartbeat":
            # Extract client UUID from topic: backup/heartbeat/{uuid}
            parts = msg.topic.split("/")
            if len(parts) >= 3:
                client_uuid = parts[2]
                self.heartbeat_received.emit(client_uuid, envelope.payload)

        elif msg_type == "backup_status":
            parts = msg.topic.split("/")
            if len(parts) >= 3:
                client_uuid = parts[2]
                self.backup_status_received.emit(client_uuid, envelope.payload)

    # -- Publish methods ----------------------------------------------------------

    def publish_command(self, client_uuid: str, command_payload: dict) -> None:
        """Send a backup command to a specific client."""
        if not self._client:
            return

        cmd = BackupCommand(
            action=command_payload.get("action", "start_backup"),
            config=command_payload.get("config"),
        )
        topic = topics.command(client_uuid)
        self._client.publish(topic, cmd.to_mqtt(), qos=1)

    def publish_schedule_sync(self, client_uuid: str, schedule_list: list) -> None:
        """Push current schedules to a client."""
        if not self._client:
            return

        sync = ScheduleSync(schedules=schedule_list)
        topic = topics.schedules(client_uuid)
        self._client.publish(topic, sync.to_mqtt(), qos=1, retain=True)

    def publish_registration_response(
        self, client_uuid: str, response: RegistrationResponse
    ) -> None:
        """Send registration approval/denial to a client."""
        if not self._client:
            return

        topic = topics.registration_response(client_uuid)
        self._client.publish(topic, response.to_mqtt(), qos=1)
