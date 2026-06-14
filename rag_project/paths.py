from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "docs" / "ai-agent" / "rag"
CONFIG_FILE = CONFIG_DIR / "config.yml"

default_config = {
    "docs_dir": "docs",
    "input_dir": "docs/ai-agent/rag/input",
    "output_dir": "docs/ai-agent/rag/output",
    "graph_file": "docs/ai-agent/rag/output/graph.json",
    "chunks_file": "docs/ai-agent/rag/output/chunks.json",
    "metadata_file": "docs/ai-agent/rag/output/metadata.json"
}

def load_or_create_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)
        return default_config
    else:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)

config_data = load_or_create_config()

RAG_DIR = PROJECT_ROOT / "rag"
DOCS_DIR = PROJECT_ROOT / config_data.get("docs_dir", "docs")
INPUT_DIR = PROJECT_ROOT / config_data.get("input_dir", "docs/ai-agent/rag/input")
OUTPUT_DIR = PROJECT_ROOT / config_data.get("output_dir", "docs/ai-agent/rag/output")
CHUNKS_PATH = PROJECT_ROOT / config_data.get("chunks_file", "docs/ai-agent/rag/output/chunks.json")
GRAPH_PATH = PROJECT_ROOT / config_data.get("graph_file", "docs/ai-agent/rag/output/graph.json")
METADATA_PATH = PROJECT_ROOT / config_data.get("metadata_file", "docs/ai-agent/rag/output/metadata.json")
