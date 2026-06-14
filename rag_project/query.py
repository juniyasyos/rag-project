import json
import re
import time
from rag_project.paths import CHUNKS_PATH, GRAPH_PATH
from rag_project.llm import llm_answer, llm_librarian, llm_big_answer

TOP_K = 3  # Dikurangi agar context tidak terlalu besar untuk SLM

def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9-]+", text.lower())
    return {w for w in words if len(w) > 2}

def score_chunks(query: str, chunks: list[dict], domain: str = None) -> list[tuple[float, dict]]:
    q_tokens = tokenize(query)
    q_words = list(q_tokens)
    scored = []
    
    # Filter RAG-specific docs and files to avoid recursion unless query is about RAG
    is_rag_query = any(k in q_tokens for k in ['rag', 'graphrag', 'pustakawan', 'llm', 'ai-agent', 'ai'])
    ignore_keywords = ['releases/v', 'v0.', 'contoh query', 'contoh_query', 'debug']
    if not is_rag_query:
        ignore_keywords.extend(['rag-project', 'rag_', 'ai-agent/rag', 'ai_agent_usage'])
    
    for chunk in chunks:
        source_file = chunk.get("source_file", "").lower()
        if any(ik in source_file for ik in ignore_keywords):
            continue
            
        if domain and domain.lower() not in chunk.get("domain", source_file):
            continue
            
        c_tokens = tokenize(chunk["content"])
        heading_lower = chunk.get("heading", "").lower()
        
        # 1. Exact Heading/Source Boost (Sangat Kuat)
        heading_boost = sum(10 for qt in q_words if qt in heading_lower)
        source_boost = sum(15 for qt in q_words if qt in source_file)
        
        # 2. Strong Overlap (Overlap pada kata yang lebih panjang/unik)
        strong_overlap = sum(3 for qt in q_tokens if qt in c_tokens and len(qt) > 4)
        
        # 3. Standard Overlap
        overlap = len(q_tokens & c_tokens)
        
        # 4. Partial Match
        partial = sum(0.5 for qt in q_words for ct in c_tokens if (qt in ct or ct in qt) and len(qt) > 3)
        
        score = overlap + strong_overlap + partial + heading_boost + source_boost
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
    top_chunks = score_chunks(question, chunks, domain)
    rel_nodes, _ = score_graph(question, graph, domain)
    return build_context(top_chunks, rel_nodes)

def run_query(question: str, domain: str = None, mode: str = "librarian", debug: bool = False):
    chunks, graph = load_data()
    if not chunks and not graph["nodes"]:
        print("No data found. Run scan or ingest first.")
        return
    
    top_chunks = score_chunks(question, chunks, domain)
    rel_nodes, rel_edges = score_graph(question, graph, domain)
    context = build_context(top_chunks, rel_nodes)
    
    if debug:
        print("=== DEBUG: TOP CHUNKS ===")
        for score, chunk in top_chunks:
            print(f"[{score}] {chunk['source_file']} - {chunk.get('heading', 'NO HEADING')}")
            # print(f"Preview: {chunk['content'][:100]}...\n")
        print("=== DEBUG: RELEVANT NODES ===")
        for node in rel_nodes:
            print(f"- {node['id']} ({node['label']})")
        print("===========================\n")
    
    start_time = time.time()
    
    # Jalankan SLM untuk mengerti semantik (hanya mengekstrak intent & query_keys)
    answer = llm_librarian(question, context)
    
    # Kumpulkan fallback rule-based
    q_lower = question.lower()
    fallback_query_keys = [w for w in q_lower.split() if len(w) > 2]
    
    # 2. Intent - Kompleks Rule-Based
    intent_rules = {
        "project_overview": ["jelaskan project", "apa itu", "tentang siimut", "ringkasan", "overview", "tujuan"],
        "command_lookup": ["command", "perintah", "migrate", "setup", "install", "menjalankan", "start", "artisan", "run"],
        "architecture_analysis": ["arsitektur", "struktur", "modular", "monolith", "alur", "flow", "desain", "database", "skema"],
        "rag_usage": ["rag", "graphrag", "knowledge", "pustakawan", "ai agent", "chunk", "ingest", "search"],
        "troubleshooting": ["error", "bug", "gagal", "masalah", "issue", "troubleshoot", "log"],
        "api_reference": ["api", "endpoint", "route", "controller", "response", "request"],
    }
    
    fallback_intent = "docs_lookup"
    for intent_key, keywords in intent_rules.items():
        if any(k in q_lower for k in keywords):
            fallback_intent = intent_key
            break
        
    query_keys = fallback_query_keys
    intent = fallback_intent
    
    # SLM Dinonaktifkan sementara, kita hanya pakai deterministic rules.
    # Namun struktur try/except tetap dijaga untuk keamanan API.
    if answer:
        try:
            json_match = re.search(r'\{.*\}', answer.replace('\n', ' '), re.DOTALL)
            if json_match:
                slm_data = json.loads(json_match.group(0))
            else:
                slm_data = json.loads(answer)
                
            if "query_keys" in slm_data and isinstance(slm_data["query_keys"], list) and len(slm_data["query_keys"]) > 0:
                query_keys = slm_data["query_keys"]
            if "intent" in slm_data and slm_data["intent"].strip():
                intent = slm_data["intent"]
        except:
            pass # Fallback digunakan jika parsing gagal
            
    # 3. Expanded Keys (Kompleks Deterministic)
    expanded_keys = []
    combined_keys = " ".join(query_keys).lower() + " " + q_lower
    
    expanded_keys_rules = {
        "siimut": ["SIIMUT", "Sistem Indikator Mutu", "Laravel 12", "Filament", "modular monolith"],
        "migrate": ["artisan migrate", "database", "COMMANDS.md", "schema", "table"],
        "rag": ["GraphRAG", "knowledge base", "chunks", "graph", "librarian", "AI_AGENT_USAGE.md"],
        "filament": ["admin panel", "Livewire", "resource", "table", "form", "dashboard"],
        "error": ["KNOWN_ISSUES.md", "TROUBLESHOOTING.md", "log", "bug", "exception"],
        "api": ["routes/api.php", "controller", "endpoint", "json"],
        "docker": ["docker-compose", "container", "sail", "image", "deployment"]
    }
    
    for kw, exp_keys in expanded_keys_rules.items():
        if kw in combined_keys:
            expanded_keys.extend(exp_keys)
            
    # Hapus duplikat dari expanded_keys dengan menjaga urutan
    expanded_keys = list(dict.fromkeys(expanded_keys))
        
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
