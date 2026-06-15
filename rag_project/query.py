import json
import re
import time
from rag_project.paths import CHUNKS_PATH, GRAPH_PATH
from rag_project.llm import llm_answer, llm_librarian, llm_big_answer

TOP_K = 3  # Dikurangi agar context tidak terlalu besar untuk SLM

def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9-]+", text.lower())
    return {w for w in words if len(w) > 2}

def score_chunks(query: str, query_keys: list[str], expanded_keys: list[str], dictionary: dict, chunks: list[dict], domain: str = None) -> list[tuple[float, dict]]:
    scored = []
    
    preferred_sources = dictionary.get("preferred_sources", [])
    avoid_sources = dictionary.get("avoid_sources", [])
    q_lower = query.lower()
    
    for chunk in chunks:
        source_file = chunk.get("source_file", "").lower()
        if domain and domain.lower() not in chunk.get("domain", source_file):
            continue
            
        content_lower = chunk["content"].lower()
        heading_lower = chunk.get("heading", "").lower()
        full_text = heading_lower + "\n" + content_lower
        
        score = 0
        
        # 1. Exact phrase boost (+10)
        if q_lower in full_text and len(q_lower) > 4:
            score += 10
            
        # 2. Keyword boost (+3)
        for k in query_keys:
            if k.lower() in full_text:
                score += 3
                
        # 3. Expanded key boost (+2)
        for ek in expanded_keys:
            if ek.lower() in full_text:
                score += 2
                
        # 4. Preferred Source boost (+5)
        if any(ps.lower() in source_file for ps in preferred_sources):
            score += 5
            
        # 5. Avoid Source penalty (-5)
        if any(av.lower() in source_file for av in avoid_sources):
            score -= 5
            
        if score > 0:
            scored.append((score, chunk))
            
    scored.sort(key=lambda x: -x[0])
    return scored[:TOP_K]

def score_graph(query: str, graph: dict, domain: str = None) -> tuple[list[dict], list[dict]]:
    q_tokens = tokenize(query)
    scored = []
    for node in graph["nodes"]:
        if domain and domain.lower() not in node.get("domain", node.get("source", "")).lower():
            continue
            
        n_id = node.get('id', '').lower()
        n_label = node.get('label', '').lower()
        n_type = node.get('type', '').lower()
        
        id_tokens = tokenize(n_id)
        label_tokens = tokenize(n_label)
        type_tokens = tokenize(n_type)
        
        overlap_id = len(q_tokens & id_tokens)
        overlap_label = len(q_tokens & label_tokens)
        type_match = 1 if len(q_tokens & type_tokens) > 0 else 0
        
        score = (overlap_label * 5) + (overlap_id * 3)
        if score > 0:
            score += type_match
            scored.append((score, node))
            
    scored.sort(key=lambda x: -x[0])
    relevant_nodes = [node for score, node in scored[:5]]
    
    # Ekstraksi Relasi 1-Hop
    relevant_node_ids = {n['id'] for n in relevant_nodes}
    node_lookup = {n['id']: n for n in graph["nodes"]}
    relevant_edges = []
    
    for edge in graph["edges"]:
        if edge["type"] in ["has_column", "contains", "has_topic"]:
            continue # Abaikan relasi receh/terlalu verbose
            
        if edge["from"] in relevant_node_ids or edge["to"] in relevant_node_ids:
            from_node = node_lookup.get(edge["from"])
            to_node = node_lookup.get(edge["to"])
            if from_node and to_node:
                relevant_edges.append({
                    "from_label": from_node["label"],
                    "to_label": to_node["label"],
                    "type": edge["type"]
                })
    
    return relevant_nodes, relevant_edges[:15] # Batasi max 15 relasi

def build_context(chunks, nodes) -> str:
    parts = ["=== DOKUMEN RELEVAN ==="]
    seen = set()
    for score, chunk in chunks:
        header = f"[{chunk['source_file']}] {chunk.get('heading', '')}"
        if header not in seen:
            seen.add(header)
            parts.append(f"\n{header}\n{chunk['content'][:500]}") # Batasi panjang konten per chunk
    if nodes:
        parts.append("\n=== TOPIK TERKAIT ===")
        for n in nodes: parts.append(f"  • {n['label']} ({n['type']})")
    
    context_str = "\n".join(parts)
    return context_str[:1500] # Maksimal 1500 karakter untuk menghemat token SLM

def build_context_pack(chunks) -> str:
    parts = []
    forbidden = ["retrieval-only", "contoh query", "query:", "output:", "tree singka", "=====", "chunk teratas", "[source]", "debug"]
    for _, chunk in chunks:
        lines = chunk['content'].split('\n')
        clean_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(f in line_lower for f in forbidden):
                continue
            clean_lines.append(line.strip())
        
        clean_content = " ".join(clean_lines)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        clean_content = re.sub(r'#+\s*', '', clean_content) # Hapus markdown header chars
        
        if clean_content:
            parts.append(f"{chunk.get('heading', '')}: {clean_content[:150]}...")
            
    return " | ".join(parts)[:500].strip()

def load_data():
    try:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f: chunks = json.load(f)
    except FileNotFoundError:
        chunks = []
    try:
        with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
    except FileNotFoundError:
        graph = {"nodes": [], "edges": []}
    return chunks, graph

def run_context(question: str, domain: str = None) -> str:
    chunks, graph = load_data()
    from rag_project.llm import extract_query_keys, expand_keys, load_dictionary
    dictionary = load_dictionary()
    qk = extract_query_keys(question)
    ek = expand_keys(question, qk)
    top_chunks = score_chunks(question, qk, ek, dictionary, chunks, domain)
    rel_nodes, _ = score_graph(question, graph, domain)
    return build_context(top_chunks, rel_nodes)

def run_query(question: str, domain: str = None, mode: str = "librarian", debug: bool = False):
    chunks, graph = load_data()
    if not chunks and not graph["nodes"]:
        print("No data found. Run scan or ingest first.")
        return
    
    from rag_project.llm import extract_query_keys, detect_intent, expand_keys, load_dictionary
    dictionary = load_dictionary()
    
    query_keys = extract_query_keys(question)
    intent = detect_intent(question)
    expanded_keys = expand_keys(question, query_keys)
    
    top_chunks = score_chunks(question, query_keys, expanded_keys, dictionary, chunks, domain)
    rel_nodes, rel_edges = score_graph(question, graph, domain)
    context = build_context(top_chunks, rel_nodes)
    
    if debug:
        print("=== DEBUG: TOP CHUNKS ===")
        for score, chunk in top_chunks:
            print(f"[{score}] {chunk['source_file']} - {chunk.get('heading', 'NO HEADING')}")
        print("=== DEBUG: RELEVANT NODES ===")
        for node in rel_nodes:
            print(f"- {node['id']} ({node['label']})")
        print("===========================\n")
    
    start_time = time.time()
    
    combined_keys = " ".join(query_keys).lower() + " " + question.lower()
        
    # 4. Route (Deterministic)
    if any(k in combined_keys for k in ["dimana", "lokasi", "daftar", "sumber", "file"]):
        route = "docs_only"
    elif len(query_keys) <= 1:
        route = "clarify"
    else:
        route = "ai_agent"
        
    # Kumpulkan data dokumen (Deterministic)
    relevant_docs = list(set(c['source_file'] for _, c in top_chunks))
    
    relevant_topics = list(set(n['label'] for n in rel_nodes))
    for edge in rel_edges:
        rel_str = f"{edge['from_label']} --[{edge['type']}]--> {edge['to_label']}"
        if rel_str not in relevant_topics:
            relevant_topics.append(rel_str)
            
    context_pack = build_context_pack(top_chunks)
    
    # 5. Confidence (Deterministic)
    if intent == "docs_lookup" or len(query_keys) == 0:
        confidence = 0.4
    else:
        doc_count = len(relevant_docs)
        if doc_count >= 3:
            confidence = 0.85
        elif doc_count == 2:
            confidence = 0.75
        elif doc_count == 1:
            confidence = 0.60
        else:
            confidence = 0.4
            
    notes = "Metadata dan konteks siap dikirim ke AI agent. RAG tidak menjawab final."
    
    final_data = {
        "user_query": question,
        "intent": intent,
        "query_keys": query_keys,
        "expanded_keys": expanded_keys,
        "route": route,
        "confidence": confidence,
        "relevant_docs": relevant_docs,
        "relevant_topics": relevant_topics,
        "context_pack": context_pack,
        "notes": notes
    }
    
    elapsed = time.time() - start_time
    
    if mode == "librarian" or mode == "handoff":
        print(json.dumps(final_data, indent=2))
