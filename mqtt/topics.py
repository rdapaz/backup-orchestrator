"""
MQTT topic hierarchy for orchestrator <-> agent communication.
"""

# Root prefix for all backup orchestrator topics
PREFIX = "backup"

# Client registration
REGISTRATION_REQUEST = f"{PREFIX}/registration/request"

def registration_response(client_uuid: str) -> str:
    return f"{PREFIX}/registration/response/{client_uuid}"

# Heartbeat (client -> orchestrator)
def heartbeat(client_uuid: str) -> str:
    return f"{PREFIX}/heartbeat/{client_uuid}"

HEARTBEAT_WILDCARD = f"{PREFIX}/heartbeat/+"

# Commands (orchestrator -> client)
def command(client_uuid: str) -> str:
    return f"{PREFIX}/command/{client_uuid}"

# Status reports (client -> orchestrator)
def status(client_uuid: str) -> str:
    return f"{PREFIX}/status/{client_uuid}"

STATUS_WILDCARD = f"{PREFIX}/status/+"

# Schedule sync (orchestrator -> client)
def schedules(client_uuid: str) -> str:
    return f"{PREFIX}/schedules/{client_uuid}"
