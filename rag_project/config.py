import os
from dotenv import load_dotenv
from rag_project.paths import RAG_DIR

def load_config():
    load_dotenv(RAG_DIR / ".env")
    load_dotenv(RAG_DIR / ".env.example")
