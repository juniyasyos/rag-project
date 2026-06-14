# Project Intelligence RAG

**Project Intelligence RAG** adalah sebuah package/tool generic untuk membangun *Retrieval-Augmented Generation* (RAG) secara lokal yang ringan dan berbasis file. Tool ini dirancang untuk dapat digunakan oleh berbagai macam project untuk membantu AI agent memahami konteks project secara keseluruhan, bukan hanya dari dokumentasi, melainkan juga dari source code dan konfigurasi.

## 🌟 Problem yang Diselesaikan

AI agent sering kali perlu membaca banyak dokumentasi dan source code untuk memahami arsitektur sebuah project. Mengirim seluruh file source atau folder dokumentasi secara langsung sangat tidak efisien dan dapat dengan mudah melampaui batas token *context window* pada LLM.

Tool ini menyelesaikan masalah tersebut dengan melakukan *multi-domain scanning* (docs, database, routes, services, models, config/docker) dan membangun *knowledge graph* secara lokal. AI agent dapat mencari entitas (Table, Column, Migration, Route, Controller, Service, Model, dsb) atau konteks spesifik tanpa harus membaca seluruh file project.

## 🔄 Flow Sederhana

Tool ini bekerja dengan alur yang modular:

`project files` → `scan/sync/ingest` → `index/graph` → `agent context`

1. **Scan & Sync**: Memindai berbagai domain di project (docs, app/Models, app/Services, database/migrations, routes, config) tanpa dependensi berat.
2. **Ingest**: Mengekstrak entitas dan memecah konten menjadi *chunks* serta membangun *knowledge graph* sederhana.
3. **Index/Graph**: Menyimpan hasil pemrosesan secara lokal berbasis file (JSON) di dalam folder `.ai/rag` milik project target.
4. **Agent Context**: Menyediakan antarmuka CLI yang dapat digunakan AI agent untuk querying atau melihat struktur graph.

## 🚀 Quick Start

### 1. Install secara Lokal

Clone repository package ini dan install:

```bash
pip install -e .
```

### 2. Setup di Project Target

Masuk ke direktori project target apa pun yang ingin diindeks:

```bash
cd /path/to/target-project
```

### 3. Build RAG & Cari Konteks

Jalankan perintah berikut dari dalam direktori project target:

```bash
# Melakukan scanning secara menyeluruh (multi-domain: code, config, docs)
rag-project scan

# Menyalin markdown manual jika perlu
rag-project sync
rag-project ingest

# Gabungan scan, sync, ingest (rebuild ulang)
rag-project refresh

# Menghasilkan context string untuk agent
rag-project context "database setup"

# Melakukan query dengan mode SLM (Pustakawan Router)
rag-project query "jelaskan project siimut" --mode librarian

# Melakukan query agar dijawab lokal jika sederhana
rag-project query "apa command menjalankan project?" --mode local

# Mengeluarkan prompt yang siap dikirim ke LLM besar (Handoff)
rag-project query "analisa arsitektur siimut" --mode handoff

# Mencari file/chunk spesifik (bisa difilter berdasarkan domain)
rag-project search "user authentication" --domain services

# Melihat keseluruhan atau mencari sebagian dari Knowledge Graph
rag-project graph "service"

# Menginspeksi satu entitas Node secara detail
rag-project inspect "model-user"
```

## 📁 Struktur Penyimpanan (di Project Target)

Package ini menyimpan seluruh data *index* dan *cache* di dalam *storage root* `.ai/rag/` dari project target. Data pengguna sama sekali **tidak** disimpan di dalam package ini.

```text
target-project/
├── .ai/
│   └── rag/                # Folder penyimpanan hasil RAG (output_dir)
│       ├── input/          # Salinan file markdown (jika disinkronisasi manual)
│       └── output/
│           ├── chunks.json # Data potongan dokumen & kode
│           └── graph.json  # Data entitas & relasi (Table, Route, Model, Service, dll)
├── docs/                   # Folder dokumentasi asli milik project
├── app/                    # Folder kode aplikasi
└── config/                 # Folder konfigurasi
```

## 🤖 Cara AI Agent Memakai File Hasil Context

AI agent dapat berinteraksi dengan tool ini untuk mengeksplorasi arsitektur project:

1. **Pencarian Global**: `rag-project search "jwt"` untuk melihat semua chunk code & docs terkait JWT.
2. **Pencarian Spesifik Domain**: `rag-project search "create user" --domain routes` untuk membatasi pencarian di API/Web routes.
3. **Graph Exploration**: `rag-project graph "model-user"` untuk melihat apa saja yang berhubungan dengan model User.
4. **Detail Node**: `rag-project inspect "route-get-api-users"` untuk melihat relasi persis.

### Mode Query (SLM Lokal)
AI agent juga dapat memanggil RAG dengan SLM lokal (sebagai *Pustakawan* atau *Router*) menggunakan flag `--mode`:
- `--mode librarian` (default): Menghasilkan output **JSON murni** yang merangkum niat pengguna (intent), dokumen relevan, dan mengambil keputusan apakah pertanyaan cukup dijawab lokal atau perlu diserahkan ke LLM besar. Sangat berguna sebagai *preprocessing/routing* untuk agen AI Anda!
- `--mode local`: SLM akan mencoba menjawab langsung pertanyaan tersebut berdasarkan konteks RAG.
- `--mode handoff`: Mengeluarkan prompt teks (Prompt template) yang sudah dirangkai dari pertanyaan *user* dan dokumen RAG terpilih, siap untuk disalin-tempel/dikirimkan ke LLM besar (seperti GPT-4 atau Claude).

## 📚 Dokumentasi Lanjutan

- [Struktur Internal Package (STRUCTURE.md)](docs/STRUCTURE.md)
- [Panduan Penggunaan (USAGE.md)](docs/USAGE.md)
- [Roadmap Pengembangan (ROADMAP.md)](docs/ROADMAP.md)
