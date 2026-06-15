# Architecture

## Overview
A minimal Python-based RAG CLI tool. It operates primarily on JSON local storage. 
It explicitly avoids over-engineering by rejecting graph databases (Neo4j) or vector databases for the current iteration.

## Core Modules
- `cli.py`: The entrypoint for all CLI commands.
- `scanner.py`: Dynamically reads `scanners/*.yml` configs to parse application source code and extract entities (nodes) and relations (edges) using regex.
- `query.py`: Retrieves information from the extracted chunks and graph to form relevant context.
- `ingest.py`: Handles parsing markdown documentation files into chunks.
- `sync.py`: Used for syncing external or additional docs into the system context.
- `freshness.py`: Checks timestamps and commit hashes to ensure the graph isn't stale compared to the current codebase state.
- `paths.py`: Centralized path management (e.g. `GRAPH_PATH`, `CHUNKS_PATH`).
- `config.py`: Environment configuration management.

## Flow
1. **Sync**: Gathers documentation and files.
2. **Ingest/Scan**: 
   - `ingest`: Parses raw documentation files.
   - `scan`: Runs regex patterns defined in YAML against the source code, creating `nodes` and `edges` representing entities and dependencies.
3. **Storage**: Nodes, edges, and chunks are saved natively as `graph.json` and `chunks.json`.
4. **Query**: The user asks a question via the CLI. `query.py` searches `chunks.json` and `graph.json`, and concatenates the context to be served.
