import os
import re


# ============================================================
# Caveman Librarian
# Tidak pakai SLM.
# Tidak jawab lokal.
# Tidak panggil API besar.
# Cuma metadata, key, route.
# ============================================================


STOPWORDS = {
    "apa", "itu", "yang", "di", "ke", "dari", "dan", "atau",
    "untuk", "dengan", "pada", "dalam", "dong", "nih", "ya",
    "saya", "aku", "kamu", "kau", "tolong"
}


def extract_query_keys(question: str) -> list[str]:
    text = question.lower().strip()

    words = re.findall(r"[a-zA-Z0-9_\-]+", text)

    keys = []
    for word in words:
        if word in STOPWORDS:
            continue
        if len(word) < 2:
            continue
        keys.append(word)

    return keys


def detect_intent(question: str) -> str:
    q = question.lower()

    if any(x in q for x in ["rag", "graphrag", "knowledge", "knowledge base", "librarian"]):
        return "rag_usage"

    if any(x in q for x in ["command", "perintah", "migrate", "migration", "setup", "install", "jalankan", "run"]):
        return "command_lookup"

    if any(x in q for x in ["arsitektur", "architecture", "struktur", "modular", "monolith", "module"]):
        return "architecture_analysis"

    if "jelaskan" in q and any(x in q for x in ["project", "proyek", "siimut"]):
        return "project_overview"

    if any(x in q for x in ["dokumen", "docs", "file", "sumber"]):
        return "docs_lookup"

    return "docs_lookup"


def expand_keys(question: str, query_keys: list[str]) -> list[str]:
    q = question.lower()
    expanded = []

    def add(items: list[str]):
        for item in items:
            if item not in expanded:
                expanded.append(item)

    if "siimut" in q:
        add([
            "SIIMUT",
            "Sistem Indikator Mutu",
            "Rumah Sakit",
            "Laravel 12",
            "Filament",
            "Filament 3.2",
            "modular monolith",
            "app/Modules",
            "PROJECT_STRUCTURE",
            "PROJECT_CONTEXT",
        ])

    if any(x in q for x in ["command", "perintah", "migrate", "migration", "setup", "install", "jalankan", "run"]):
        add([
            "COMMANDS.md",
            "artisan",
            "php artisan",
            "php artisan migrate",
            "database",
            "setup development",
        ])

    if any(x in q for x in ["arsitektur", "architecture", "struktur", "modular", "monolith", "module"]):
        add([
            "PROJECT_STRUCTURE.md",
            "modular monolith",
            "app/Modules",
            "Domain layer",
            "Laravel structure",
        ])

    if any(x in q for x in ["rag", "graphrag", "knowledge", "knowledge base", "librarian"]):
        add([
            "GraphRAG",
            "RAG",
            "knowledge base",
            "chunks",
            "graph",
            "librarian",
            "handoff",
        ])

    return expanded


def detect_route(question: str, intent: str, query_keys: list[str]) -> str:
    q = question.lower().strip()

    if not q or len(query_keys) == 0:
        return "clarify"

    if any(x in q for x in ["daftar dokumen", "dokumen apa", "sumber apa", "file apa", "lokasi file"]):
        return "docs_only"

    return "ai_agent"


def calculate_confidence(intent: str, query_keys: list[str], relevant_docs: list[str]) -> float:
    if intent == "unknown" or not query_keys:
        return 0.4

    doc_count = len(relevant_docs)

    if doc_count >= 3:
        return 0.85

    if doc_count == 2:
        return 0.75

    if doc_count == 1:
        return 0.6

    return 0.5


def clean_context_pack(context: str, max_chars: int = 1000) -> str:
    if not context:
        return ""

    banned_patterns = [
        "rag-project query",
        "Retrieval-only",
        "Retrieval Only",
        "Contoh Query",
        "[Retrieval Only",
        "no LLM configured",
        "klasifikasi singkat",
        "kata_kunci1",
        "kata_kunci2",
        "intent pertanyaan",
        "alasan",
        "Tulis ringkasan",
        "```txt",
        "```",
    ]

    lines = context.splitlines()
    clean_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if any(pattern.lower() in stripped.lower() for pattern in banned_patterns):
            continue

        # Buang tree dump
        if stripped.startswith(("├", "│", "└", "─")):
            continue

        # Buang heading terlalu mentah tapi simpan isi penting
        stripped = stripped.replace("#", "").strip()
        stripped = stripped.replace("---", "").strip()

        if not stripped:
            continue

        clean_lines.append(stripped)

    text = " ".join(clean_lines)

    # Rapikan spasi
    text = re.sub(r"\s+", " ", text).strip()

    # Potong aman
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].strip()

    return text


def build_librarian_metadata(
    question: str,
    context: str,
    relevant_docs: list[str] | None = None,
    relevant_topics: list[str] | None = None,
) -> dict:
    relevant_docs = relevant_docs or []
    relevant_topics = relevant_topics or []

    query_keys = extract_query_keys(question)
    intent = detect_intent(question)
    expanded_keys = expand_keys(question, query_keys)
    route = detect_route(question, intent, query_keys)
    confidence = calculate_confidence(intent, query_keys, relevant_docs)
    context_pack = clean_context_pack(context)

    return {
        "user_query": question,
        "intent": intent,
        "query_keys": query_keys,
        "expanded_keys": expanded_keys,
        "route": route,
        "confidence": confidence,
        "relevant_docs": relevant_docs[:5],
        "relevant_topics": relevant_topics[:8],
        "context_pack": context_pack,
        "notes": "Metadata dan konteks siap dikirim ke AI agent. RAG tidak menjawab final.",
    }


# ============================================================
# Compatibility stubs
# Supaya import lama tidak langsung error.
# Tapi tidak dipakai untuk jawab.
# ============================================================


def llm_librarian(question: str, context: str) -> str | None:
    """
    Deprecated.
    Jangan pakai SLM untuk librarian.
    Pakai build_librarian_metadata().
    """
    return None


def llm_answer(question: str, context: str) -> str | None:
    """
    Disabled.
    RAG tidak boleh menjawab lokal.
    """
    return None


def llm_big_answer(question: str, context: str) -> str | None:
    """
    Disabled.
    RAG tidak boleh auto-call LLM besar.
    """
    return None