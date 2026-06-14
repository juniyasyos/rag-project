# Known Issues

1. **Regex Limitations**: Complex, multi-line nested code structures might evade regex-based scanner definitions in `scanners/*.yml`.
2. **Duplicate Graph Edges**: Successive scans append to `graph.json`. While nodes are effectively de-duplicated by ID, edge deduplication may occasionally fail if metadata structures slightly vary across scans.
3. **Scalability Constraints**: `chunks.json` and `graph.json` are loaded entirely into RAM during `query`. This may become a memory bottleneck if the main application scales to 10,000+ files.
