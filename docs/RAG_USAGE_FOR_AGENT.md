# Panduan Penggunaan RAG untuk AI Agent

Dokumen ini berisi panduan wajib bagi AI Agent (termasuk Anda) saat berinteraksi dan membantu pengembangan pada project ini.

---

## 1. Aturan Utama

Setiap AI Agent wajib mematuhi aturan berikut sebelum melakukan tindakan modifikasi atau eksplorasi:
- **Jangan langsung scan seluruh repo.** Jangan pernah menggunakan perintah pencarian skala penuh pada keseluruhan source code tanpa konteks.
- **Baca `AGENTS.md` dulu.** Pastikan memahami mode dan peran agen pada sistem.
- **Query RAG dulu.** Untuk mencari tahu struktur, modul, atau konteks sistem, selalu tanyakan pada RAG (knowledge base) terlebih dahulu.
- **Baru baca source code yang relevan.** Setelah mendapatkan ID modul atau path yang relevan dari RAG, baru gunakan perintah baca file pada source code.
- **Jangan scan folder yang dilarang:** `vendor/`, `node_modules/`, `storage/`, `bootstrap/cache/`, `public/build/`.
- **Tulis "Needs Verification".** Jika menemukan informasi dalam RAG atau source code yang meragukan atau belum pasti, gunakan tag `Needs Verification`.
- **Update docs & Rebuild RAG.** Jika terdapat perubahan arsitektur, keputusan penting, atau penambahan modul, wajib memperbarui dokumentasi dan me-rebuild RAG.

---

## 2. Kapan Harus Menggunakan RAG vs Source Code

### Wajib Pakai RAG
- Saat pertama kali diberikan *task* yang melibatkan bisnis logic besar atau arsitektur (contoh: "Tolong perbaiki Daily Report").
- Saat ingin mengetahui *Known Issues* atau bug yang sudah dicatat sebelumnya.
- Saat mencari relasi antara sebuah *Service*, *Command*, dan *Modul*.
- Saat mereviu *Decisions* (keputusan arsitektur) lama.

### Boleh Membaca Source Code
- **Hanya setelah** mendapat referensi path file atau service dari hasil query RAG.
- Saat ingin mengetahui implementasi detail (baris kode) pada class, method, atau file spesifik.
- Saat melakukan proses debugging langsung pada baris yang error.

---

## 3. Urutan Kerja AI Agent

1. **Memahami Task:** Baca request dari user.
2. **Query RAG:** Cari modul, issue, atau informasi terdekat menggunakan keyword.
3. **Eksplorasi Source Code Spesifik:** Jika RAG mengembalikan referensi file, buka dan analisa file spesifik tersebut.
4. **Eksekusi Solusi:** Lakukan modifikasi.
5. **Update Dokumentasi (Opsional):** Jika solusi mengubah struktur modul/decision.
6. **Rebuild RAG:** Jika ada update dokumentasi.
7. **Lapor:** Tulis rangkuman dan kembalikan pada user.

---

## 4. Command Penting

### Query RAG
Gunakan perintah ini untuk mencari informasi pada knowledge base:
```bash
rag-project query "pertanyaan"
```

### Rebuild RAG
Setiap kali ada dokumen yang diubah (misalnya `CHANGELOG.md`, `MODULES.md`, dsb.), wajib jalankan perintah berikut:
```bash
rag-project rebuild
```

---

## 5. Pola Kerja Berdasarkan Situasi

### Contoh Prompt Awal untuk Agent
Jika sebagai agent kamu baru diberikan task: *"Cek mengapa dashboard lambat"*. 
Prompt internal yang kamu jalankan pertama kali seharusnya:
*Eksekusi command:* `rag-project query "kenapa dashboard lambat atau issue performance dashboard"`

### Pola Kerja untuk Debugging
1. Query RAG terkait issue: `rag-project query "known issue terkait [fitur]"`
2. Ekstrak nama Service atau Controller dari output.
3. Baca source code dari path yang didapat.
4. Fix bug pada file tersebut.

### Pola Kerja untuk Tambah Fitur
1. Query RAG: `rag-project query "modul apa yang mengurus [fitur]"`
2. Identifikasi Module yang tepat.
3. Buat service baru dan daftarkan pada `SERVICES.md`.
4. Rebuild RAG.

### Pola Kerja Setelah Ubah Docs / Kode
1. Update `docs/CHANGELOG.md` jika perubahan rilis.
2. Update metadata di `docs/MODULES.md` atau `docs/SERVICES.md` jika nambah logic penting.
3. Jalankan command **Rebuild RAG**.
