import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307").strip()
base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip() or None

print("=== LLM Configuration ===")
print(f"API Key present: {bool(api_key)}")
print(f"Model: {model}")
print(f"Base URL: {base_url}")
print("=========================\n")

client_kwargs = {"api_key": api_key}
if base_url:
    client_kwargs["base_url"] = base_url

try:
    client = Anthropic(**client_kwargs, timeout=60.0)
    print("Sending 'hello there' to LLM...")
    response = client.messages.create(
        model=model,
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "hello there"}],
        max_tokens=100
    )
    print("\n✅ Success! Response received:")
    print(response.content[0].text)
except Exception as e:
    import traceback
    print("\n❌ Error occurred:")
    traceback.print_exc()
