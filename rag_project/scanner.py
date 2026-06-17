import os
import json
import re
import yaml
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from rag_project.paths import PROJECT_ROOT, CHUNKS_PATH, GRAPH_PATH


def _add_node(nodes: dict, node_id: str, node_type: str, label: str, source: str, domain: str, metadata: dict = None, is_primary: bool = False) -> None:
    """Tambah atau update node di graph.
    
    Args:
        is_primary: Jika True, node ini berasal dari deklarasi class (definisi utama).
                     Jika node sudah ada dengan source sekunder, source akan di-overwrite
                     oleh source primer ini. Ini mengatasi bug dimana model-user bisa
                     mendapat source dari UserUnitKerja.php (via belongsTo) padahal
                     seharusnya dari User.php (class declaration).
    """
    clean_id = node_id.lower().strip()
    clean_type = node_type.lower().strip()
    clean_label = label.replace("\n", "").replace("\r", "").strip()
    clean_label = re.sub(r"\s+", " ", clean_label)
    
    if clean_id not in nodes:
        # Node baru — buat entry
        nodes[clean_id] = {
            "id": clean_id,
            "type": clean_type,
            "label": clean_label,
            "source": source,
            "domain": domain
        }
        if is_primary:
            nodes[clean_id]["_primary_source"] = True
    else:
        # Node sudah ada. Update source hanya jika:
        # - Node baru adalah primary source (class declaration), DAN
        # - Node existing belum punya primary source
        # Ini memastikan source attribution menunjuk ke file dimana class didefinisikan,
        # bukan file yang hanya mereferensikan class tersebut.
        if is_primary and not nodes[clean_id].get("_primary_source"):
            nodes[clean_id]["source"] = source
            nodes[clean_id]["domain"] = domain
            nodes[clean_id]["type"] = clean_type
            nodes[clean_id]["label"] = clean_label
            nodes[clean_id]["_primary_source"] = True

    if metadata:
        nodes[clean_id].update(metadata)


def _add_edge(edges: dict, from_id: str, to_id: str, rel_type: str, source: str) -> None:
    """Tambah edge ke graph dengan auto-deduplication.
    
    Menggunakan dict dengan tuple key (from, to, type) sebagai pengganti list
    untuk menghindari duplikasi edge selama scanning. Edge pertama yang ditemukan
    akan disimpan, duplikat diabaikan.
    """
    clean_from = from_id.lower().strip()
    clean_to = to_id.lower().strip()
    clean_type = rel_type.lower().strip()
    
    edge_key = (clean_from, clean_to, clean_type)
    if edge_key not in edges:
        edges[edge_key] = {
            "from": clean_from,
            "to": clean_to,
            "type": clean_type,
            "source": source
        }


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


def _process_rules(rules: list, content: str, file_id: str, rel_path: str, domain: str, nodes: dict, edges: dict, file_metadata: dict, parent_match=None):
    """Proses rules dari YAML config dan extract entities/relations.
    
    Args:
        edges: Dict dengan key tuple (from, to, type) untuk auto-dedup.
    """
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
                
                # Proses metadata dari YAML config
                metadata = dict(file_metadata)
                ent_metadata = ent.get("metadata", {})
                
                # Cek apakah entity ini ditandai sebagai primary source (class declaration)
                # `primary: true` di YAML metadata = entity ini adalah definisi utama class
                is_primary = False
                if isinstance(ent_metadata.get("primary"), bool):
                    is_primary = ent_metadata["primary"]
                elif isinstance(ent_metadata.get("primary"), str):
                    is_primary = ent_metadata["primary"].lower() == "true"
                
                for k, v in ent_metadata.items():
                    # Skip 'primary' — ini processing hint, bukan data untuk disimpan
                    if k == "primary":
                        continue
                    metadata[k] = _format_string(str(v), match, file_id, rel_path, domain, parent_match)
                    
                if ent_id and ent_type:
                    _add_node(nodes, ent_id, ent_type, ent_label, rel_path, ent_domain, metadata, is_primary)
            
            for rel in rule.get("relations", []):
                from_id = _format_string(rel.get("from"), match, file_id, rel_path, domain, parent_match)
                to_id = _format_string(rel.get("to"), match, file_id, rel_path, domain, parent_match)
                rel_type = _format_string(rel.get("type"), match, file_id, rel_path, domain, parent_match)
                
                if from_id and to_id and rel_type:
                    _add_edge(edges, from_id, to_id, rel_type, rel_path)
                    
            if "sub_rules" in rule:
                _process_rules(rule["sub_rules"], content, file_id, rel_path, domain, nodes, edges, file_metadata, match)


def scan_file_with_config(filepath: Path, rel_path: str, domain: str, config: dict, nodes: dict, edges: dict, chunks: list):
    """Scan satu file dengan config domain dari YAML.
    
    Args:
        edges: Dict dengan key tuple (from, to, type) untuk auto-dedup.
    """
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


def _clean_nodes_for_output(nodes: dict) -> list:
    """Bersihkan internal flags dari nodes sebelum output ke JSON.
    
    Menghapus `_primary_source` flag yang hanya digunakan untuk processing internal,
    bukan data yang perlu disimpan di graph.json.
    """
    result = []
    for node in nodes.values():
        clean_node = {k: v for k, v in node.items() if not k.startswith("_")}
        result.append(clean_node)
    return result


def _edges_dict_to_list(edges: dict) -> list:
    """Konversi edges dict ke list untuk output JSON."""
    return list(edges.values())


def run_scan():
    from rich.console import Console
    console = Console()
    console.print("[yellow]Scanning project files across domains...[/yellow]")
    
    nodes = {}
    # Bug fix: edges sekarang menggunakan dict dengan tuple key (from, to, type)
    # untuk auto-deduplication selama scanning, menggantikan list yang bisa
    # mengakumulasi duplikat
    edges = {}
    chunks = []
    files_scanned = 0
    
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
                    files_scanned += 1
                else:
                    for root, _, files in os.walk(target_path):
                        for file in files:
                            if file.endswith(tuple(extensions)):
                                file_path = Path(root) / file
                                rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
                                scan_file_with_config(file_path, rel_path, domain, domain_config, nodes, edges, chunks)
                                files_scanned += 1
                            
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
        json.dump(final_chunks, f, separators=(',', ':'), ensure_ascii=False)
    
    # Konversi edges dict ke list dan bersihkan internal flags dari nodes
    clean_node_list = _clean_nodes_for_output(nodes)
    edge_list = _edges_dict_to_list(edges)
    
    final_graph = {"nodes": clean_node_list, "edges": edge_list}
    
    if GRAPH_PATH.exists():
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                existing_graph = json.load(f)
                
            # Merge nodes: update existing jika scan baru punya primary source
            existing_nodes_by_id = {n["id"]: n for n in existing_graph.get("nodes", [])}
            
            for n in final_graph["nodes"]:
                nid = n["id"]
                if nid in existing_nodes_by_id:
                    # Node sudah ada di graph lama. Update jika scan baru punya
                    # primary source (dari class declaration) dan existing belum punya.
                    # Ini memastikan source attribution selalu menunjuk ke file definisi.
                    new_is_primary = nodes.get(nid, {}).get("_primary_source", False)
                    if new_is_primary:
                        existing_nodes_by_id[nid]["source"] = n["source"]
                        existing_nodes_by_id[nid]["domain"] = n["domain"]
                        existing_nodes_by_id[nid]["type"] = n["type"]
                        existing_nodes_by_id[nid]["label"] = n["label"]
                        # Update metadata fields juga
                        for k, v in n.items():
                            if k not in ("id", "source", "domain", "type", "label"):
                                existing_nodes_by_id[nid][k] = v
                else:
                    existing_nodes_by_id[nid] = n
            
            # Edge dedup: keep existing logic (sudah benar)
            existing_edges = {(e["from"], e["to"], e["type"]): e for e in existing_graph.get("edges", [])}
            for e in final_graph["edges"]:
                edge_key = (e["from"], e["to"], e["type"])
                if edge_key not in existing_edges:
                    existing_edges[edge_key] = e
                    
            final_graph = {
                "nodes": list(existing_nodes_by_id.values()),
                "edges": list(existing_edges.values())
            }
        except Exception:
            pass
            
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(final_graph, f, separators=(',', ':'), ensure_ascii=False)
        
    console.print(f"  Scanned {files_scanned} files. Found {len(nodes)} entities and {len(edges)} relations.")
