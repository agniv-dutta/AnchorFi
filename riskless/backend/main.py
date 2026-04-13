from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.models.db import init_db
from backend.routers.compare import router as compare_router
from backend.routers.assess import router as assess_router
from backend.routers.health import router as health_router
from backend.routers.history import router as history_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(assess_router, prefix="/api", tags=["assess"])
    app.include_router(compare_router, prefix="/api", tags=["compare"])
    app.include_router(history_router, prefix="/api", tags=["history"])

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()

    return app


app = create_app()

