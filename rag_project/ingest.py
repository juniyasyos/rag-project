import json
import re
from pathlib import Path
from rag_project.paths import INPUT_DIR, OUTPUT_DIR, CHUNKS_PATH, GRAPH_PATH
from rag_project.graph import build_graph

MAX_CHUNK_SIZE = 2000

def heading_level(line: str) -> int:
    m = re.match(r"^(#{1,6})\s", line)
    return len(m.group(1)) if m else 0

def split_long_text(text: str, filename: str, heading: str, start_index: int) -> list[dict]:
    paragraphs = re.split(r"\n\s*\n", text)
    sub_chunks = []
    buffer = []
    buf_len = 0
    idx = start_index

    for para in paragraphs:
        para = para.strip()
        if not para: continue
        if buf_len + len(para) > MAX_CHUNK_SIZE and buffer:
            idx += 1
            sub_chunks.append({
                "id": f"chunk-{idx:04d}",
                "source_file": filename,
                "heading": heading,
                "chunk_index": idx,
                "content": "\n\n".join(buffer),
            })
            buffer = [para]
            buf_len = len(para)
        else:
            buffer.append(para)
            buf_len += len(para)

    if buffer:
        idx += 1
        sub_chunks.append({
            "id": f"chunk-{idx:04d}",
            "source_file": filename,
            "heading": heading,
            "chunk_index": idx,
            "content": "\n\n".join(buffer),
        })
    return sub_chunks

def chunk_markdown(filename: str, content: str) -> list[dict]:
    lines = content.split("\n")
    chunks = []
    current_heading = "(root)"
    current_lines = []
    chunk_counter = 0
    heading_encountered = False

    def flush():
        nonlocal chunk_counter
        text = "\n".join(current_lines).strip()
        if not text: return
        if len(text) > MAX_CHUNK_SIZE:
            sub_chunks = split_long_text(text, filename, current_heading, chunk_counter)
            chunks.extend(sub_chunks)
            chunk_counter += len(sub_chunks)
        else:
            chunk_counter += 1
            chunks.append({
                "id": f"chunk-{chunk_counter:04d}",
                "source_file": filename,
                "heading": current_heading,
                "chunk_index": chunk_counter,
                "content": text,
            })

    for line in lines:
        h = heading_level(line)
        if h > 0:
            if heading_encountered:
                flush()
            else:
                heading_encountered = True
            current_heading = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        flush()
    return chunks

def run_ingest():
    from rich.console import Console
    from rich.table import Table
    console = Console()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    files = []
    for f in sorted(INPUT_DIR.glob("*.md")):
        files.append((f.name, f.read_text(encoding="utf-8")))
        
    all_chunks = []
    for filename, content in files:
        all_chunks.extend(chunk_markdown(filename, content))
        
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
    graph = build_graph(files)
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
        
    console.print(f"  Created {len(all_chunks)} chunks, {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
