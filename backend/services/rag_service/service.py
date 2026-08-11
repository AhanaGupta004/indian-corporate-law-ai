import logging
from shared.providers.llm import OllamaProvider
from shared.providers.embedding import SentenceTransformerProvider
from shared.providers.vector_store import FAISSVectorStore, LocalFAISSVectorStore
from shared.config.settings import get_settings
from services.rag_service.analysis.prompts import build_prompt, _classify_document, _parse_response
from services.rag_service.extraction import extract_text

logger = logging.getLogger(__name__)

_llm_provider = None
_embedding_provider = None
_global_vector_store = None

def get_llm_provider():
    global _llm_provider
    if not _llm_provider:
        _llm_provider = OllamaProvider()
    return _llm_provider

def get_embedding_provider():
    global _embedding_provider
    if not _embedding_provider:
        _embedding_provider = SentenceTransformerProvider()
    return _embedding_provider

def get_global_vector_store():
    global _global_vector_store
    if not _global_vector_store:
        settings = get_settings()
        _global_vector_store = FAISSVectorStore(settings.FAISS_INDEX_PATH, settings.FAISS_METADATA_PATH)
        _global_vector_store.load()
    return _global_vector_store

def chunk_text(text: str, size: int = 500, overlap: int = 100) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text] if text.strip() else []
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return chunks

def build_law_context(distances, indices, metadata, max_chars: int = 1500) -> str:
    if indices is None or len(indices) == 0 or (hasattr(indices, 'size') and indices.size == 0):
        return ""
    parts = []
    budget = max_chars
    if hasattr(distances, 'flatten'): distances = distances.flatten()
    if hasattr(indices, 'flatten'): indices = indices.flatten()
    for dist, idx in zip(distances, indices):
        r = metadata(int(idx))
        if not r: continue
        header = f"[{r.get('section_number','?')}] {r.get('section_title','')}"
        body   = r.get("content", "")[:600]
        chunk  = f"{header}\n{body}"
        if len(chunk) > budget:
            chunk = chunk[:budget]
        parts.append(chunk)
        budget -= len(chunk)
        if budget <= 0:
            break
    return "\n\n---\n\n".join(parts)

def _local_context(text: str, top_k: int = 4, max_chars: int = 2500) -> str:
    settings = get_settings()
    try:
        chunks = chunk_text(text, size=settings.CHUNK_SIZE_WORDS, overlap=settings.CHUNK_OVERLAP_WORDS)
        if not chunks:
            return text[:max_chars]
        embed_provider = get_embedding_provider()
        vecs = embed_provider.encode(chunks)
        d = vecs.shape[1]
        local_store = LocalFAISSVectorStore(d)
        local_store.add(vecs)
        query = (
            "legal clauses obligations duties liabilities compliance "
            "payment termination representations warranties indemnity "
            "breach penalty dispute jurisdiction governing law"
        )
        q_vec = embed_provider.encode([query])
        _, idxs = local_store.search(q_vec, min(top_k, len(chunks)))
        selected = [chunks[i] for i in idxs if 0 <= i < len(chunks)]
        if chunks[0] not in selected:
            selected = [chunks[0]] + selected[:top_k-1]
        ctx = "\n\n---\n\n".join(selected)[:max_chars]
        logger.info(f"[LOCAL] {len(selected)} chunks selected, {len(ctx)} chars")
        return ctx
    except Exception as exc:
        logger.error(f"[FAIL] Local FAISS error: {exc}", exc_info=True)
        return text[:max_chars]


async def run_analysis(filepath: str, filename: str, progress_callback=None) -> dict:
    """Full RAG pipeline orchestration."""
    async def _notify(status: str):
        if progress_callback:
            await progress_callback(status)

    settings = get_settings()

    await _notify("EXTRACTING")
    text = extract_text(filepath, filename)
    if not text or not text.strip():
        return {"error": "Document contains no extractable text"}

    logger.info(f"[DOC] {len(text):,} chars | {len(text.split()):,} words")
    doc_type = _classify_document(text)
    logger.info(f"[TYPE] Document classified as: {doc_type}")

    logger.info("[STEP 1/4] Building local document context...")
    await _notify("CHUNKING")
    local_ctx = _local_context(text, top_k=settings.TOP_K_LOCAL, max_chars=settings.CONTEXT_MAX_CHARS)

    logger.info("[STEP 2/4] Searching Companies Act knowledge base...")
    await _notify("EMBEDDING")
    law_query = (local_ctx[:400] or text[:400])
    global_store = get_global_vector_store()
    embed_provider = get_embedding_provider()
    law_vec = embed_provider.encode([law_query])
    distances, indices = global_store.search(law_vec, settings.TOP_K_GLOBAL)
    law_ctx = build_law_context(distances, indices, global_store.get_metadata, max_chars=1500)
    logger.info(f"[LAW] Retrieved {len(indices)} sections, {len(law_ctx)} chars")

    await _notify("INDEXING")
    logger.info("[STEP 3/4] Building analysis prompt...")
    prompt = build_prompt(doc_full=text[:3000], local_context=local_ctx, law_context=law_ctx, doc_type=doc_type)

    await _notify("ANALYZING")
    logger.info("[STEP 4/4] Calling LLM...")
    llm = get_llm_provider()
    raw = await llm.generate(prompt, timeout=settings.OLLAMA_TIMEOUT)

    if raw is None:
        return {"error": "LLM timed out or returned empty response"}

    result = _parse_response(raw, doc_type)
    return result
