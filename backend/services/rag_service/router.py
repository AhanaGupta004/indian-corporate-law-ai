from typing import Optional
import logging
import os
from fastapi import APIRouter, Header, HTTPException, status, BackgroundTasks
from shared.security.jwt import extract_user_from_token
from shared.database.user_repo import UserRepository
from shared.database.document_repo import DocumentRepository
from services.rag_service.ingestion_worker.tasks import _async_process_document

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])

def _auth(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return extract_user_from_token(authorization.removeprefix("Bearer "))


async def _trigger(doc_id: str, authorization: Optional[str], background_tasks: BackgroundTasks) -> dict:
    user_id = _auth(authorization)
    doc = await DocumentRepository.get_document(doc_id)
    if not doc or str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Document not found or access denied")

    filepath = doc.get("filepath", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found on disk")

    current_status = doc.get("status", "unknown")
    active_statuses = ["QUEUED", "PROCESSING", "EXTRACTING", "CHUNKING", "EMBEDDING", "INDEXING", "ANALYZING"]

    if current_status in active_statuses:
        return {"doc_id": doc_id, "status": current_status, "message": "Already processing"}

    if current_status == "COMPLETED" and doc.get("result"):
        return {"doc_id": doc_id, "status": "COMPLETED", "message": "Analysis already complete", **_format_result(doc["result"])}

    background_tasks.add_task(_async_process_document, user_id, doc_id, filepath, doc["filename"])
    await DocumentRepository.update_document_status(doc_id, "QUEUED")
    logger.info(f"[OK] doc_id={doc_id} -> QUEUED")
    return {"doc_id": doc_id, "status": "QUEUED", "message": "Analysis queued"}


@router.post("/summarize/{doc_id}")
async def trigger_analysis(doc_id: str, background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    """Trigger RAG analysis. Returns immediately; poll GET /result/{doc_id}."""
    return await _trigger(doc_id, authorization, background_tasks)


@router.post("/api/summarize/{doc_id}")
async def trigger_analysis_compat(doc_id: str, background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    return await _trigger(doc_id, authorization, background_tasks)


@router.get("/result/{doc_id}")
async def get_result(doc_id: str, authorization: Optional[str] = Header(None)):
    return await _result_response(doc_id, authorization)


@router.get("/summarize/{doc_id}")
async def get_result_compat(doc_id: str, authorization: Optional[str] = Header(None)):
    return await _result_response(doc_id, authorization)


@router.get("/api/summarize/{doc_id}")
async def get_result_api_compat(doc_id: str, authorization: Optional[str] = Header(None)):
    return await _result_response(doc_id, authorization)


@router.post("/api/documents/{doc_id}/cancel")
async def cancel_analysis(doc_id: str, authorization: Optional[str] = Header(None)):
    user_id = _auth(authorization)
    doc = await DocumentRepository.get_document(doc_id)
    if not doc or str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Document not found or access denied")

    current_status = doc.get("status", "unknown")
    active_statuses = ["QUEUED", "PROCESSING", "EXTRACTING", "CHUNKING", "EMBEDDING", "INDEXING", "ANALYZING"]

    if current_status in active_statuses:
        await DocumentRepository.update_document_status(doc_id, "CANCELLED")
        return {"success": True, "message": "Analysis cancelled successfully"}

    return {"success": False, "message": f"Document is not currently processing (status: {current_status})"}


async def _result_response(doc_id: str, authorization: Optional[str]) -> dict:
    user_id = _auth(authorization)
    doc = await DocumentRepository.get_document(doc_id)
    if not doc or str(doc["user_id"]) != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Document not found or access denied")

    doc_status = doc.get("status", "unknown")

    if doc_status == "COMPLETED":
        result = doc.get("result") or {}
        return {"doc_id": doc_id, "status": "COMPLETED", **_format_result(result)}

    if doc_status == "FAILED":
        return {"doc_id": doc_id, "status": "FAILED", "error": "Analysis failed. Re-upload the document and try again."}

    return {"doc_id": doc_id, "status": doc_status}


def _format_result(result: dict) -> dict:
    return {
        "summary":     result.get("summary", ""),
        "clauses":     result.get("clauses", []),
        "obligations": result.get("obligations", []),
        "risks":       result.get("risks", []),
        "risk_score":  result.get("risk_score", 0),
        "critical_risks": result.get("critical_risks", ""),
        "compliance":  result.get("compliance", ""),
    }
