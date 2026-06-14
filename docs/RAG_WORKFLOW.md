# RAG Workflow & Troubleshooting

Alur kerja penggunaan RAG untuk AI Agent:

1. Baca `AGENTS.md`
2. Baca `rag-project/README.md`
3. Baca docs RAG
4. Query RAG jika bisa
5. Baru baca source file relevan

## Troubleshooting Command RAG

Jika command RAG dijalankan, contohnya:
```bash
cd rag-project && python -m rag_project.cli --help
```

Dan menghasilkan error:
```
bash: line 1: python: command not found
```
*(Exit code: 127)*

**Catatan / Solusi:**
Ini terjadi karena command `python` tidak ditemukan di environment saat ini (kemungkinan karena harus menggunakan `python3` atau virtual environment belum aktif). Silakan sesuaikan eksekusi menggunakan `python3` atau aktifkan environment yang sesuai jika ingin menjalankan CLI tersebut.
