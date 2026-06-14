# 📚 GraphRAG Project Documentation

Selamat datang di folder dokumentasi khusus untuk project **GraphRAG**.

Project ini adalah knowledge base berbasis Graph Retrieval-Augmented Generation (GraphRAG) yang digunakan untuk melakukan query, parsing, dan pengelolaan *knowledge graph* melalui CLI `rag-project`.

---

## 📋 Daftar Dokumen RAG

| Dokumen | Fungsi |
|---|---|
| [RAG_GUIDE.md](RAG_GUIDE.md) | Panduan lengkap tentang sistem GraphRAG (arsitektur, pola query) |
| [RAG_SCHEMA.md](RAG_SCHEMA.md) | Spesifikasi skema node dan edge untuk GraphRAG |
| [RAG_WORKFLOW.md](RAG_WORKFLOW.md) | Alur kerja dari proses ingest, chunking, hingga query |
| [RAG_USAGE_FOR_AGENT.md](RAG_USAGE_FOR_AGENT.md) | Panduan bagi AI Agent dalam menggunakan tool ini |
| [AI_AGENT_USAGE.md](AI_AGENT_USAGE.md) | Aturan utama untuk AI Agent saat memproses repository |

---

## 🛠 Instalasi & Penggunaan CLI

Project ini dibangun menggunakan Python (lihat `pyproject.toml`).

```bash
# Instalasi project (di environment Python Anda)
pip install -e .

# Cek command yang tersedia via CLI
rag-project --help
```

---

_Catatan: Direktori `docs/` ini **hanya** digunakan untuk dokumentasi internal project GraphRAG._
