from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """
    Memuat variabel environment dari file .env di direktori saat ini.
    """
    load_dotenv(Path.cwd() / ".env")
