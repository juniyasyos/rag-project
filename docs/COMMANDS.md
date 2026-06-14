# Commands

Use the CLI by running `python -m rag_project.cli <command> [args]`.

## Data Indexing Commands
- `sync`: Sync external/internal documentation.
- `ingest`: Ingest documentation into chunks.
- `scan`: Execute YAML-based source code scanners across the project to extract relationships.
- `refresh` / `rebuild`: Runs `sync` -> `ingest` -> `scan` sequentially, completely rebuilding the knowledge base.

## Search and Query
- `search <query> [--domain <domain>]`: Semantic or keyword search. Same as `query`.
- `query <query> [--domain <domain>]`: Interactively ask the LLM a question based on indexed knowledge.
- `context <query> [--domain <domain>]`: Returns raw formatted context (JSON/Text) that would be passed to the LLM without actually querying it.
- `graph <query>`: Searches for a node in the graph by label or ID and prints its connections.
- `inspect <node_id>`: Prints the detailed exact match node properties and all edges connected to it.

## Utilities
- `check`: Validates the freshness of the index against current commit hashes and modification times.
