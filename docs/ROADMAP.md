# Roadmap Pengembangan Project RAG

Pengembangan **Project RAG** dirancang untuk dilakukan secara bertahap (incremental) agar sistem tidak menjadi terlalu kompleks dan tetap fokus pada solusi ringan untuk kebutuhan *AI Agent*.

Saat ini, kita fokus pada solusi lokal berbasis file yang tidak membutuhkan *external database* (seperti Neo4j, Vector DB, dll), agar setup di berbagai *project target* tetap mulus dan sederhana.

## 🛣️ Tahapan Pengembangan

### Phase 1: Local File-based RAG *(Current)*
Fokus pada fungsionalitas inti untuk *ingestion* dan *retrieval* dasar.
- Ekstraksi dokumen markdown menjadi *chunks* secara lokal.
- Penyimpanan *index* dan *graph* sederhana menggunakan file JSON.
- Perintah CLI dasar: `sync`, `ingest`, dan `search`.
- Pemisahan total antara data *project target* dengan logika internal package RAG.
- **Prioritas Terdekat**: Memastikan CLI berjalan lancar, stabil, dan dapat diandalkan untuk skenario penggunaan di berbagai tipe project target.

### Phase 2: Better Graph Relation
Penyempurnaan pada algoritma ekstraksi relasi antar entitas.
- Pattern matching yang lebih baik untuk menemukan relasi implisit dalam teks dokumentasi.
- Deduplikasi node/edge yang lebih presisi pada algoritma graf.
- Dukungan *weight* atau scoring pada *edge* untuk memprioritaskan hasil pencarian yang saling terkait erat.

### Phase 3: CLI Lebih Nyaman
Meningkatkan *developer experience* (DX) saat menggunakan `project-rag`.
- Peningkatan format output (berwarna, berbentuk tabel untuk *search*).
- Interactive mode (misalnya prompt konfirmasi atau navigasi search results).
- Command `refresh` yang mendeteksi perubahan file (*diff*) sehingga tidak perlu *rebuild* seluruh *chunks* dari awal (incremental ingest).

### Phase 4: Multi-Project Registry
Mendukung pengelolaan beberapa project dalam satu lingkungan atau mesin.
- Menyimpan *registry* project-project mana saja yang memiliki *knowledge base* RAG.
- Perintah global untuk *refresh* semua project secara otomatis (via *cron* atau *background worker*).

### Phase 5: Plugin / Agent Integration
Mempermudah ekosistem AI Agent untuk langsung memanfaatkan output RAG ini.
- Standarisasi format `AGENT_CONTEXT.md` agar mudah diparsing oleh berbagai model bahasa (LLM).
- *Library binding* atau API minimalis (Python/Node.js) sehingga *script agent* dapat memanggil fungsi pencarian tanpa harus via CLI (subprocess).

### Phase 6: Optional Vector Database
Menambahkan dukungan fitur pencarian berbasis vektor *hanya jika sangat diperlukan*.
- Implementasi embedding lokal atau integrasi API embedding ringan.
- Opsi untuk menyimpan *chunks* di database vektor eksternal (seperti ChromaDB atau Qdrant) untuk organisasi yang memiliki kebutuhan RAG skala *enterprise*.
- Fitur ini akan selalu bersifat **opsional**, *fallback* utamanya akan tetap *file-based*.

## 🚫 Fitur yang Belum Perlu Dibuat (Out of Scope untuk Saat Ini)

Agar pengembangan tetap terarah pada *file-based RAG* yang ringan, beberapa fitur berikut secara sadar **ditunda atau tidak dikembangkan** pada saat ini:
- **Penggunaan Neo4j atau Graph DB eksternal**. (JSON graph file sudah cukup untuk skala ringan).
- **Multi-agent orchestration system**. (Tool ini hanya sebagai *provider* konteks, bukan *agent runner*).
- **Vector DB terdedikasi** (sebagai *default*). Phase-phase awal cukup dengan keyword-based / local semantic search.
- Sistem UI web (*dashboard*) yang terlalu kompleks.
