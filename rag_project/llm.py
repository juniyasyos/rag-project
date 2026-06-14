import os
import sys

_llama_instance = None

def get_llama_instance(model_path):
    global _llama_instance
    if _llama_instance is None:
        try:
            from llama_cpp import Llama
            print(f"  🚀 Memuat model SLM lokal dari: {model_path} ...", file=sys.stderr)
            _llama_instance = Llama(
                model_path=model_path,
                n_ctx=1536,
                n_threads=4,
                verbose=False
            )
        except ImportError:
            print("  ⚠️  llama-cpp-python tidak terinstal.", file=sys.stderr)
            return None
    return _llama_instance

def get_local_model_path():
    local_model_path = os.getenv("LOCAL_MODEL_PATH", "").strip()
    if not local_model_path:
        default_path = os.path.join(os.getcwd(), "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
        if os.path.exists(default_path):
            local_model_path = default_path
    return local_model_path if (local_model_path and os.path.exists(local_model_path)) else None

def llm_librarian(question: str, context: str) -> str | None:
    local_model_path = get_local_model_path()
    if local_model_path:
        llm = get_llama_instance(local_model_path)
        if llm:
            try:
                system_prompt = """Anda adalah Pustakawan Sistem (Router). Tugas Anda BUKAN menjawab secara detail.
Keluarkan HANYA JSON valid. JANGAN cetak teks lain. Ganti nilai-nilai berikut dengan data SEBENARNYA berdasarkan konteks:
{
  "intent": "intent pertanyaan",
  "can_answer_locally": true_atau_false,
  "should_call_big_llm": true_atau_false,
  "confidence": 0.0_hingga_1.0,
  "relevant_docs": ["doc1"],
  "relevant_topics": ["topic1"],
  "answer_local": "jawaban singkat jika mudah",
  "reason": "alasan"
}"""
                user_prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}\n\nKeluarkan HANYA JSON valid."
                
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=250
                )
                return response["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"  ⚠️  Gagal memanggil SLM lokal: {e}", file=sys.stderr)
                return None
    return None

def llm_answer(question: str, context: str) -> str | None:
    local_model_path = get_local_model_path()
    if local_model_path:
        llm = get_llama_instance(local_model_path)
        if llm:
            try:
                system_prompt = (
                    "Anda adalah Pustakawan sistem lokal. Anda tidak bisa mengakses internet.\n"
                    "Jawab pertanyaan berdasarkan konteks yang diberikan secara akurat dan to the point."
                )
                user_prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}"
                
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  
                    max_tokens=250
                )
                return response["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"  ⚠️  Gagal memanggil SLM lokal: {e}", file=sys.stderr)
                return None

    # Fallback ke API eksternal (Anthropic-compatible) jika SLM lokal tidak ada
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "").strip()
    base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip() or None

    if not api_key or not model:
        return None

    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    try:
        client_kwargs = {"api_key": api_key}
        if base_url: client_kwargs["base_url"] = base_url
        client = Anthropic(**client_kwargs)
        response = client.messages.create(
            model=model,
            system="Anda adalah Pustakawan sistem. Jawab secara akurat, singkat, dan to the point berdasarkan konteks.",
            messages=[{"role": "user", "content": f"Konteks:\n{context}\n\nPertanyaan: {question}"}],
            temperature=0.1, max_tokens=250,
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️  LLM call failed: {e}", file=sys.stderr)
        return None

def llm_big_answer(question: str, context: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "").strip()
    base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip() or None

    if not api_key or not model:
        print("  ⚠️  Kredensial LLM Besar (Anthropic/Deepseek) tidak ditemukan di .env", file=sys.stderr)
        return None

    try:
        from anthropic import Anthropic
    except ImportError:
        print("  ⚠️  anthropic package not installed.", file=sys.stderr)
        return None

    try:
        client_kwargs = {"api_key": api_key}
        if base_url: client_kwargs["base_url"] = base_url
        client = Anthropic(**client_kwargs)
        
        print(f"  🌐 Memanggil LLM Besar ({model}) ...", file=sys.stderr)
        
        response = client.messages.create(
            model=model,
            system="Anda adalah asisten AI yang ahli dalam rekayasa perangkat lunak. Jawab pertanyaan pengguna secara detail dan analitis berdasarkan konteks yang diberikan.",
            messages=[{"role": "user", "content": f"Konteks Ringkas:\n{context}\n\nPertanyaan: {question}\n\nTolong berikan penjelasan detail, analisa, atau instruksi berdasarkan konteks di atas."}],
            temperature=0.3, max_tokens=2000,
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️  Big LLM call failed: {e}", file=sys.stderr)
        return None
