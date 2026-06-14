# Struktur Package & Arsitektur

Dokumen ini menjelaskan struktur internal dari tool Project RAG, serta pemisahan (separation of concerns) antara *package/tool code* dengan data milik *project target*.

## 📂 Struktur Internal Package RAG

Source code package ini sendiri dipisah berdasarkan modul dan fungsionalitas:

```text
rag-project/
├── rag_project/
│   ├── __init__.py
│   ├── cli.py             # Handler CLI utama (init, sync, ingest, dll)
│   ├── config.py          # Config loader untuk membaca rag.yml
│   ├── sync.py            # Logika sinkronisasi file
│   ├── ingest.py          # Logika pemecahan chunk & ekstrak graph
│   ├── graph.py           # Struktur data / index untuk graph
│   ├── search.py          # Modul pencarian keyword / basic search
│   └── context.py         # Context generator (pembuat AGENT_CONTEXT.md)
├── scripts/               # Script utilitas (jika ada)
├── docs/                  # Dokumentasi tool ini sendiri
├── README.md
├── pyproject.toml
└── requirements.txt
```

### Fungsi Modul-Modul Utama

- **CLI (`cli.py`)**: Menangani semua interaksi terminal (command-line interface). Mengekspos perintah seperti `init`, `sync`, `ingest`, `context`, dan `search`.
- **Config Loader (`config.py`)**: Bertugas menemukan dan membaca file konfigurasi `rag.yml` yang ada pada *project target*.
- **Sync (`sync.py`)**: Menyalin (mirroring) file markdown `.md` dari `docs folder` *project target* menuju folder `input/` pada storage RAG.
- **Ingest (`ingest.py`)**: Memproses file dari folder `input/`, memecahnya menjadi chunks terstruktur, serta mengekstrak entitas dan relasinya.
- **Graph / Index (`graph.py`)**: Mengelola penyimpanan hasil chunk dan graph ke dalam bentuk file JSON yang ringan tanpa butuh database eksternal.
- **Search (`search.py`)**: Berisi logika pencarian berbasis keyword (atau embeddings, jika diaktifkan nanti) untuk menemukan chunk dan graph yang relevan dari data *index*.
- **Context Generator (`context.py`)**: Bertugas menghasilkan file `AGENT_CONTEXT.md` sebagai ringkasan bagi AI agent di dalam folder penyimpanan project target.

## 🧱 Pemisahan Arsitektur

Agar Project RAG dapat dipakai oleh berbagai project secara generik, terdapat tiga domain utama yang sepenuhnya dipisah:

### 1. Package / Tool Code
Ini adalah source code dari RAG itu sendiri (repository ini). Hanya berisi logika (*engine*), tanpa menyimpan state atau data dokumentasi project apa pun. Code ini diinstall secara global atau di dalam virtual environment melalui `pip`.

### 2. Project Target
Ini adalah direktori source code atau project tempat tool ini digunakan (misal: aplikasi web Laravel, backend Node.js, atau platform Docker). Project target ini hanya perlu menyiapkan `docs folder` dan file `rag.yml`. Tidak ada source code RAG di dalam project target.

### 3. Storage / Index / Cache / Output
Seluruh hasil ekstraksi (*chunks*, *graph*, salinan file `input`, dan file *context*) akan disimpan di dalam **Storage Root** (umumnya diletakkan di dalam folder target seperti `.ai/rag/` atau `.rag/`).

Dengan pemisahan ini, package RAG akan selalu "bersih" (*stateless*), dan data milik *project target* tidak tercampur. Hal ini memungkinkan package RAG dipakai di banyak project sekaligus dalam komputer yang sama.
