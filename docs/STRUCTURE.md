# Struktur Package & Arsitektur

Dokumen ini menjelaskan struktur internal dari tool Project Intelligence RAG, serta pemisahan (separation of concerns) antara *package/tool code* dengan data milik *project target*.

## 📂 Struktur Internal Package RAG

Source code package ini sendiri dipisah berdasarkan modul dan fungsionalitas:

```text
rag-project/
├── rag_project/
│   ├── __init__.py
│   ├── cli.py             # Handler CLI utama (init, sync, ingest, scan, dll)
│   ├── config.py          # Config loader untuk membaca konfigurasi project
│   ├── sync.py            # Logika sinkronisasi file manual
│   ├── ingest.py          # Logika pemecahan chunk & ekstrak graph (markdown)
│   ├── scanner.py         # Multi-domain scanner (database, routes, services, dll)
│   ├── graph.py           # Struktur data / index untuk graph entities
│   └── query.py           # Modul pencarian keyword dan context generation
├── docs/                  # Dokumentasi tool ini sendiri
├── README.md
├── pyproject.toml
└── requirements.txt
```

### Fungsi Modul-Modul Utama

- **CLI (`cli.py`)**: Menangani semua interaksi terminal (command-line interface). Mengekspos perintah seperti `scan`, `sync`, `ingest`, `context`, `inspect`, dan `search`.
- **Config Loader (`config.py`)**: Bertugas membaca konfigurasi environment.
- **Scanner (`scanner.py`)**: Melakukan pemindaian (scanning) ke berbagai domain di project (seperti app/Models, app/Services, database/migrations, routes, dsb) untuk mengekstrak struktur kode dan menjadikannya entitas graph (Table, Model, dsb).
- **Sync (`sync.py`)**: Menyalin (mirroring) file markdown dari docs folder menuju input folder lokal.
- **Ingest (`ingest.py`)**: Memproses file markdown, memecahnya menjadi chunks terstruktur, serta mengekstrak entitas.
- **Graph / Index (`graph.py`)**: Mengelola logika relasi graph secara dinamis tanpa hardcode.
- **Query / Search (`query.py`)**: Berisi logika pencarian berbasis keyword untuk menemukan chunk dan graph relevan dari data *index*, dengan fitur filter per domain. Serta dapat me-return konteks murni via `run_context`.

## 🧱 Pemisahan Arsitektur

Agar Project Intelligence RAG dapat dipakai oleh berbagai project secara generik, terdapat tiga domain utama yang sepenuhnya dipisah:

### 1. Package / Tool Code
Ini adalah source code dari RAG itu sendiri (repository ini). Hanya berisi logika (*engine*), tanpa menyimpan state atau data dokumentasi project apa pun. Code ini diinstall secara global atau di dalam virtual environment melalui `pip`.

### 2. Project Target
Ini adalah direktori source code atau project tempat tool ini digunakan (misal: aplikasi web Laravel, backend Node.js, atau platform Docker). Tool akan langsung memindai folder seperti `app/`, `database/`, `routes/`, `config/` dan mengekstrak entitas tanpa harus mengubah source code project target.

### 3. Storage / Index / Cache / Output
Seluruh hasil ekstraksi (*chunks*, *graph*, salinan file `input`) akan disimpan di dalam **Storage Root** (yaitu folder `.ai/rag/` di root project target).

Dengan pemisahan ini, package RAG akan selalu "bersih" (*stateless*), dan data milik *project target* tidak tercampur. Hal ini memungkinkan package RAG dipakai di banyak project dengan struktur file index yang terisolasi per project.
