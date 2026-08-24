import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
CHROMA_COLLECTION_NAME = "policy_docs"

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "data" / "minidesk.db"))

POLICIES_DIR = os.getenv("POLICIES_DIR", str(BASE_DIR / "data" / "policies"))

RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
RETRIEVAL_SIMILARITY_THRESHOLD = float(os.getenv("RETRIEVAL_SIMILARITY_THRESHOLD", "0.35"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
ADMIN_EMAIL = "admin@admin.com"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

TICKET_CATEGORIES = [
    "VPN Access",
    "Password Reset",
    "Hardware Request",
    "Remote Work",
    "Expense Reimbursement",
    "Software License",
    "Other",
]

TICKET_STATUSES = ["open", "in_progress", "resolved"]
