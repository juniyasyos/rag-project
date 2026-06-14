#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag_project.sync import sync_docs
if __name__ == '__main__': sync_docs()
