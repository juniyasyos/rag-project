#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag_project.ingest import run_ingest
from rag_project.freshness import write_metadata
if __name__ == '__main__':
    run_ingest()
    write_metadata()
