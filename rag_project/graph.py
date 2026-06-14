import re
from collections import OrderedDict

def _add_node(nodes: dict, node_id: str, node_type: str, label: str,
              source: str, metadata: dict = None) -> None:
    if node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "source": source,
        }
    if metadata:
        nodes[node_id].update(metadata)

def _add_edge(edges: list, from_id: str, to_id: str, rel_type: str,
              source: str, nodes: dict) -> None:
    if from_id in nodes and to_id in nodes:
        edges.append({
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "source": source,
        })

def extract_entities(filename: str, content: str, all_nodes: dict[str, dict]) -> None:
    doc_id = f"doc-{filename.replace('.md', '').lower()}"
    _add_node(all_nodes, doc_id, "document", filename, filename)

    for match in re.finditer(r"^##\s+(.*)$", content, re.MULTILINE):
        sec_name = match.group(1).strip()
        sec_id = f"section-{filename}-{sec_name.lower().replace(' ', '-')}"
        _add_node(all_nodes, sec_id, "section", sec_name, filename)

    for match in re.finditer(r"^-\s+`([^`]+)`:", content, re.MULTILINE):
        val = match.group(1).strip()
        if val.endswith('.py'):
            _add_node(all_nodes, f"module-{val.lower()}", "module", val, filename)
        else:
            _add_node(all_nodes, f"command-{val.lower()}", "command", val, filename)

    for match in re.finditer(r"^##\s+`([^`]+\.json)`", content, re.MULTILINE):
        val = match.group(1).strip()
        _add_node(all_nodes, f"storage_file-{val.lower()}", "storage_file", val, filename)

    if "DECISIONS.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_node(all_nodes, f"decision-{val.lower().replace(' ', '-')}", "decision", val, filename)

    if "KNOWN_ISSUES.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_node(all_nodes, f"known_issue-{val.lower().replace(' ', '-')}", "known_issue", val, filename)

    if "ROADMAP.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_node(all_nodes, f"roadmap_item-{val.lower().replace(' ', '-')}", "roadmap_item", val, filename)


def extract_edges(filename: str, content: str, nodes: dict[str, dict], edges: list[dict]) -> None:
    doc_id = f"doc-{filename.replace('.md', '').lower()}"

    for match in re.finditer(r"^##\s+(.*)$", content, re.MULTILINE):
        sec_name = match.group(1).strip()
        sec_id = f"section-{filename}-{sec_name.lower().replace(' ', '-')}"
        _add_edge(edges, doc_id, sec_id, "contains", filename, nodes)

    for match in re.finditer(r"^-\s+`([^`]+)`:", content, re.MULTILINE):
        val = match.group(1).strip()
        if val.endswith('.py'):
            _add_edge(edges, doc_id, f"module-{val.lower()}", "defines", filename, nodes)
        else:
            _add_edge(edges, doc_id, f"command-{val.lower()}", "defines", filename, nodes)

    for match in re.finditer(r"^##\s+`([^`]+\.json)`", content, re.MULTILINE):
        val = match.group(1).strip()
        _add_edge(edges, doc_id, f"storage_file-{val.lower()}", "defines", filename, nodes)

    if "DECISIONS.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_edge(edges, doc_id, f"decision-{val.lower().replace(' ', '-')}", "contains", filename, nodes)

    if "KNOWN_ISSUES.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_edge(edges, doc_id, f"known_issue-{val.lower().replace(' ', '-')}", "contains", filename, nodes)

    if "ROADMAP.md" in filename:
        for match in re.finditer(r"^\d+\.\s+\*\*(.*)\*\*:", content, re.MULTILINE):
            val = match.group(1).strip()
            _add_edge(edges, doc_id, f"roadmap_item-{val.lower().replace(' ', '-')}", "contains", filename, nodes)

    # Manual specific relations based on text context
    if "JSON local storage" in content:
        _add_edge(edges, doc_id, "storage_file-chunks.json", "uses", filename, nodes)
        _add_edge(edges, doc_id, "storage_file-graph.json", "uses", filename, nodes)
        
    if "Neo4j" in content and "DECISIONS.md" in filename:
        _add_edge(edges, "decision-no-neo4j-/-external-graph-db", "module-llm.py", "related_to", filename, nodes) # just an example connection
        
    if "ROADMAP.md" in filename:
        _add_edge(edges, "roadmap_item-scanner-expansion", "doc-architecture", "planned_in", filename, nodes)
        _add_edge(edges, "roadmap_item-vector-embeddings-(future)", "doc-project_context", "planned_in", filename, nodes)
        
    if "KNOWN_ISSUES.md" in filename:
        _add_edge(edges, "doc-project_context", "known_issue-regex-limitations", "limited_by", filename, nodes)
        
    if "ARCHITECTURE.md" in filename:
        _add_edge(edges, doc_id, "module-scanner.py", "documents", filename, nodes)
        _add_edge(edges, doc_id, "module-ingest.py", "documents", filename, nodes)

def build_graph(all_files: list[tuple[str, str]]) -> dict:
    nodes = OrderedDict()
    edges = []
    seen_edges = set()

    for filename, content in all_files:
        extract_entities(filename, content, nodes)

    for filename, content in all_files:
        e_before = len(edges)
        extract_edges(filename, content, nodes, edges)
        new_edges = edges[e_before:]
        deduped = []
        for e in new_edges:
            key = (e["from"], e["to"], e["type"])
            if key not in seen_edges:
                seen_edges.add(key)
                deduped.append(e)
        edges[e_before:] = deduped

    return {"nodes": list(nodes.values()), "edges": edges}
