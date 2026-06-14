import os
import sys

def llm_answer(question: str, context: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "").strip()
    base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip() or None

    if not api_key or not model:
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
        response = client.messages.create(
            model=model,
            system=(
                "Anda adalah asisten yang menjawab pertanyaan tentang project SIIMUT.\n"
                "Jawab dalam bahasa Indonesia berdasarkan konteks."
            ),
            messages=[{"role": "user", "content": f"Konteks:\n{context}\n\nPertanyaan: {question}"}],
            temperature=0.3, max_tokens=1000,
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️  LLM call failed: {e}", file=sys.stderr)
        return None
