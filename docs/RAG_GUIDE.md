# Panduan GraphRAG untuk Dokumentasi Project

Panduan lengkap tentang sistem **GraphRAG** (Graph Retrieval-Augmented Generation)
untuk query knowledge base project ini.

> **Khusus AI Agents:** Wajib membaca alur kerja dan pola penggunaan RAG di [RAG_USAGE_FOR_AGENT.md](RAG_USAGE_FOR_AGENT.md).

---

## 📋 Ringkasan

GraphRAG adalah sistem knowledge base ringan yang:

1. **Sync** — Menyalin dokumentasi dari `docs/` ke `docs/ai-agent/rag/input/`
2. **Ingest** — Memecah dokumen jadi chunk + mengekstrak grafik pengetahuan
3. **Query** — Menjawab pertanyaan dengan keyword scoring + LLM opsional (Claude)

**Tujuan**: Memudahkan developer (manusia dan AI) untuk mencari informasi
tentang project tanpa harus membaca puluhan file dokumentasi manual.

---

## 📁 Struktur

```txt
project/
├── docs/                          # Dokumentasi sumber (markdown)
│   ├── *.md                       # Dokumentasi utama
│   ├── releases/                  # Release notes
│   ├── upgrade/                   # Panduan upgrade/migrasi
│   └── ai-agent/
│       └── rag/
│           ├── input/             # Hasil copy dari docs/
│           ├── output/            # Output chunks.json & graph.json
│           └── config.yml         # Konfigurasi path
├── rag/                           # Source code / Python module (rag_project)
│   ├── scripts/
│   │   ├── sync_docs.py           # Sync markdown
│   │   ├── ingest.py              # Chunking + graph extraction
│   │   └── query.py               # Query CLI
│   ├── .env.example               # Konfigurasi API key
│   └── README.md                  # Dokumentasi teknis RAG
├── AGENTS.md                      # Daftar AI agents & tooling
└── CHANGELOG.md                   # Catatan perubahan
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Sync Dokumentasi

```bash
rag-project sync
```

Perintah ini membersihkan `docs/ai-agent/rag/input/` dan menyalin semua file `.md` dari `docs/` dan
`docs/releases/` (kecuali template) ke `docs/ai-agent/rag/input/`.

### 3. Ingest

```bash
rag-project ingest
```

Membaca semua markdown dari `docs/ai-agent/rag/input/` dan menghasilkan:

- **chunks.json** — 400+ chunk dokumen berbasis heading
- **graph.json** — 30+ node entitas + 10+ edge relasi

### 4. Query

```bash
# Retrieval-only (tanpa LLM)
rag-project query "apa itu modular monolith?"

# Dengan LLM (copy .env dulu)
cp rag/.env.example rag/.env
# Isi ANTHROPIC_API_KEY dan ANTHROPIC_MODEL
rag-project query "command apa untuk setup development?"
```

---

## 🔄 Rebuild

Jalankan setiap kali dokumentasi berubah:

```bash
rag-project rebuild
```

---

## 📤 Output

### chunks.json

Array chunk dengan format:

```json
{
  "id": "chunk-0001",
  "source_file": "PROJECT_STRUCTURE.md",
  "heading": "app/ — Source Code",
  "chunk_index": 1,
  "content": "| Path | Fungsi | Catatan |..."
}
```

### graph.json

Object dengan nodes dan edges:

```json
{
  "nodes": [
    { "id": "my_project", "type": "Project", "label": "MyProject", "source": "..." }
  ],
  "edges": [
    { "from": "filament", "to": "nginx", "type": "exposed_by", "source": "..." }
  ]
}
```

---

## 🧠 Cara Kerja

### Chunking
1. Baca setiap file `.md`
2. Pecah berdasarkan heading markdown (`#`, `##`, dst.)
3. Jika > 2000 karakter, pecah per paragraf
4. Setiap chunk punya ID unik (`chunk-0001`)

### Graph Extraction
1. Pattern matching dengan kata kunci untuk entity types
2. Entity types: Project, App, Service, Module, Command, Port, Container, Env, KnownIssue, Decision, Release
3. Relasi: uses, exposed_by, has_port, contains, defined_in, related_to, affects, includes
4. Deduplikasi otomatis — node yang sama tidak dibuat dua kali

### Query
1. Tokenize pertanyaan
2. Score chunk berdasar keyword overlap + heading boost + source boost
3. Cari node/edge graph relevan
4. (Opsional) Kirim konteks ke Claude untuk jawaban natural language

---

## ⚠️ Keterbatasan

1. **Pattern-based graph** — hanya entitas eksplisit dengan kata kunci
2. **Source code tidak diindeks** — hanya markdown di `docs/`
3. **Keyword scoring** — tanpa semantic search / embedding
4. **LLM opsional** — tanpa API key, hanya retrieval
5. **No auto-rebuild** — perlu manual sync_docs + ingest
6. **Bahasa campuran** — dokumentasi ID/EN, query keduanya

---

## 🔮 Next Improvement

- [ ] Semantic chunk search dengan embedding (sentence-transformers)
- [ ] Indeks AI agent docs (`docs/ai-agents/`)
- [ ] Graph extraction dengan LLM untuk akurasi lebih tinggi
- [ ] UI Streamlit untuk browsing knowledge base
- [ ] Auto-rebuild via git hook
- [ ] Caching query untuk pertanyaan berulang
- [ ] Integrasi Laravel Artisan command
