from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.internal import router as internal_router
from app.api.websocket import router as websocket_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.system.broadcaster import start_broadcasters
from app.tools import register_all_tools
from app.voice.orchestrator import voice_orchestrator

setup_logging()
logger = get_logger("main")


async def _start_voice() -> None:
    try:
        await voice_orchestrator.start()
    except Exception as exc:  # noqa: BLE001 - no mic / model load failure shouldn't crash the backend
        logger.error("VOICE PIPELINE UNAVAILABLE: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all_tools()
    broadcaster_tasks = start_broadcasters()
    voice_task = asyncio.create_task(_start_voice())
    logger.info("FRIDAY BACKEND STARTED")
    yield
    voice_task.cancel()
    await voice_orchestrator.stop()
    for task in broadcaster_tasks:
        task.cancel()
    logger.info("FRIDAY BACKEND STOPPED")


app = FastAPI(title="FRIDAY", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)
app.include_router(internal_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "friday-backend"}


def run() -> None:
    import uvicorn

    uvicorn.run(app, host=settings.friday_host, port=settings.friday_port, log_level="warning")


if __name__ == "__main__":
    run()
