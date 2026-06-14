import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# =========================
# Konfigurasi Model
# =========================
REPO_ID = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"

# Simpan model di folder project
MODEL_DIR = "models"
LOCAL_MODEL_PATH = os.path.join(MODEL_DIR, FILENAME)

SYSTEM_PROMPT = """
Anda adalah chatbot AI lokal berbahasa Indonesia.

Aturan penting:
- Anda berjalan secara lokal menggunakan model GGUF.
- Anda TIDAK punya akses internet.
- Anda TIDAK bisa membaca file, folder, database, atau web kecuali user memberikan isi datanya langsung.
- Jangan mengaku bisa browsing, mengunduh, menjalankan command, atau mengecek sistem.
- Jika tidak tahu, jawab jujur: "Saya tidak tahu dari konteks yang tersedia."
- Jawab ringkas, jelas, dan tidak mengarang kemampuan.
"""

# =========================
# Cek Model Lokal
# =========================
os.makedirs(MODEL_DIR, exist_ok=True)

if os.path.exists(LOCAL_MODEL_PATH):
    print(f"✅ Model lokal ditemukan: {LOCAL_MODEL_PATH}")
    model_path = LOCAL_MODEL_PATH
else:
    print(f"📥 Model belum ada di lokal.")
    print(f"📥 Mengunduh model {FILENAME} dari {REPO_ID}...")

    model_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False
    )

    print(f"✅ Model berhasil diunduh ke: {model_path}")

print("🚀 Memuat model ke memori...")

llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# =========================
# Memory Chat
# =========================
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT.strip()
    }
]

print("\n💬 Chatbot siap!")
print("Ketik pesan kamu.")
print("Ketik 'exit', 'quit', atau 'keluar' untuk berhenti.")
print("-" * 50)

# =========================
# Loop Chatbot
# =========================
while True:
    user_input = input("\n👤 Kamu: ").strip()

    if user_input.lower() in ["exit", "quit", "keluar"]:
        print("\n👋 Chat selesai.")
        break

    if not user_input:
        continue

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = llm.create_chat_completion(
        messages=messages,
        temperature=0.3,
        max_tokens=300
    )

    assistant_reply = response["choices"][0]["message"]["content"].strip()

    print("\n🤖 Bot:")
    print(assistant_reply)

    messages.append({
        "role": "assistant",
        "content": assistant_reply
    })

    # Biar history tidak terlalu panjang
    # System prompt tetap disimpan, chat lama dipotong
    if len(messages) > 12:
        messages = [messages[0]] + messages[-10:]