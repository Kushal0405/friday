# FRIDAY

An original, voice-first desktop AI assistant for Windows. FRIDAY listens for its wake word ("**Friday**"), transcribes speech locally, decides whether a request needs a tool or a direct answer, executes real actions on your machine, and speaks the result back — all visualized in a custom-built HUD.

This is a from-scratch build with no reused JARVIS/FRIDAY code or movie UI assets. The visual language, architecture, and code are original.

## Status

Under active incremental development. See `CLAUDE.md`-adjacent plan history for phase progress. Phase 1 (Electron + React + Python + WebSocket skeleton) is implemented; voice, tools, and the full HUD are being built out phase by phase.

## Architecture

```
Electron (React HUD + main process)
        │  WebSocket (ws://127.0.0.1:8765/ws/friday)
        ▼
Python backend (FastAPI)
        │
   ┌────┼─────────┬──────────┐
   ▼    ▼         ▼          ▼
 Voice  AI      Tools     Tasks/Events
 (STT/  (LLM,   (Apps,    (state machine,
  TTS,  tool-   Browser,  event bus →
  wake  calling) Files,   WebSocket)
  word)          System,
                 Volume…)
```

The frontend never touches the OS directly. Every action — opening an app, taking a screenshot, changing volume — goes through the Python backend's registered Tool system. The AI cannot execute arbitrary shell commands.

## Requirements

- Windows 10/11
- Python 3.11+ (developed against 3.13.1)
- Node.js 18+ (developed against v23.9.0)
- [Ollama](https://ollama.com) running locally with a pulled model (default: `llama3.1`) — or any OpenAI-compatible endpoint
- A working microphone for voice features

## Installation

```powershell
# Backend
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# edit .env if you want to point at a different AI provider

# Frontend
cd ../frontend
npm install
```

## Environment configuration

`backend/.env` (copy from `.env.example`):

```env
AI_API_KEY=
AI_MODEL=llama3.1
AI_BASE_URL=http://localhost:11434/v1

WHISPER_MODEL=small

FRIDAY_HOST=127.0.0.1
FRIDAY_PORT=8765

WAKE_WORD=friday
```

`AI_BASE_URL` defaults to a local Ollama server so FRIDAY works with zero API cost. Point it at OpenAI or any OpenAI-compatible endpoint by changing `AI_BASE_URL`/`AI_API_KEY`/`AI_MODEL` — no code changes required.

`.env` is git-ignored and never read by the Electron renderer; secrets stay backend-side.

## Running in development

**Backend:**
```powershell
cd backend
venv\Scripts\python -m app.main
```
Verify with `curl http://127.0.0.1:8765/health`.

**Frontend (Electron + Vite dev server):**
```powershell
cd frontend
npm run dev
```

**Both together:** double-click `scripts/start-friday.bat` (verifies Python/Node, starts the backend, waits for `/health`, then launches the HUD; stops the backend when the HUD closes).

## Production build

```powershell
cd frontend
npm run package
```
Produces `frontend/release/FRIDAY Setup.exe` via electron-builder (NSIS installer).

## Supported commands (growing each phase)

- "What time is it?"
- "Open Chrome" / "Open VS Code" / "Close Chrome"
- "Search Google for React 19" / "Open YouTube" / "Open GitHub"
- "Take a screenshot"
- "Open Downloads" / "Open Documents"
- "What's my CPU usage?"
- "Increase volume" / "Mute" / "Set volume to 50%"
- "Play" / "Pause" / "Next"
- "What's in my clipboard?"

## Security model

- Electron: `contextIsolation: true`, `nodeIntegration: false`, all OS access mediated by a minimal `contextBridge` preload API.
- The renderer cannot execute shell commands. All tool execution happens in the Python backend behind a registered-tool allowlist with Pydantic-validated inputs.
- Destructive actions (shutdown, restart, delete, kill process) require explicit user confirmation before execution.
- Clipboard contents are only read on explicit user request — never automatically fed to the AI.
- API keys live only in `backend/.env`, never in the renderer or logs.

## Project structure

```
friday/
├── frontend/        Electron + React + TypeScript + Vite HUD
├── backend/         Python FastAPI backend (AI, voice, tools, tasks, events)
├── scripts/         start-friday.bat
└── README.md
```

## Troubleshooting

- **Backend won't start**: confirm `venv\Scripts\pip install -r requirements.txt` completed without errors; check the console log for the failing import.
- **HUD shows "RECONNECTING…" forever**: backend isn't running or `FRIDAY_PORT` mismatch between `backend/.env` and the frontend's Electron config.
- **AI responses fail**: confirm Ollama is running (`ollama serve`) and the model in `AI_MODEL` has been pulled (`ollama pull llama3.1`). Offline-capable tools (time, system stats, opening apps, screenshots, volume) still work without the AI.
