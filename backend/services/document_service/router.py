from typing import Optional
import logging
import os
import mimetypes
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, File, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from shared.security.jwt import extract_user_from_token
from shared.database.user_repo import UserRepository
from shared.database.document_repo import DocumentRepository
from shared.storage.provider import get_storage_provider
from services.document_service import service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

def _auth(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return extract_user_from_token(authorization.removeprefix("Bearer "))


async def _handle_upload(file: UploadFile, authorization: Optional[str]) -> dict:
    user_id = _auth(authorization)
    user = await UserRepository.find_user_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    limit = 5
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_count = user.get("daily_doc_count", 0)
    last_reset = user.get("last_reset_date")

    if last_reset != current_date:
        current_count = 0

    if current_count >= limit:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Daily limit of {limit} documents reached.")

    active_statuses = ["QUEUED", "PROCESSING", "EXTRACTING", "CHUNKING", "EMBEDDING", "INDEXING", "ANALYZING"]
    collection = DocumentRepository.get_collection()
    from bson.objectid import ObjectId
    active_count = await collection.count_documents({
        "user_id": ObjectId(user_id),
        "status": {"$in": active_statuses}
    })
    if active_count > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "You already have a document processing. Please wait for it to finish or cancel it.")

    await UserRepository.increment_daily_doc_count(user_id, current_date)
    content = await file.read()
    username = user["email"].split("@")[0]
    doc = await service.process_file_upload(user_id, username, file.filename, content)
    logger.info(f"📤  Upload: {file.filename} → doc_id={doc['doc_id']}")
    return {
        "success":  True,
        "doc_id":   doc["doc_id"],
        "filename": doc["filename"],
        "status":   doc["status"],
        "message":  "File uploaded. Call POST /summarize/{doc_id} to analyse.",
    }


@router.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Upload a legal document (PDF / DOCX / TXT)."""
    return await _handle_upload(file, authorization)


@router.get("/api/documents")
async def list_documents(authorization: Optional[str] = Header(None)):
    """List all documents belonging to the authenticated user."""
    user_id = _auth(authorization)
    docs = await service.list_user_documents(user_id)
    return {"documents": docs}


@router.post("/api/documents/reset-stuck")
async def reset_stuck_documents(authorization: Optional[str] = Header(None)):
    user_id = _auth(authorization)
    from bson.objectid import ObjectId
    active_statuses = ["QUEUED", "PROCESSING", "EXTRACTING", "CHUNKING", "EMBEDDING", "INDEXING", "ANALYZING"]
    collection = DocumentRepository.get_collection()
    result = await collection.update_many(
        {"user_id": ObjectId(user_id), "status": {"$in": active_statuses}},
        {"$set": {"status": "FAILED", "updated_at": datetime.now(timezone.utc)}},
    )
    count = result.modified_count
    return {"success": True, "reset_count": count, "message": f"Marked {count} stuck document(s) as failed."}


@router.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, authorization: Optional[str] = Header(None)):
    """Get document metadata by ID."""
    user_id = _auth(authorization)
    return await service.get_document_info(user_id, doc_id)


@router.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, authorization: Optional[str] = Header(None)):
    """Permanently delete a document and its file from disk."""
    user_id = _auth(authorization)
    doc = await DocumentRepository.get_document(doc_id)
    if not doc or str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot delete this document")
    filepath = doc.get("filepath", "")
    storage = get_storage_provider()
    await storage.delete_document(filepath)
    await DocumentRepository.delete_document(doc_id)
    return {"success": True, "message": "Document deleted"}


@router.get("/api/documents/{doc_id}/file")
async def serve_document_file(doc_id: str, authorization: Optional[str] = Header(None)):
    user_id = _auth(authorization)
    doc = await DocumentRepository.get_document(doc_id)
    if not doc or str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    filepath = doc.get("filepath", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found on disk")
    filename = doc.get("filename", "document")
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or "application/octet-stream"
    return FileResponse(path=filepath, media_type=mime, filename=filename,
                        headers={"Content-Disposition": f'inline; filename="{filename}"'})
