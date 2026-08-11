"""
document_service/main.py — Standalone FastAPI app for document management
Runs independently on port 8002
"""
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

from shared.config.settings import get_settings
from shared.database.mongo import DatabaseManager
from services.document_service.router import router


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%H:%M:%S')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root.addHandler(ch)

setup_logging()
logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Document Service starting...")
    await DatabaseManager.connect_db()
    yield
    await DatabaseManager.close_db()
    logger.info("🛑 Document Service shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="LegalBuddy — Document Service", version=settings.APP_VERSION, lifespan=lifespan)

    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(RequestIDMiddleware)
    app.include_router(router)

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "document_service"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
