"""
api_gateway/main.py — Public-facing reverse proxy on port 5000
Routes all external requests to the correct internal microservice.

Service Map:
  /api/auth/*          → auth_service      (port 8001)
  /api/documents/*     → document_service  (port 8002)
  /summarize/*         → rag_service       (port 8003)
  /result/*            → rag_service       (port 8003)
  /api/summarize/*     → rag_service       (port 8003)
  /health              → gateway itself
"""
import logging
import uuid
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger
from shared.config.settings import get_settings


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

# Internal service URLs (from env or defaults)
AUTH_SVC     = os.getenv("AUTH_SERVICE_URL",     "http://localhost:8001")
DOCUMENT_SVC = os.getenv("DOCUMENT_SERVICE_URL", "http://localhost:8002")
RAG_SVC      = os.getenv("RAG_SERVICE_URL",      "http://localhost:8003")


def _resolve_upstream(path: str) -> str:
    """Determine which upstream service to proxy the request to."""
    if path.startswith("/api/auth"):
        return AUTH_SVC
    if path.startswith("/api/documents"):
        return DOCUMENT_SVC
    if path.startswith("/summarize") or path.startswith("/result") or path.startswith("/api/summarize"):
        return RAG_SVC
    return None


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API Gateway starting...")
    app.state.http_client = httpx.AsyncClient(timeout=180.0)
    yield
    await app.state.http_client.aclose()
    logger.info("🛑 API Gateway shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="LegalBuddy — API Gateway", version=settings.APP_VERSION, lifespan=lifespan)

    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/health", tags=["infra"])
    async def health():
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "services": {
                "auth":     AUTH_SVC,
                "document": DOCUMENT_SVC,
                "rag":      RAG_SVC,
            }
        }

    @app.get("/ready", tags=["infra"])
    async def ready():
        return {"status": "ready"}

    @app.get("/", tags=["infra"])
    async def root():
        return {"message": "LegalBuddy API Gateway", "docs": "/docs"}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def proxy(request: Request, path: str):
        full_path = "/" + path
        upstream = _resolve_upstream(full_path)

        if not upstream:
            return Response(content='{"detail":"Not Found"}', status_code=404, media_type="application/json")

        target_url = upstream + full_path
        if request.url.query:
            target_url += "?" + request.url.query

        # Forward request body and headers (excluding host)
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

        logger.info(f"[PROXY] {request.method} {full_path} → {target_url}")

        client: httpx.AsyncClient = request.app.state.http_client
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
        )

        # Stream the upstream response back
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=dict(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type"),
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
