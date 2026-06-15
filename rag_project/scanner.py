import os
import json
import re
import yaml
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from rag_project.paths import PROJECT_ROOT, CHUNKS_PATH, GRAPH_PATH

def _add_node(nodes: dict, node_id: str, node_type: str, label: str, source: str, domain: str, metadata: dict = None) -> None:
    if node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "source": source,
            "domain": domain
        }
    if metadata:
        nodes[node_id].update(metadata)

def _add_edge(edges: list, from_id: str, to_id: str, rel_type: str, source: str) -> None:
    edges.append({
        "from": from_id,
        "to": to_id,
        "type": rel_type,
        "source": source
    })

def _format_string(template: str, match, file_id: str, rel_path: str, domain: str, parent_match=None) -> str:
    if not template:
        return ""
    
    s = template.replace("{file_id}", file_id)
    s = s.replace("{rel_path}", rel_path)
    s = s.replace("{domain}", domain)
    
    if parent_match:
        for i, g in enumerate(parent_match.groups(), 1):
            if g:
                s = s.replace(f"{{parent_{i}}}", g)
                s = s.replace(f"{{parent_{i}_lower}}", g.lower())
                s = s.replace(f"{{parent_{i}_upper}}", g.upper())
                s = s.replace(f"{{parent_{i}_slug}}", g.lower().replace("/", "-"))
                
    if match:
        for i, g in enumerate(match.groups(), 1):
            if g:
                s = s.replace(f"{{{i}}}", g)
                s = s.replace(f"{{{i}_lower}}", g.lower())
                s = s.replace(f"{{{i}_upper}}", g.upper())
                s = s.replace(f"{{{i}_slug}}", g.lower().replace("/", "-"))
                
    return s

def _process_rules(rules: list, content: str, file_id: str, rel_path: str, domain: str, nodes: dict, edges: list, file_metadata: dict, parent_match=None):
    if not rules:
        return
        
    for rule in rules:
        pattern = rule.get("pattern")
        if not pattern:
            continue
            
        limit = rule.get("limit", 0)
        try:
            matches = list(re.finditer(pattern, content, flags=re.MULTILINE))
        except re.error:
            continue
            
        if limit > 0:
            matches = matches[:limit]
            
        for match in matches:
            for ent in rule.get("entities", []):
                ent_id = _format_string(ent.get("id"), match, file_id, rel_path, domain, parent_match)
                ent_type = _format_string(ent.get("type"), match, file_id, rel_path, domain, parent_match)
                ent_label = _format_string(ent.get("label"), match, file_id, rel_path, domain, parent_match)
                ent_domain = _format_string(ent.get("domain", domain), match, file_id, rel_path, domain, parent_match)
                
                metadata = dict(file_metadata)
                for k, v in ent.get("metadata", {}).items():
                    metadata[k] = _format_string(v, match, file_id, rel_path, domain, parent_match)
                    
                if ent_id and ent_type:
                    _add_node(nodes, ent_id, ent_type, ent_label, rel_path, ent_domain, metadata)
            
            for rel in rule.get("relations", []):
                from_id = _format_string(rel.get("from"), match, file_id, rel_path, domain, parent_match)
                to_id = _format_string(rel.get("to"), match, file_id, rel_path, domain, parent_match)
                rel_type = _format_string(rel.get("type"), match, file_id, rel_path, domain, parent_match)
                
                if from_id and to_id and rel_type:
                    _add_edge(edges, from_id, to_id, rel_type, rel_path)
                    
            if "sub_rules" in rule:
                _process_rules(rule["sub_rules"], content, file_id, rel_path, domain, nodes, edges, file_metadata, match)


def scan_file_with_config(filepath: Path, rel_path: str, domain: str, config: dict, nodes: dict, edges: list, chunks: list):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return
        
    source_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    try:
        commit_hash = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", str(filepath)], 
            cwd=PROJECT_ROOT, 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        commit_hash = ""

    updated_at = datetime.now(timezone.utc).isoformat()
    
    file_metadata = {
        "source_file": rel_path,
        "source_hash": source_hash,
        "last_indexed_commit": commit_hash,
        "updated_at": updated_at,
        "confidence": "derived_from_source"
    }

    file_id = rel_path.lower().replace("/", "-").replace(".", "-")
    
    rules = config.get("rules", [])
    _process_rules(rules, content, file_id, rel_path, domain, nodes, edges, file_metadata)

def run_scan():
    from rich.console import Console
    console = Console()
    console.print("[yellow]Scanning project files across domains...[/yellow]")
    
    nodes = {}
    edges = []
    chunks = []
    
    scanners_dir = Path(__file__).parent / "scanners"
    configs = []
    scanner_name = os.environ.get("RAG_SCANNER", "laravel")
    scanner_file = scanners_dir / f"{scanner_name}.yml"
    
    if scanner_file.exists():
        try:
            with open(scanner_file, "r", encoding="utf-8") as yf:
                configs.append(yaml.safe_load(yf))
        except Exception as e:
            console.print(f"[red]Error loading scanner config {scanner_file}: {e}[/red]")
                
    if not configs:
        console.print(f"[yellow]Scanner config {scanner_name}.yml not found in scanners directory.[/yellow]")
        return
        
    for config in configs:
        extensions = config.get("extensions", [".php", ".yml", ".yaml", ".md", ".json", ".js", ".vue"])
        domains = config.get("domains", {})
        
        for domain, domain_config in domains.items():
            paths = domain_config.get("paths", [])
            for path_str in paths:
                target_path = PROJECT_ROOT / path_str
                if not target_path.exists():
                    continue
                if target_path.is_file():
                    scan_file_with_config(target_path, path_str, domain, domain_config, nodes, edges, chunks)
                else:
                    for root, _, files in os.walk(target_path):
                        for file in files:
                            if file.endswith(tuple(extensions)):
                                file_path = Path(root) / file
                                rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
                                scan_file_with_config(file_path, rel_path, domain, domain_config, nodes, edges, chunks)
                            
    if CHUNKS_PATH.exists():
        try:
            with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
        except:
            existing_chunks = []
    else:
        existing_chunks = []
        
    final_chunks = existing_chunks + chunks
    
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=2, ensure_ascii=False)
        
    final_graph = {"nodes": list(nodes.values()), "edges": edges}
    if GRAPH_PATH.exists():
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                existing_graph = json.load(f)
                
            existing_node_ids = {n["id"] for n in existing_graph.get("nodes", [])}
            for n in final_graph["nodes"]:
                if n["id"] not in existing_node_ids:
                    existing_graph.setdefault("nodes", []).append(n)
            
            existing_edges = {(e["from"], e["to"], e["type"]) for e in existing_graph.get("edges", [])}
            for e in final_graph["edges"]:
                if (e["from"], e["to"], e["type"]) not in existing_edges:
                    existing_graph.setdefault("edges", []).append(e)
                    
            final_graph = existing_graph
        except Exception:
            pass
            
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(final_graph, f, indent=2, ensure_ascii=False)
        
    console.print(f"  Scanned {len(chunks)} files. Found {len(nodes)} entities and {len(edges)} relations.")
