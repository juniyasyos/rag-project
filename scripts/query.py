#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag_project.config import load_config
from rag_project.query import run_query
if __name__ == '__main__':
    load_config()
    run_query(" ".join(sys.argv[1:]).strip())
