# Storage Format

Data is stored locally in JSON format at paths defined in `paths.py` (typically in `docs/ai-agent/rag/output/`). No complex external databases are used.

## `chunks.json`
Array of text chunks from documentation and source files.
```json
[
  {
    "id": "chunk-file-database-migrations-...",
    "source_file": "database/migrations/...php",
    "domain": "database",
    "content": "...",
    "heading": "File: ...",
    "source_hash": "fab50369...",
    "last_indexed_commit": "fd68e116...",
    "updated_at": "2026-06-14T06:52:59+00:00"
  }
]
```

## `graph.json`
Contains two main lists: `nodes` and `edges`.

### Nodes
Nodes represent extracted entities (e.g., Table, Controller, Model, Service, ConfigFile). Nodes contain complex metadata to guarantee freshness and verify correctness.
```json
{
  "id": "table-posts",
  "type": "Table",
  "label": "posts",
  "source": "database/migrations/...php",
  "domain": "database",
  "source_file": "database/migrations/...php",
  "source_hash": "fab503...",
  "last_indexed_commit": "fd68e11...",
  "updated_at": "2026-06-14T06:52:59+00:00",
  "confidence": "derived_from_source"
}
```

### Edges
Edges represent directional relationships between nodes (e.g., `handled_by`, `depends_on`, `has_column`).
```json
{
  "from": "route-get-api-posts",
  "to": "controller-postcontroller",
  "type": "handled_by",
  "source": "routes/api.php"
}
```
