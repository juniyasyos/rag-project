import os
import re
import yaml
from rag_project.paths import CUSTOM_DICTIONARY_PATH, DICTIONARY_PATH

def load_dictionary():
    dict_path = CUSTOM_DICTIONARY_PATH if CUSTOM_DICTIONARY_PATH.exists() else DICTIONARY_PATH
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ============================================================
# Caveman Librarian
# Tidak pakai SLM.
# Tidak jawab lokal.
# Tidak panggil API besar.
# Cuma metadata, key, route.
# ============================================================



def extract_query_keys(question: str) -> list[str]:
    text = question.lower().strip()
    words = re.findall(r"[a-zA-Z0-9_\-]+", text)

    dictionary = load_dictionary()
    custom_stopwords = set(dictionary.get("stopwords", []))
    default_stopwords = {"apa", "itu", "yang", "di", "ke", "dari", "dan", "atau"}
    stopwords = custom_stopwords if custom_stopwords else default_stopwords

    keys = []
    for word in words:
        if word in stopwords:
            continue
        if len(word) < 2:
            continue
        keys.append(word)

    return keys


def detect_intent(question: str) -> str:
    q = question.lower()
    dictionary = load_dictionary()
    intents = dictionary.get("intents", {})

    for intent_key, keywords in intents.items():
        if any(x.lower() in q for x in keywords):
            return intent_key

    return "docs_lookup"


def expand_keys(question: str, query_keys: list[str]) -> list[str]:
    q = question.lower()
    expanded = []

    def add(items: list[str]):
        for item in items:
            if item not in expanded:
                expanded.append(item)

    dictionary = load_dictionary()
    expanded_rules = dictionary.get("expanded_keys", {})

    for key_pattern, add_items in expanded_rules.items():
        if key_pattern.lower() in q:
            add(add_items)

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