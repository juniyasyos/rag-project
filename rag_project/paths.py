import os
from pathlib import Path
from dotenv import load_dotenv

# Prioritaskan load .env dari direktori saat ini (Current Working Directory)
load_dotenv(Path.cwd() / ".env")

# 1. Tentukan Project Root (Bisa dari .env atau Current Working Directory)
_env_root = os.environ.get("RAG_PROJECT_ROOT")
if _env_root and _env_root.strip():
    PROJECT_ROOT = Path(_env_root).resolve()
else:
    PROJECT_ROOT = Path.cwd().resolve()

# 2. Lokasi instalasi package ini sendiri (berguna jika butuh baca resource internal)
RAG_DIR = Path(__file__).resolve().parent.parent

# 3. Path ke direktori docs dan folder penyimpanan hasil RAG
DOCS_DIR = PROJECT_ROOT / os.environ.get("RAG_DOCS_DIR", "docs")
_storage_root = PROJECT_ROOT / os.environ.get("RAG_STORAGE_DIR", ".ai/rag")

INPUT_DIR = _storage_root / "input"
OUTPUT_DIR = _storage_root / "output"
CHUNKS_PATH = OUTPUT_DIR / "chunks.json"
GRAPH_PATH = OUTPUT_DIR / "graph.json"
METADATA_PATH = OUTPUT_DIR / "metadata.json"
CUSTOM_DICTIONARY_PATH = _storage_root / os.environ.get("RAG_DICTIONARY", "dictionary.yml")
DICTIONARY_PATH = RAG_DIR / "rag_project" / "scanners" / "dictionary.yml"

# Pastikan folder penyimpanan tersedia
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)
