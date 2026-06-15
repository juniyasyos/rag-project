import json
import re
import time
from rag_project.paths import CHUNKS_PATH, GRAPH_PATH

TOP_K = 3  # Dikurangi agar context tidak terlalu besar untuk SLM

def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[a-z0-9-]+", text.lower())
    return {w for w in words if len(w) > 2}

def score_chunks(intent: str, subject: str, entities: list[str], keys: list[str], preferred_sources: list[str], avoid_sources: list[str], chunks: list[dict], domains: list[str] = None, top_k: int = 3) -> list[tuple[float, dict]]:
    scored = []
    
    for chunk in chunks:
        source_file = chunk.get("source_file", "").lower()
        if domains:
            if not any(d.lower() in chunk.get("domain", source_file).lower() for d in domains):
                continue
            
        content_lower = chunk["content"].lower()
        heading_lower = chunk.get("heading", "").lower()
        full_text = heading_lower + "\n" + content_lower
        
        score = 0
        
        # Boost based on explicit args
        if subject and subject.lower() in full_text:
            score += 10
            
        for e in entities:
            if e.lower() in full_text:
                score += 5
                
        for k in keys:
            if k.lower() in full_text:
                score += 3
                
        # Preferred Source boost
        if any(ps.lower() in source_file for ps in preferred_sources):
            score += 5
            
        # Avoid Source penalty
        if any(av.lower() in source_file for av in avoid_sources):
            score -= 5
            
        if score > 0:
            scored.append((score, chunk))
            
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]

def score_graph(subject: str, entities: list[str], keys: list[str], graph: dict, domains: list[str] = None) -> tuple[list[dict], list[dict]]:
    q_tokens = set()
    if subject: q_tokens.update(tokenize(subject))
    for e in entities: q_tokens.update(tokenize(e))
    for k in keys: q_tokens.update(tokenize(k))
    
    scored = []
    for node in graph["nodes"]:
        if domains:
            if not any(d.lower() in node.get("domain", node.get("source", "")).lower() for d in domains):
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
    parts = ["DOKUMEN RELEVAN:"]
    seen = set()
    for score, chunk in chunks:
        header = f"[{chunk['source_file']}] {chunk.get('heading', '')}"
        if header not in seen:
            seen.add(header)
            parts.append(f"{header}: {chunk['content'][:500]}") # Batasi panjang konten per chunk
    if nodes:
        parts.append("TOPIK TERKAIT:")
        for n in nodes: parts.append(f"{n['label']} ({n['type']})")
    
    context_str = " | ".join(parts)
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

def run_context(question: str, domains: list[str] = None) -> str:
    chunks, graph = load_data()
    
    # Fallback default route for simple context command
    preferred_sources = []
    avoid_sources = []
    
    # For backward compat, use the question as a key
    top_chunks = score_chunks("docs_lookup", question, [], [], preferred_sources, avoid_sources, chunks, domains)
    rel_nodes, _ = score_graph(question, [], [], graph, domains)
    return build_context(top_chunks, rel_nodes)

def run_query(intent: str, subject: str, entities: list[str], keys: list[str], domains: list[str], top_k: int, mode: str, debug: bool):
    chunks, graph = load_data()
    if not chunks and not graph["nodes"]:
        print("No data found. Run scan or ingest first.")
        return
    
    route_config = {
        "project_overview": {"read_first": ["docs"], "read_if_needed": ["README", "ARCHITECTURE"], "avoid_first": ["services", "models", "routes"]},
        "architecture_analysis": {"read_first": ["docs", "services", "modules"], "read_if_needed": ["config"], "avoid_first": ["migrations"]},
        "service_lookup": {"read_first": ["services", "entities", "models"], "read_if_needed": ["repositories"], "avoid_first": ["routes", "docs"]},
        "data_model_lookup": {"read_first": ["models", "migrations"], "read_if_needed": ["database", "schema"], "avoid_first": ["routes", "services"]},
        "command_lookup": {"read_first": ["COMMANDS", "README"], "read_if_needed": ["scripts", "package.json"], "avoid_first": ["models", "services"]},
        "api_reference": {"read_first": ["routes", "controllers"], "read_if_needed": ["middlewares", "requests"], "avoid_first": ["models", "migrations"]},
        "troubleshooting": {"read_first": ["KNOWN_ISSUES", "CHANGELOG"], "read_if_needed": ["logs", "exceptions"], "avoid_first": ["docs", "README"]},
        "rag_usage": {"read_first": ["rag"], "read_if_needed": ["config"], "avoid_first": ["services", "models"]},
        "docs_lookup": {"read_first": ["docs"], "read_if_needed": [], "avoid_first": []}
    }
    
    mapping = route_config.get(intent, {"read_first": [], "read_if_needed": [], "avoid_first": []})
    preferred_sources = mapping["read_first"]
    avoid_sources = mapping["avoid_first"]
    
    top_chunks = score_chunks(intent, subject, entities, keys, preferred_sources, avoid_sources, chunks, domains, top_k)
    rel_nodes, rel_edges = score_graph(subject, entities, keys, graph, domains)
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
    
    # Route logic based on intent
    if intent in ["project_overview", "docs_lookup", "command_lookup"]:
        route = "docs_only"
    elif intent in ["service_lookup", "data_model_lookup", "api_reference"]:
        route = "code_lookup"
    else:
        route = "ai_agent"
        
    relevant_docs = list(set(c['source_file'] for _, c in top_chunks))
    for node in rel_nodes:
        if 'source' in node and node['source'] not in relevant_docs:
            relevant_docs.append(node['source'])
    relevant_topics = list(set(n['label'] for n in rel_nodes))
    for edge in rel_edges:
        rel_str = f"{edge['from_label']} --[{edge['type']}]--> {edge['to_label']}"
        if rel_str not in relevant_topics:
            relevant_topics.append(rel_str)
            
    context_pack = build_context_pack(top_chunks)
    if not context_pack and relevant_topics:
        # Fallback for code_lookup when only graph nodes match
        clean_topics = [t.strip().replace('\n', '').replace('  ', ' ') for t in relevant_topics if t.strip()]
        context_pack = "Nodes/Relations: " + " | ".join(clean_topics[:10])
    
    confidence = 0.85 if len(relevant_docs) >= 1 else 0.4
    
    final_data = {
        "intent": intent,
        "subject": subject,
        "entities": entities,
        "keys": keys,
        "domains": domains,
        "route": route,
        "confidence": confidence,
        "relevant_docs": relevant_docs,
        "relevant_topics": relevant_topics,
        "context_pack": context_pack,
    }
    
    if mode == "handoff":
        final_data["read_first"] = mapping["read_first"]
        final_data["read_if_needed"] = mapping["read_if_needed"]
        final_data["avoid_first"] = mapping["avoid_first"]
    
    elapsed = time.time() - start_time
    
    print(json.dumps(final_data, separators=(',', ':')))
