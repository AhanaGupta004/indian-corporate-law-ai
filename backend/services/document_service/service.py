import logging
import os
import re
from pathlib import Path
from fastapi import HTTPException, status

from shared.config.settings import get_settings
from shared.database.document_repo import DocumentRepository
from shared.storage.provider import get_storage_provider

logger = logging.getLogger(__name__)


async def process_file_upload(user_id: str, username: str, filename: str, content: bytes) -> dict:
    settings = get_settings()
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"File type '{ext}' not allowed. Accepted: {settings.ALLOWED_EXTENSIONS}")
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit")

    storage = get_storage_provider()
    filepath = await storage.save_document(user_id, username, filename, content)
    logger.info(f"💾  Saved upload: {filepath} ({len(content):,} bytes)")

    doc = await DocumentRepository.create_document(user_id, filename, filepath)
    return {
        "doc_id":     str(doc["_id"]),
        "filename":   doc["filename"],
        "filepath":   doc["filepath"],
        "status":     doc["status"],
        "created_at": doc["created_at"].isoformat(),
    }


async def list_user_documents(user_id: str) -> list[dict]:
    docs = await DocumentRepository.get_user_documents(user_id)
    return [
        {
            "doc_id":     str(d["_id"]),
            "filename":   d["filename"],
            "status":     d["status"],
            "created_at": d["created_at"].isoformat(),
        }
        for d in docs
    ]


async def get_document_info(user_id: str, doc_id: str) -> dict:
    doc = await DocumentRepository.get_document(doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    return {
        "doc_id":     str(doc["_id"]),
        "filename":   doc["filename"],
        "status":     doc["status"],
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc.get("updated_at", doc["created_at"]).isoformat(),
    }
