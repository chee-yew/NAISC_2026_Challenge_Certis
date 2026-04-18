"""Save, load, and update alerts in the database."""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update, desc

from core.models import Alert, AlertRecord, FeedbackRecord, get_session


async def save_alert(alert: Alert) -> None:
    async with get_session() as session:
        record = AlertRecord(
            alert_id=alert.alert_id,
            timestamp=alert.timestamp,
            severity=alert.severity.value,
            category=alert.category,
            title=alert.title,
            description=alert.description,
            evidence=alert.evidence,
            recommended_actions=alert.recommended_actions,
            contributing_agents=alert.contributing_agents,
            confidence=alert.confidence,
            location=alert.location,
            status=alert.status,
            camera_id=alert.camera_id,
            frame_snapshot=alert.frame_snapshot,
        )
        session.add(record)
        await session.commit()


async def list_alerts(limit: int = 50, status: Optional[str] = None) -> List[Alert]:
    async with get_session() as session:
        stmt = select(AlertRecord).order_by(desc(AlertRecord.timestamp)).limit(limit)
        if status:
            stmt = stmt.where(AlertRecord.status == status)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [_record_to_alert(r) for r in records]


async def update_alert_status(alert_id: str, status: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            update(AlertRecord)
            .where(AlertRecord.alert_id == alert_id)
            .values(status=status)
        )
        await session.commit()
        return result.rowcount > 0


async def save_feedback(alert_id: str, outcome: str, officer_note: Optional[str]) -> None:
    async with get_session() as session:
        record = FeedbackRecord(
            alert_id=alert_id,
            outcome=outcome,
            officer_note=officer_note,
            timestamp=datetime.utcnow(),
        )
        session.add(record)
        await session.commit()


def _record_to_alert(r: AlertRecord) -> Alert:
    from core.models import SeverityLevel
    return Alert(
        alert_id=r.alert_id,
        timestamp=r.timestamp,
        severity=SeverityLevel(r.severity),
        category=r.category,
        title=r.title,
        description=r.description,
        evidence=r.evidence or [],
        recommended_actions=r.recommended_actions or [],
        contributing_agents=r.contributing_agents or [],
        confidence=r.confidence,
        location=r.location,
        status=r.status,
        camera_id=r.camera_id,
        frame_snapshot=r.frame_snapshot,
    )
