# RAG Schema

Dokumen ini menjelaskan tipe node dan edge yang digunakan oleh sistem RAG untuk melakukan ekstraksi dan penelusuran graf pengetahuan.

## Node Types

- **Project**: Representasi dari keseluruhan project.
- **Module**: Modul atau domain bisnis utama (misal: Daily Report, IAM).
- **Service**: Komponen layanan atau logika bisnis (misal: ImutReportService).
- **Command**: CLI command (misal: SyncFormTemplateDates).
- **Port**: Interface atau kontrak antar modul.
- **Container**: Dependency injection atau Docker container.
- **Env**: Variabel environment (misal: SESSION_DOMAIN).
- **KnownIssue**: Bug atau masalah yang sudah diketahui dan dicatat.
- **Decision**: Keputusan arsitektur atau desain (ADR).
- **Release**: Versi rilis aplikasi (misal: v1.4.0).
- **File**: File fisik dalam repository.
- **Feature**: Fungsionalitas aplikasi.

## Edge Types

- `uses`: Node A menggunakan fungsionalitas Node B (contoh: Service uses Port).
- `exposes`: Node A menyediakan Node B untuk digunakan (contoh: Module exposes Port).
- `has_command`: Node A menyediakan/memiliki Node B (Command).
- `has_issue`: Node A memiliki/terkait dengan masalah Node B (KnownIssue).
- `affected_by`: Node A terpengaruh oleh Node B.
- `decided_by`: Node A adalah hasil dari keputusan Node B (Decision).
- `introduced_in`: Node A pertama kali muncul pada rilis/commit Node B.
- `fixed_in`: Issue Node A diperbaiki pada rilis/commit Node B.
- `related_to`: Relasi umum antara Node A dan Node B.
- `defined_in`: Node A didefinisikan secara fisik dalam Node B (File/Path).

## Contoh Format Node dan Edge

Sistem RAG mengekstrak informasi berdasarkan format key-value sederhana di bawah header.

```markdown
## MOD-001 - Daily Report

Type: Module
Status: Active
Area: Daily Report
Related Services:
- SVC-001
Related Commands:
- CMD-001
Related Issues:
- KI-001
Related Decisions:
- DEC-001
Source:
- app/Modules/DailyReport
- commit: abc1234

Summary:
Modul ini menangani laporan harian...
```
