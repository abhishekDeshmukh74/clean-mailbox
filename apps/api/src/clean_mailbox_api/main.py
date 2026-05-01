from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.google_oauth import router as auth_router
from .config import get_settings
from .routes.agents import router as agents_router
from .routes.emails import router as emails_router
from .routes.me import router as me_router
from .routes.settings import router as settings_router

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Clean Mailbox API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(emails_router)
    app.include_router(agents_router)
    app.include_router(settings_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
