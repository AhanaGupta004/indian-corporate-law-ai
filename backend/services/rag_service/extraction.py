import logging
from pathlib import Path
import pdfplumber
import PyPDF2
import docx as python_docx

logger = logging.getLogger(__name__)

def extract_text(filepath: str, filename: str) -> str:
    """
    Extract plain text from PDF, DOCX, or TXT.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        try:
            with pdfplumber.open(filepath) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages)
            if text.strip():
                logger.info(f"📄  pdfplumber: {len(text):,} chars from {len(pages)} pages")
                return text
        except Exception as e:
            logger.warning(f"⚠️   pdfplumber failed ({e}), trying PyPDF2 …")

        with open(filepath, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            text = "".join(p.extract_text() or "" for p in reader.pages)
        logger.info(f"📄  PyPDF2: {len(text):,} chars")
        return text

    elif ext == ".docx":
        doc  = python_docx.Document(filepath)
        text = "\n".join(p.text for p in doc.paragraphs)
        logger.info(f"📄  DOCX: {len(text):,} chars")
        return text

    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        logger.info(f"📄  TXT: {len(text):,} chars")
        return text

    raise ValueError(f"Unsupported file type: {ext}")
