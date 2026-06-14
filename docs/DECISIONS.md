# Technical Decisions (ADR)

1. **No Neo4j / External Graph DB**:
   - *Reason*: Over-engineering for early stages. Local JSON files loaded into memory are fast enough for medium-sized projects and remove external system dependencies, making the tool highly portable.
2. **Regex over AST parsers**:
   - *Reason*: Avoids writing or depending on complex Abstract Syntax Tree parsers for multiple languages (PHP, JS, TS). Regex via YAML configurations provides enough accuracy for semantic routing and architecture mapping.
3. **YAML Scanner Configurations**:
   - *Reason*: Decouples scanning logic from Python code. Adding support for new frameworks (e.g., React, Go, Docker) only requires a new declarative YAML file.
4. **No Vector Embeddings Yet**:
   - *Reason*: We currently rely on explicit Graph traversal and keyword/chunk mapping. Embeddings add latency and setup overhead. They can be introduced later if context retrieval precision drops or scales beyond simple lookups.
