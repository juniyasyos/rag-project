# Roadmap (Next Improvements)

1. **Scanner Expansion**: 
   - Add `react.yml` for scanning JSX/TSX components and props.
   - Add `docker.yml` for extracting advanced infrastructure links and service maps.
   - Migrate any remaining hardcoded regex logic out of `scanner.py` completely into their respective YAML files.
2. **Incremental Indexing**: 
   - Utilize `source_hash` and `last_indexed_commit` (newly added metadata) to only re-scan files that have changed, rather than scanning the whole project from scratch on `scan`.
3. **Vector Embeddings (Future)**: 
   - Integrate simple local embeddings (e.g., `sentence-transformers` or OpenAI/Anthropic embeddings) when basic keyword search in `chunks.json` is no longer sufficient.
4. **Edge Deduplication Fix**:
   - Improve graph merging logic in `scanner.py` to ensure edges are robustly de-duplicated across multiple scans.
