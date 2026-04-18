"""Alerts router"""
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.connections import manager
from core.feedback import list_alerts, update_alert_status, save_feedback
from core.models import AlertFeedback

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
async def get_alerts(limit: int = Query(50, le=200), status: Optional[str] = None):
    alerts = await list_alerts(limit=limit, status=status)
    return [a.model_dump(mode="json") for a in alerts]


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """
    Real-time alert channel.

    Server → Client: {"type": "alert", "data": <Alert JSON>}
    Client → Server: {"type": "feedback", "data": {"alert_id": "...", "outcome": "confirmed"|"dismissed", "officer_note": "..."}}
    """
    await manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "feedback":
                fb = AlertFeedback(**msg["data"])
                await update_alert_status(fb.alert_id, fb.outcome)
                await save_feedback(fb.alert_id, fb.outcome, fb.officer_note)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
