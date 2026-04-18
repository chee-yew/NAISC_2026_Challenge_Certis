# CERTIS — Predictive Agentic Security Advisor

Our submission for NAISC 2026. It's a security operations dashboard that uses Claude to analyse live camera feeds, audio, and access control logs to detect threats and surface recommended actions to on-site officers.

Three agents (vision, audio, log) run in parallel on incoming data. A coordinator agent synthesises their findings and raises an alert if confidence clears the threshold. Alerts hit the dashboard in real time over WebSocket.

## Tech Stack

- **Backend**: FastAPI + LangGraph + SQLite
- **AI**: Anthropic Claude (vision + text)
- **Frontend**: React + TypeScript + Tailwind CSS + Vite

## Getting Started

You'll need Python 3.10+, Node.js 18+, and an Anthropic API key.

**Backend**

```bash
cd backend

python -m venv venv
source venv/Scripts/activate      # Windows (bash)
# source venv/bin/activate         # macOS / Linux

pip install -r requirements.txt
uvicorn main:app --reload
```

Runs at `http://localhost:8000`. Swagger docs at `/docs`.

**Frontend**

Open a second terminal, then run:

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`.

## Environment Variables

Create a `backend/.env` before starting the backend:

```env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
DATABASE_URL=sqlite+aiosqlite:///./security.db
FRAME_ANALYSIS_INTERVAL=3
ALERT_COOLDOWN=30
```

| Variable | What it does | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | required |
| `CLAUDE_MODEL` | Which Claude model to use | `claude-sonnet-4-6` |
| `DATABASE_URL` | Database connection string | SQLite local file |
| `FRAME_ANALYSIS_INTERVAL` | Only analyse every Nth camera frame | `3` |
| `ALERT_COOLDOWN` | Seconds before the same alert type can fire again | `30` |

## How It Works

```
Camera (WebSocket) ──► Vision Agent ──┐
Audio  (REST)      ──► Audio Agent  ──┼──► Coordinator ──► Alert ──► WebSocket broadcast
Logs   (REST)      ──► Log Agent   ──┘
```

The **Vision Agent** checks CCTV frames for physical threats. The **Audio Agent** handles intercom/microphone transcripts. The **Log Agent** applies rules to access control and alarm events — no LLM, just rules. The **Coordinator** takes all three and decides whether to raise an alert and what officers should do next.

Alerts only fire if confidence is ≥ 0.65. If the Claude API goes down, the coordinator falls back to rule-based logic.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/alerts` | Get stored alerts |
| POST | `/api/audio` | Send a transcript for analysis |
| POST | `/api/logs/event` | Send an access control / alarm event |
| POST | `/api/feedback` | Officer confirms or dismisses an alert |
| WebSocket | `/api/ws/alerts` | Real-time alert stream |
| WebSocket | `/ws/camera` | Camera frame ingestion |

## Project Structure

```
├── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── vision_agent.py
│   │   ├── audio_agent.py
│   │   ├── log_agent.py
│   │   └── coordinator.py
│   ├── core/
│   │   ├── config.py
│   │   └── models.py
│   ├── routers/
│   └── graph.py
└── frontend/
    └── src/
        ├── components/
        └── hooks/
```

## Notes

- Microphone transcription only works on Chrome or Edge (Web Speech API limitation)
- The demo panel lets you simulate events (fire alarm, forced entry, panic button, etc.) without real hardware
- Webcam access is required for the camera feed
