# Project Intelligence RAG (SIIMUT Caveman Librarian)

**Project Intelligence RAG** adalah sebuah *CLI tool* berbasis Python yang dirancang khusus sebagai **"Pustakawan"** untuk memetakan arsitektur proyek Laravel secara lokal. Tool ini mengekstrak entitas dan relasi dari *source code* dan dokumentasi ke dalam *Knowledge Graph* berformat JSON, menghemat **hingga 99%** konsumsi *context window* LLM.

## 🌟 Desain Arsitektur & Filosofi

Tool ini beroperasi dengan prinsip **"Caveman Librarian"** — murni sebagai mesin *retrieval & indexing* tanpa menggunakan LLM lokal untuk menghasilkan jawaban (NLG di-disable). Semua pemrosesan berbasis *pattern matching* (Regex via YAML) bukan AST parsing, sehingga sangat cepat dan ringan.

**Karakteristik Kunci:**
- **Zero Database:** Hanya menggunakan `chunks.json` dan `graph.json` lokal. Tidak ada dependensi Neo4j atau Vector DB.
- **Multi-Domain Scanning:** Mendeteksi 20+ domain Laravel (Models, Services, Controllers, Routes, Migrations, Policies, Filament, Livewire, Console Commands, dll).
- **Cross-Domain Relations:** Mampu mendeteksi injeksi dependensi (`depends_on`) dan penggunaan model lintas domain (`uses_model`, `authorizes`, `seeds`).
- **Stateless:** Kode *parser* terpisah dari penyimpanan data (yang diletakkan di `.ai/rag/output/` pada direktori proyek target).

## 🚀 Performa & Efisiensi Konteks

Dibandingkan dengan pencarian konvensional (Grep) yang memuat seluruh *source code* ke dalam *context window* LLM, tool ini secara ekstrem meringkas muatan dengan berfokus menyuplai **metadata arsitektur dan relasi**:

| Metrik | Pencarian Konvensional (Grep) | Pendekatan Pustakawan (RAG Project) |
|--------|------------------|-------------------|
| **Payload ke LLM** | Menyuapkan seluruh isi *file* kode mentah. | Menyuapkan ringkasan relasi (node & *edges*). |
| **Kebutuhan Token** | Sangat besar (bisa > 20.000 token). | Sangat kecil (dibatasi ketat ~150 hingga 500 token). |
| **Fungsi Ideal** | Analisis logika fungsi spesifik & *debugging*. | Pemetaan arsitektur & *impact analysis* tahap awal. |

*Kesimpulan: Tool ini memangkas konsumsi token di fase awal (discovery) dengan membuang logika kode dan berfokus murni pada pemetaan struktur.*

## 🛠️ Instalasi & Setup

1. **Install Package (Global/Venv):**
```bash
cd rag-project
pip install -e .
```

2. **Masuk ke Target Project (Laravel):**
```bash
cd /path/to/laravel-project
```

3. **Build Knowledge Graph:**
```bash
# Melakukan scanning code & ingest docs secara penuh
rag-project refresh
```

## 🤖 Perintah CLI (Untuk AI Agent & Developer)

Tool ini berjalan dari *root* direktori proyek target.

### 1. Eksplorasi Arsitektur (Graph)
```bash
# Menampilkan statistik jumlah node/edge di proyek
rag-project graph stats

# Mencari node berdasarkan keyword (contoh: "user")
rag-project graph "user"

# Melihat KESELURUHAN relasi (inbound & outbound) dari satu entitas
rag-project inspect "model-user"
rag-project inspect "service-laporanimutservice"
```

### 2. Keyword & Intent-Based Querying
```bash
# Mendapatkan konteks terstruktur untuk AI Agent (menggunakan intent routing & keyword scoring)
rag-project query --intent architecture_analysis --subject "Laporan Imut"

# Intent yang tersedia:
# project_overview, architecture_analysis, service_lookup, data_model_lookup,
# command_lookup, api_reference, troubleshooting, docs_lookup
```

### 3. Pencarian Raw
```bash
# Mencari string spesifik dalam output RAG
rag-project search --intent docs_lookup --subject "authentication"
```

## 📁 Struktur Data Graph

Output disimpan di `target-project/.ai/rag/output/`.

- **Nodes (`graph.json`):** Entitas seperti `Table`, `Model`, `Controller`, `Service`, `Route`, `Policy`, `FilamentResource`.
- **Edges (`graph.json`):** Relasi seperti `has_column`, `uses_model`, `depends_on`, `handled_by`, `creates_table`, `authorizes`, `seeds`.
- **Chunks (`chunks.json`):** Pecahan dokumentasi *markdown* yang telah di-index.

---
*Dikembangkan secara khusus untuk menganalisis arsitektur monolit Laravel kompleks seperti SIIMUT.*
