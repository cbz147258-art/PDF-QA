import os
from dotenv import load_dotenv

load_dotenv()

# ===== DeepSeek API =====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ===== Embedding Model =====
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# ===== Upload Config =====
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {".pdf"}

# ===== Milvus Lite (embedded vector DB, no server needed) =====
MILVUS_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "milvus_db", "milvus.db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RETRIEVAL = 5

# ===== SQLite (metadata + QA records) =====
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdf_qa.db')}"