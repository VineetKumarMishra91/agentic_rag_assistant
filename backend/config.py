import os
from dotenv import load_dotenv

load_dotenv(override=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MONGODB_URI = os.environ.get("MONGODB_URI")
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR") or "chroma_data"
RECALL_API_KEY = os.environ.get("RECALL_API_KEY")

GEMINI_CHAT_MODEL = os.environ.get("GEMINI_CHAT_MODEL", "gemini-3.5-flash")
GEMINI_LITE_MODEL = os.environ.get("GEMINI_LITE_MODEL", "gemini-3.5-flash-lite")
GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

