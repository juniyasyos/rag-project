# Panduan Penggunaan Project RAG

Dokumen ini menjelaskan cara menggunakan Project RAG pada sebuah *project target* serta panduan khusus bagi AI Agent untuk memanfaatkannya.

## 🛠️ Penggunaan Per-Project

Tool ini dirancang untuk dijalankan di root direktori *project target*. Beberapa contoh tipe project yang dapat didukung:
- Project **Laravel** (biasanya dokumentasi di `docs/` atau file README dan arsitektur di root).
- Project **Next.js** / Frontend (dokumentasi komponen).
- Project **Docker Platform** / Infrastruktur (dokumentasi deployment dan container).
- Project generic apa pun yang berbasis file markdown.

### Command Utama

Berikut adalah command utama yang tersedia dalam CLI `project-rag`. Jalankan command ini dari dalam direktori *project target*.

- `project-rag init`
  Membuat file konfigurasi awal `rag.yml` di dalam direktori saat ini.
- `project-rag sync`
  Menyalin (mirror) file-file dokumentasi `.md` dari folder sumber yang dikonfigurasi ke dalam direktori RAG lokal (`input/`).
- `project-rag ingest`
  Memecah file dari direktori `input/` menjadi beberapa *chunk* dan membuat struktur *graph* lokal tanpa database eksternal. Hasilnya disimpan dalam format JSON.
- `project-rag context`
  Menghasilkan/memperbarui file `AGENT_CONTEXT.md` berdasarkan hasil ingestion.
- `project-rag search "<keyword atau query>"`
  Melakukan pencarian di atas *knowledge base* RAG lokal untuk menemukan konteks yang spesifik dan relevan.
- `project-rag refresh`
  Merupakan command *shortcut* (gabungan) yang menjalankan `sync`, `ingest`, dan `context` secara berurutan.

### Kapan Perlu Menjalankan Refresh?

Jalankan `project-rag refresh` dalam kondisi-kondisi berikut agar *knowledge base* RAG tetap *up-to-date*:
- Setelah ada file dokumentasi `.md` yang ditambah, diubah, atau dihapus.
- Setelah struktur *source code* project dirombak secara besar-besaran (jika dokumentasi arsitektur diubah).
- Setelah ada **keputusan teknis baru** (misalnya menambahkan `DECISIONS.md` atau Architecture Decision Records).
- Setelah membuat *changelog* atau rilis baru.

---

## 🤖 AI Agent Usage Guide

Panduan berikut dikhususkan bagi AI Agent ketika ditugaskan untuk beroperasi pada *project target* yang menggunakan tool RAG ini. 

### Sebelum Mengerjakan Task:

1. **Baca File Konteks**: Pastikan untuk selalu membaca file `AGENT_CONTEXT.md` yang terletak di *storage root* (misal: `.ai/rag/AGENT_CONTEXT.md`) untuk mendapatkan pemahaman arsitektur dan status project secara cepat.
2. **Gunakan Pencarian**: Gunakan perintah `project-rag search "<query>"` untuk menemukan konteks spesifik yang dibutuhkan terkait tugas (contoh: *routing, database setup, environment variable*).
3. **Cek Kondisi Dokumentasi**: Jika dokumentasi project mengalami perubahan, jalankan command `project-rag refresh` agar konteks RAG tersinkronisasi.
4. **Hindari Pemindaian Penuh**: Jangan langsung melakukan *scan* atau *read* pada seluruh file di dalam repository/folder docs jika konteks yang disediakan RAG sudah cukup untuk menyelesaikan tugas.
5. **Usulkan Pembaruan Keputusan**: Jika Anda menemukan ada keputusan teknis baru atau arsitektur yang dibuat/diubah selama penyelesaian *task*, usulkan kepada *user* untuk memperbarui file dokumentasi (seperti `DECISIONS.md`) lalu lakukan *refresh*.

### Sebelum Mengedit File:

- Jalankan `ls` untuk memahami direktori saat ini.
- Cek struktur repository dan kenali *pattern* atau standar *code* yang berlaku.
- Cek file dokumentasi yang sudah ada sebelum membuat keputusan teknis baru.
- Cek `git status` untuk memahami file apa saja yang sedang berubah.
- **Jangan** menghapus file dokumentasi lama tanpa alasan yang jelas atau konfirmasi eksplisit dari *user*.
- Lakukan modifikasi (*update*) kode dan dokumen secara *incremental* (bertahap).
- Setelah tugas selesai, selalu tampilkan ringkasan (summary) dari perubahan yang dilakukan beserta daftar file yang dimodifikasi.
