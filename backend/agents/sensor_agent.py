"""Sensor Agent: handles environmental and motion sensor events.

This module ingests sensor-specific event types and delegates to log_agent.
"""
from core.models import LogEvent
from agents.log_agent import ingest_event


def ingest_sensor_event(
    sensor_type: str,
    location: str,
    device_id: str,
    value: float | None = None,
) -> LogEvent:
    """Convert a raw sensor reading into a LogEvent and add it to the buffer."""
    EVENT_TYPE_MAP = {
        "motion": "MOTION_ALARM",
        "glass_break": "GLASS_BREAK",
        "door_contact": "DOOR_PROPPED",
        "smoke": "FIRE_ALARM",
        "temperature": "FIRE_ALARM",  # high-temperature reading treated as potential fire
    }
    event = LogEvent(
        event_type=EVENT_TYPE_MAP.get(sensor_type.lower(), sensor_type.upper()),
        location=location,
        device_id=device_id,
        details={"sensor_type": sensor_type, "value": value},
    )
    ingest_event(event)
    return event
