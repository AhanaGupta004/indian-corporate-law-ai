import logging
import asyncio
from shared.database.document_repo import DocumentRepository
from services.rag_service.service import run_analysis

logger = logging.getLogger(__name__)


def process_document_task(user_id: str, doc_id: str, filepath: str, filename: str):
    """Synchronous wrapper for potential Celery/RQ use."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(_async_process_document(user_id, doc_id, filepath, filename))


async def _async_process_document(user_id: str, doc_id: str, filepath: str, filename: str):
    logger.info("=" * 70)
    logger.info(f"[START] Analysis started — doc_id={doc_id}")
    logger.info("=" * 70)

    try:
        doc = await DocumentRepository.get_document(doc_id)
        if doc:
            current_status = doc.get("status", "")
            if current_status in ["COMPLETED", "FAILED"] or current_status not in ["UPLOADED", "QUEUED"]:
                if current_status != "QUEUED":
                    logger.warning(f"[SKIP] Document {doc_id} is in state {current_status}. Skipping.")
                    return

        await DocumentRepository.update_document_status(doc_id, "PROCESSING")

        async def _update_status(status_str: str):
            curr = await DocumentRepository.get_document(doc_id)
            if curr and curr.get("status") == "CANCELLED":
                raise asyncio.CancelledError("Analysis was cancelled by user")
            await DocumentRepository.update_document_status(doc_id, status_str)

        result = await run_analysis(filepath, filename, progress_callback=_update_status)

        if result.get("error") and not result.get("summary"):
            raise ValueError(f"LLM pipeline failed: {result['error']}")

        await DocumentRepository.store_document_result(doc_id, result)

        logger.info("=" * 70)
        logger.info(f"[OK] Analysis complete — doc_id={doc_id}")
        logger.info("=" * 70)

    except asyncio.CancelledError as exc:
        logger.info("=" * 70)
        logger.warning(f"[CANCELLED] Analysis cancelled — doc_id={doc_id}: {exc}")
        logger.info("=" * 70)

    except Exception as exc:
        logger.error("=" * 70)
        logger.error(f"[FAIL] Analysis failed — doc_id={doc_id}: {exc}", exc_info=True)
        logger.error("=" * 70)
        try:
            await DocumentRepository.update_document_status(doc_id, "FAILED")
        except Exception as db_exc:
            logger.critical(f"[CRITICAL] Could not update status for {doc_id}: {db_exc}", exc_info=True)
