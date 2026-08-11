import os
import sys
import pickle
import faiss
import argparse
from tqdm import tqdm

# Ensure we can import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.providers.embedding import SentenceTransformerProvider
from services.rag_service.extraction import extract_text

def chunk_text(text: str, chunk_size_words: int = 500, overlap_words: int = 100):
    words = text.split()
    chunks = []
    step = chunk_size_words - overlap_words
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size_words]
        chunk = " ".join(chunk_words)
        chunks.append({
            "chunk_id": len(chunks) + 1,
            "content": chunk,
            "word_count": len(chunk_words),
            "section_title": f"Chunk {len(chunks) + 1}"  # Basic fallback for title
        })
        if i + chunk_size_words >= len(words):
            break
    return chunks

def build_index(pdf_path: str):
    print(f"[INFO] Extracting text from {pdf_path}...")
    try:
        text = extract_text(pdf_path, os.path.basename(pdf_path))
    except Exception as e:
        print(f"[ERROR] Failed to extract text: {e}")
        return

    print(f"[INFO] Total text extracted: {len(text):,} characters.")
    
    chunks = chunk_text(text, chunk_size_words=500, overlap_words=100)
    print(f"[INFO] Split into {len(chunks)} chunks.")

    provider = SentenceTransformerProvider()
    
    embeddings = []
    batch_size = 32
    
    print("[INFO] Encoding chunks in batches...")
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch_texts = [c["content"] for c in chunks[i:i + batch_size]]
        batch_emb = provider.encode(batch_texts)
        embeddings.extend(batch_emb)
        
    import numpy as np
    embeddings_np = np.array(embeddings, dtype=np.float32)
    
    d = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    index_path = os.path.join(output_dir, "faiss_index.bin")
    meta_path = os.path.join(output_dir, "metadata.pkl")
    
    print(f"[INFO] Saving index with {index.ntotal} vectors to {index_path}...")
    faiss.write_index(index, index_path)
    
    print(f"[INFO] Saving metadata to {meta_path}...")
    with open(meta_path, "wb") as f:
        pickle.dump(chunks, f)
        
    print("[SUCCESS] Knowledge base built successfully from PDF!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=str, default="../act.pdf", help="Path to PDF")
    args = parser.parse_args()
    
    pdf_path = os.path.abspath(args.pdf)
    if not os.path.exists(pdf_path):
        print(f"[ERROR] Could not find PDF at {pdf_path}")
        sys.exit(1)
        
    build_index(pdf_path)
