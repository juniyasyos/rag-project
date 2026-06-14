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
    
    # Filter RAG-specific docs and files to avoid recursion
    ignore_keywords = ['rag-project', 'rag_', 'ai-agent/rag', 'releases/v', 'v0.']
    
    for chunk in chunks:
        source_file = chunk.get("source_file", "").lower()
        if any(ik in source_file for ik in ignore_keywords):
            continue
            
        if domain and domain.lower() not in chunk.get("domain", source_file):
            continue
            
        c_tokens = tokenize(chunk["content"])
        overlap = len(q_tokens & c_tokens)
        partial = sum(1 for qt in q_words for ct in c_tokens if qt in ct or ct in qt)
        heading_boost = sum(2 for qt in q_words if qt in chunk.get("heading", "").lower())
        source_boost = sum(1 for qt in q_words if qt in source_file)
        score = overlap * 2 + partial + heading_boost + source_boost
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: -x[0])
    return scored[:TOP_K]

def score_graph(query: str, graph: dict, domain: str = None) -> tuple[list[dict], list[dict]]:
    q_tokens = tokenize(query)
    relevant_nodes = []
    for node in graph["nodes"]:
        if domain and domain.lower() not in node.get("domain", node.get("source", "")).lower():
            continue
        text = f"{node['id']} {node['label']} {node['type']}".lower()
        if q_tokens & tokenize(text):
            relevant_nodes.append(node)
    
    # Hanya pakai node ID untuk relevansi, tidak perlu memuat edge terlalu banyak
    return relevant_nodes[:5], []

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
    for _, chunk in chunks:
        clean_content = chunk['content'].replace('\n', ' ').strip()
        parts.append(clean_content[:300]) # Ambil intisari per dokumen
    return " ".join(parts)[:1500]

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

def run_query(question: str, domain: str = None, mode: str = "librarian"):
    chunks, graph = load_data()
    if not chunks and not graph["nodes"]:
        print("No data found. Run scan or ingest first.")
        return
    
    top_chunks = score_chunks(question, chunks, domain)
    rel_nodes, _ = score_graph(question, graph, domain)
    context = build_context(top_chunks, rel_nodes)
    
    start_time = time.time()
    
    if mode == "librarian":
        answer = llm_librarian(question, context)
        elapsed = time.time() - start_time
        if answer:
            # Parse JSON and format
            try:
                # Cari blok JSON jika SLM ngaco cetak teks lain
                json_match = re.search(r'\{.*\}', answer.replace('\n', ' '), re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    data = json.loads(answer)
            except:
                data = {
                    "intent": "unknown",
                    "can_answer_locally": False,
                    "should_call_big_llm": True,
                    "confidence": 0.0,
                    "relevant_docs": [],
                    "relevant_topics": [],
                    "answer_local": "",
                    "reason": "SLM returned invalid JSON"
                }
            
            # Enforce rule: kalau can_answer_locally=false maka should_call_big_llm=true
            if not data.get("can_answer_locally", True):
                data["should_call_big_llm"] = True
                
            # Programmatically assign context_pack from chunks
            data["context_pack"] = build_context_pack(top_chunks)
            
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps({"error": "Failed to get librarian response"}, indent=2))
            
    elif mode == "handoff":
        context_pack = build_context_pack(top_chunks)
        
        # Cetak prompt siap kirim tanpa mengeksekusi LLM besar
        print("\n--- PROMPT UNTUK LLM BESAR ---\n")
        print(f"Pertanyaan:\n{question}\n")
        print("Konteks Ringkas (Context Pack):")
        print(context_pack)
        
        print("\nSumber Dokumen:")
        seen = set()
        for _, c in top_chunks:
            if c['source_file'] not in seen:
                print(f"  • {c['source_file']}")
                seen.add(c['source_file'])
                
        print("\nTolong berikan penjelasan detail, analisa, atau instruksi langkah demi langkah berdasarkan konteks di atas.")
        print("\n------------------------------\n")
        elapsed = time.time() - start_time
