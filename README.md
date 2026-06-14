# Project RAG

**Project RAG** adalah sebuah package/tool generic untuk membangun *Retrieval-Augmented Generation* (RAG) secara lokal yang ringan dan berbasis file. Tool ini dirancang untuk dapat digunakan oleh berbagai macam project untuk membantu AI agent memahami konteks project dengan cepat dan efisien.

## 🌟 Problem yang Diselesaikan

AI agent sering kali perlu membaca banyak dokumentasi untuk memahami konteks sebuah project. Memberikan seluruh file sumber atau folder dokumentasi (`docs/`) secara langsung sangat tidak efisien dan dapat dengan mudah melampaui batas token *context window* pada LLM.

Tool ini menyelesaikan masalah tersebut dengan mengekstrak dokumen markdown menjadi *chunks* yang terstruktur dan membangun *knowledge graph* sederhana secara lokal. AI agent kemudian dapat mencari konteks spesifik yang relevan tanpa harus membaca seluruh file dokumentasi project.

## 🔄 Flow Sederhana

Tool ini bekerja dengan alur yang sangat sederhana:

`docs/source files` → `sync` → `ingest` → `index/graph` → `agent context`

1. **Sync**: Mengambil file markdown dari folder dokumentasi project target.
2. **Ingest**: Memecah file menjadi *chunks* dan mengekstrak relasi antar entitas (graph).
3. **Index/Graph**: Menyimpan hasil pemrosesan secara lokal berbasis file (JSON).
4. **Agent Context**: Menghasilkan ringkasan dan antarmuka pencarian agar AI agent mudah menggunakannya.

## 🚀 Quick Start

### 1. Install secara Lokal

Clone repository package ini dan install secara global atau di *virtual environment*:

```bash
pip install -e .
```

### 2. Setup di Project Target

Masuk ke direktori project target apa pun yang ingin diindeks (misalnya: project aplikasi web, service backend, dll).

```bash
cd /path/to/target-project
```

Buat file konfigurasi `rag.yml` di root direktori project target. Contoh `rag.yml`:

```yaml
source_dir: "./docs"
output_dir: "./.ai/rag"
```

### 3. Build RAG & Cari Konteks

Jalankan serangkaian perintah berikut dari dalam direktori project target:

```bash
# Menyalin dokumentasi ke direktori input RAG
project-rag sync

# Memecah dokumen menjadi chunks & membuat knowledge graph
project-rag ingest

# Menghasilkan file AGENT_CONTEXT.md untuk panduan awal AI agent
project-rag context

# Mencari konteks spesifik
project-rag search "cara setup database lokal"
```

## 📁 Contoh Struktur Project Target

Package RAG akan menyimpan seluruh data *index* dan *cache* di dalam *storage root* (misal: folder `.ai/rag/`) dari project target. Data pengguna sama sekali **tidak** disimpan di dalam package `project-rag` itu sendiri.

```text
target-project/
├── docs/                   # Folder dokumentasi asli milik project
│   ├── architecture.md
│   └── setup.md
├── src/                    # Source code project target
├── rag.yml                 # Konfigurasi RAG untuk project ini
└── .ai/
    └── rag/                # Folder penyimpanan hasil RAG (output_dir)
        ├── input/          # Salinan file markdown yang akan diproses
        ├── output/
        │   ├── chunks.json # Data potongan dokumen
        │   └── graph.json  # Data entitas & relasi
        └── AGENT_CONTEXT.md # File yang harus dibaca pertama kali oleh AI agent
```

## 🤖 Cara AI Agent Memakai File Hasil Context

AI agent yang ditugaskan pada project target harus membaca file hasil context terlebih dahulu.

1. Agent melihat file `.ai/rag/AGENT_CONTEXT.md`. File ini berisi ringkasan struktur RAG dan direktori project.
2. Jika butuh tahu cara setup database, agent dapat menjalankan perintah `project-rag search "database setup"` daripada membaca seluruh dokumen di `/docs`.
3. Agent menggunakan hasil pencarian untuk melanjutkan tugasnya dengan konteks yang tepat sasaran.

## 📚 Dokumentasi Lanjutan

- [Struktur Internal Package (STRUCTURE.md)](docs/STRUCTURE.md)
- [Panduan Penggunaan (USAGE.md)](docs/USAGE.md)
- [Roadmap Pengembangan (ROADMAP.md)](docs/ROADMAP.md)
