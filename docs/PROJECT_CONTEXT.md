# Project Context: RAG Intelligence System

## Purpose
This sub-project is a lightweight Retrieval-Augmented Generation (RAG) system built natively in Python to index, trace, and reason over the main application's codebase (which includes Laravel, React, Docker, etc.).

## Scope
- Focuses **only** on managing the knowledge graph and extracting source code intelligence.
- Acts as an intelligent developer assistant engine to assist the AI Agent in understanding the broader codebase context.
- Currently, it extracts code semantics via regex defined in YAML scanner configurations (e.g., `scanners/laravel.yml`), without relying on heavy abstract syntax tree (AST) parsers.

## Goals
- Allow the AI Agent to reason about the user's project holistically.
- Map entities (Tables, Controllers, Models, Routes) and relationships.
- Answer queries using an LLM (currently Anthropic/Claude) given context extracted from the graph.
- Keep the design minimal: No complex graph databases like Neo4j, no complex embedding vector DBs yet. Local JSON files are the single source of truth.
