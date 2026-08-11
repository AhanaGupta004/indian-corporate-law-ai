import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Server
        self.APP_NAME = "Legal AI RAG System"
        self.APP_VERSION = "4.0.0"
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", 5000))
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

        # MongoDB
        self.MONGODB_URL = (
            os.getenv("MONGODB_URL")
            or os.getenv("MONGODB_URI")
            or "mongodb://localhost:27017"
        )
        self.MONGODB_DB = os.getenv("MONGODB_DB", "legalbuddy")

        # JWT
        self.JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))

        # File Upload
        self.UPLOAD_BASE_DIR = "uploads"
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
        self.ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

        # Ollama LLM
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
        self.OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 120))

        # RAG / chunking
        self.CHUNK_SIZE_WORDS = int(os.getenv("CHUNK_SIZE_WORDS", 500))
        self.CHUNK_OVERLAP_WORDS = int(os.getenv("CHUNK_OVERLAP_WORDS", 100))
        self.TOP_K_GLOBAL = int(os.getenv("TOP_K_GLOBAL", 5))
        self.TOP_K_LOCAL = int(os.getenv("TOP_K_LOCAL", 3))
        self.CONTEXT_MAX_CHARS = int(os.getenv("CONTEXT_MAX_CHARS", 1500))

        # FAISS paths
        self.FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "output/faiss_index.bin")
        self.FAISS_METADATA_PATH = os.getenv("FAISS_METADATA_PATH", "output/metadata.pkl")

        # CORS
        self.CORS_ORIGINS = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173"
        ).split(",")

        # Redis Queue
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Security / CAPTCHA
        self.RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET", "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")

_settings = Config()

def get_settings() -> Config:
    return _settings
