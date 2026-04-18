"""Camera router"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.config import settings
from core.connections import manager
from core.feedback import save_alert
from agents.graph import run_pipeline

router = APIRouter(tags=["camera"])
logger = logging.getLogger(__name__)



@dataclass
class CameraState:
    last_analysis: float = 0.0
    last_alert_category: Optional[str] = None
    last_alert_time: float = 0.0


_camera_state: dict[str, CameraState] = {}


@router.websocket("/ws/camera")
async def camera_websocket(websocket: WebSocket):
    """
    Client → Server: {"type": "frame", "camera_id": "webcam_1", "data": "<base64 JPEG>"}
    Server → Client: {"type": "ack"} | {"type": "alert", "data": <Alert JSON>}
    """
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") != "frame":
                continue

            camera_id: str = msg.get("camera_id", "webcam_1")
            frame_b64: str = msg.get("data", "")

            now = time.time()
            state = _camera_state.setdefault(camera_id, CameraState())

            if now - state.last_analysis < settings.frame_analysis_interval:
                await websocket.send_json({"type": "ack"})
                continue

            state.last_analysis = now
            logger.debug("Analysing frame from %s", camera_id)

            alert = await run_pipeline(
                frame_b64=frame_b64,
                camera_id=camera_id,
            )

            if alert:
                # Suppress if same threat category was alerted within the cooldown window
                same_category = alert.category == state.last_alert_category
                within_cooldown = (now - state.last_alert_time) < settings.alert_cooldown

                if same_category and within_cooldown:
                    logger.debug(
                        "Suppressed duplicate alert '%s' for %s (cooldown: %.0fs remaining)",
                        alert.category, camera_id, settings.alert_cooldown - (now - state.last_alert_time),
                    )
                    await websocket.send_json({"type": "ack"})
                    continue

                state.last_alert_category = alert.category
                state.last_alert_time = now

                alert.camera_id = camera_id
                alert.frame_snapshot = frame_b64
                await save_alert(alert)
                payload = {"type": "alert", "data": alert.model_dump(mode="json")}
                await websocket.send_json(payload)
                await manager.broadcast(payload)
            else:
                # Threat resolved, clear the cooldown so it re-alerts immediately if it returns
                if state.last_alert_category:
                    logger.debug("Threat resolved on %s, cooldown cleared.", camera_id)
                    state.last_alert_category = None
                    state.last_alert_time = 0.0
                await websocket.send_json({"type": "ack"})

    except WebSocketDisconnect:
        logger.info("Camera WebSocket disconnected: %s", websocket.client)
    except Exception as exc:
        logger.error("Camera WebSocket error: %s", exc)
