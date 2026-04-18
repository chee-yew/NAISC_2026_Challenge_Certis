"""Vision Agent, analyses CCTV/webcam frames for active security threats."""
import logging
from typing import Optional

import anthropic

from core.config import settings
from core.models import VisionAssessment, SeverityLevel
from agents.utils import parse_llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a security camera analysis AI for a commercial building security operations centre.
Analyse CCTV frames and identify ACTIVE security threats only (reactive mode — no predictions).

Threat types to detect:
- PHYSICAL_ALTERCATION: Fight, assault, or physical confrontation
- UNAUTHORIZED_ACCESS: Person in restricted area or bypassing access control
- UNATTENDED_ITEM: Bag or package left unattended in a public area
- MEDICAL_EMERGENCY: Person collapsed, seizing, or in clear medical distress
- FALLEN_PERSON: Person on the ground, possibly injured or unconscious
- SUSPICIOUS_BEHAVIOR: Person acting in a highly threatening or erratic manner
- CROWD_INCIDENT: Rapid crowd formation, stampede, or mass disturbance

Respond ONLY with valid JSON (no markdown fences):
{
  "threat_detected": <bool>,
  "threat_type": <string or null>,
  "confidence": <0.0–1.0>,
  "description": "<1–2 sentences>",
  "evidence": ["<observation 1>", "..."],
  "severity": <"critical"|"high"|"medium"|"low"|null>,
  "location": "<location in frame, e.g. near entrance, or null>"
}

Severity guide:
- critical: Immediate danger to life (weapons, unconscious person, fire)
- high: Serious threat requiring urgent response (active fight, forced entry)
- medium: Threat requiring response within minutes (suspicious item, restricted area)
- low: Minor anomaly warranting monitoring

Do not flag normal activity. Be accurate. When in doubt, do not alert."""




async def analyze_frame(frame_b64: str, camera_id: str) -> VisionAssessment:
    """Send a base64-encoded JPEG frame to Claude vision and return a threat assessment."""
    if "," in frame_b64:
        frame_b64 = frame_b64.split(",", 1)[1]

    user_text = f"Camera: {camera_id}. Is there an active security threat in this frame?"

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        message = await client.messages.create(
            model=settings.claude_model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": frame_b64}},
                    {"type": "text", "text": user_text},
                ],
            }],
        )
        result = parse_llm_json(message.content[0].text)
        return VisionAssessment(**result)
    except Exception as exc:
        logger.error("Vision agent error: %s", exc)
        return VisionAssessment(
            threat_detected=False, confidence=0.0,
            description=f"Vision agent error: {exc}"
        )
