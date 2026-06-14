import json
import re
from rag_project.paths import CHUNKS_PATH, GRAPH_PATH
from rag_project.llm import llm_answer

TOP_K = 5

def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9-]+", text.lower())
    return {w for w in words if len(w) > 2}

def score_chunks(query: str, chunks: list[dict]) -> list[tuple[float, dict]]:
    q_tokens = tokenize(query)
    q_words = list(q_tokens)
    scored = []
    for chunk in chunks:
        c_tokens = tokenize(chunk["content"])
        overlap = len(q_tokens & c_tokens)
        partial = sum(1 for qt in q_words for ct in c_tokens if qt in ct or ct in qt)
        heading_boost = sum(2 for qt in q_words if qt in chunk["heading"].lower())
        source_boost = sum(1 for qt in q_words if qt in chunk["source_file"].lower())
        score = overlap * 2 + partial + heading_boost + source_boost
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: -x[0])
    return scored[:TOP_K]

def score_graph(query: str, graph: dict) -> tuple[list[dict], list[dict]]:
    q_tokens = tokenize(query)
    relevant_nodes = []
    for node in graph["nodes"]:
        text = f"{node['id']} {node['label']} {node['type']}".lower()
        if q_tokens & tokenize(text):
            relevant_nodes.append(node)
    node_ids = {n["id"] for n in relevant_nodes}
    relevant_edges = []
    for edge in graph["edges"]:
        edge_text = f"{edge['from']} {edge['to']} {edge['type']}".lower()
        if q_tokens & tokenize(edge_text) or edge["from"] in node_ids or edge["to"] in node_ids:
            relevant_edges.append(edge)
    return relevant_nodes, relevant_edges

def build_context(chunks, nodes, edges) -> str:
    parts = ["Berikut adalah konteks dari dokumentasi project:\n"]
    parts.append("=== DOKUMEN ===")
    seen = set()
    for score, chunk in chunks:
        header = f"[{chunk['source_file']}] {chunk['heading']}"
        if header not in seen:
            seen.add(header)
            parts.append(f"\n{header}\n{chunk['content'][:1500]}")
    if nodes or edges:
        parts.append("\n=== GRAF PENGETAHUAN ===")
        for n in nodes: parts.append(f"  • [{n['type']}] {n['label']} ({n['id']})")
        for e in edges: parts.append(f"  • {e['from']} --[{e['type']}]--> {e['to']}")
    return "\n".join(parts)

def run_query(question: str):
    import sys
    try:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f: chunks = json.load(f)
        with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
    except FileNotFoundError:
        print("Run ingest first.")
        return
    
    top_chunks = score_chunks(question, chunks)
    rel_nodes, rel_edges = score_graph(question, graph)
    context = build_context(top_chunks, rel_nodes, rel_edges)
    answer = llm_answer(question, context)
    
    print("\n" + "="*60 + f"\n  Pertanyaan: {question}\n" + "="*60 + "\n")
    if answer:
        print(f"  Jawaban:\n  {answer}")
    else:
        print("  [Retrieval Only — no LLM configured]\n")
        for i, (score, chunk) in enumerate(top_chunks, 1):
            print(f"  [{i}] {chunk['source_file']} → {chunk['heading']} (Score: {score})\n      {chunk['content'][:200]}...")
    if top_chunks:
        print("\n  Sumber:")
        seen = set()
        for _, c in top_chunks:
            if c['source_file'] not in seen:
                print(f"    • docs/{c['source_file']}")
                seen.add(c['source_file'])
    if rel_nodes or rel_edges:
        print("\n  Relasi Graph Terkait:")
        for n in rel_nodes: print(f"    • [{n['type']}] {n['label']} ({n['id']})")
        for e in rel_edges: print(f"    • {e['from']} --[{e['type']}]--> {e['to']}")
