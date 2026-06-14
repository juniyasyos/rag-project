import json
import time
from rag_project.paths import METADATA_PATH

def write_metadata():
    with open(METADATA_PATH, "w") as f:
        json.dump({"last_updated": time.time()}, f)

def check_freshness():
    if not METADATA_PATH.exists():
        print("No metadata.json. Rebuild RAG.")
    else:
        with open(METADATA_PATH, "r") as f:
            data = json.load(f)
        print(f"RAG was last updated: {time.ctime(data.get('last_updated', 0))}")
