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
    lower = content.lower()
    if re.search(r"project.*siimut|siimut.*adalah|sistem indikator mutu", lower):
        _add_node(all_nodes, "siimut", "Project", "SIIMUT", filename)
    if "filament" in lower:
        _add_node(all_nodes, "filament", "App", "Filament", filename)

    for mod_id, mod_label in [
        ("authorization", "Authorization"), ("benchmarking", "Benchmarking"),
        ("daily-report", "DailyReport"), ("form-engine", "FormEngine"),
        ("imut-master", "ImutMaster"), ("laporan", "Laporan"), ("reporting", "Reporting")
    ]:
        if mod_id.replace("-", " ") in lower or mod_id.replace("-", "") in lower:
             _add_node(all_nodes, mod_id, "Module", mod_label, filename)

    if "iam" in lower or "sso" in lower or "nexaid" in lower:
        _add_node(all_nodes, "iam-service", "Service", "IAM/SSO Service", filename)
    if "nginx" in lower:
        _add_node(all_nodes, "nginx", "Service", "Nginx", filename)
    if "mysql" in lower or "mariadb" in lower:
        _add_node(all_nodes, "mysql", "Service", "MySQL", filename)
    if "redis" in lower:
        _add_node(all_nodes, "redis", "Service", "Redis", filename)
    if "queue" in lower:
        _add_node(all_nodes, "queue-worker", "Service", "Queue Worker", filename)
    if "backup" in lower:
        _add_node(all_nodes, "backup-service", "Service", "Backup Service", filename)

    if re.search(r"port\s+8000|:8000", lower):
        _add_node(all_nodes, "port-8000", "Port", "Port 8000", filename)
    if re.search(r"port\s+8088|:8088", lower):
        _add_node(all_nodes, "port-8088", "Port", "Port 8088", filename)
    if re.search(r"port\s+3306|:3306", lower):
        _add_node(all_nodes, "port-3306", "Port", "Port 3306", filename)

    if "volume" in lower:
        _add_node(all_nodes, "storage-volume", "Volume", "Storage Volume", filename)

    if re.search(r"session_driver|queue_connection|app_env|db_host|app_key", lower):
        _add_node(all_nodes, "env-config", "Env", "Environment Config", filename)

    if "php artisan serve" in lower:
        _add_node(all_nodes, "cmd-serve", "Command", "php artisan serve", filename)
    if "php artisan migrate" in lower:
        _add_node(all_nodes, "cmd-migrate", "Command", "php artisan migrate", filename)
    if "composer" in lower and "dev" not in lower.split()[:3]:
        _add_node(all_nodes, "cmd-composer", "Command", "Composer", filename)

    if re.search(r"needs review|needs verification|bug|issue|masalah|bottleneck", lower):
        _add_node(all_nodes, "known-issue-kernel", "KnownIssue", "Kernel Duplication Issue", filename)

    if filename == "KNOWN_ISSUES.md":
        for issue_id in re.findall(r"\*\*ID\*\*:\s*(KI-\d+)", content):
            issue_label_match = re.search(r"##\s+" + re.escape(issue_id) + r":\s*(.+?)(?:\n|$)", content)
            label = issue_label_match.group(1).strip() if issue_label_match else issue_id
            safe_id = issue_id.lower().replace("-", "-")
            _add_node(all_nodes, safe_id, "KnownIssue", label, filename)

    if filename == "DECISIONS.md":
        for dec_id in re.findall(r"\*\*ID\*\*:\s*(DEC-\d+)", content):
            dec_label_match = re.search(r"##\s+" + re.escape(dec_id) + r":\s*(.+?)(?:\n|$)", content)
            label = dec_label_match.group(1).strip() if dec_label_match else dec_id
            safe_id = dec_id.lower().replace("-", "-")
            _add_node(all_nodes, safe_id, "Decision", label, filename)

    if "refactor" in lower or "migrasi" in lower:
        _add_node(all_nodes, "decision-refactor", "Decision", "Refactor Decision", filename)

    if "docker" in lower:
        _add_node(all_nodes, "docker", "Container", "Docker", filename)

    if re.search(r"v\d+\.\d+\.\d+", content):
        for v in re.findall(r"v(\d+\.\d+\.\d+)", content):
            safe = f"release-v{v.replace('.', '-')}"
            _add_node(all_nodes, safe, "Release", f"Release v{v}", filename)

    blocks = re.split(r'\n##\s+([A-Z]+-\d+)\s+-\s+([^\n]+)\n', '\n' + content)
    for i in range(1, len(blocks) - 2, 3):
        node_id = blocks[i].lower().strip()
        label = blocks[i+1].strip()
        body = blocks[i+2]
        metadata = {}
        for key in ["Type", "Status", "Area"]:
            m = re.search(fr"^{key}:\s*(.+)", body, re.MULTILINE)
            if m: metadata[key.lower()] = m.group(1).strip()
        for list_key in ["Related Services", "Related Commands", "Related Issues", "Related Decisions", "Related Modules", "Source"]:
            m = re.search(fr"^{list_key}:\n((?:-\s+.*\n?)+)", body, re.MULTILINE)
            if m:
                items = [x.strip("- ").strip() for x in m.group(1).strip().split('\n') if x.strip()]
                metadata[list_key.lower().replace(" ", "_")] = items
        m = re.search(r"-\s+commit:\s*(.+)", body, re.MULTILINE)
        if m: metadata["commit"] = m.group(1).strip()
        node_type = metadata.get("type", "Unknown")
        _add_node(all_nodes, node_id, node_type, label, filename, metadata)


def extract_edges(filename: str, content: str, nodes: dict[str, dict], edges: list[dict]) -> None:
    lower = content.lower()
    if "filament" in lower and ("service" in lower or "layer" in lower):
        _add_edge(edges, "filament", "iam-service", "uses", filename, nodes)
        _add_edge(edges, "filament", "backup-service", "uses", filename, nodes)

    if "nginx" in lower and "filament" in lower or "nginx" in lower and "aplikasi" in lower:
        _add_edge(edges, "filament", "nginx", "exposed_by", filename, nodes)

    if ":8000" in lower:
        _add_edge(edges, "filament", "port-8000", "has_port", filename, nodes)

    for mod_id in ["authorization", "benchmarking", "daily-report", "form-engine", "imut-master", "laporan", "reporting"]:
        mod_label = mod_id.replace("-", " ").title().replace(" ", "")
        if mod_label.lower() in lower:
            _add_edge(edges, mod_id, "iam-service", "uses", filename, nodes)

    if "refactor" in lower:
        _add_edge(edges, "decision-refactor", "siimut", "affects", filename, nodes)

    for issue_id in re.findall(r"\*\*ID\*\*:\s*(KI-\d+)", content):
        safe_issue = issue_id.lower().replace("-", "-")
        area_match = re.search(r"\*\*Area\*\*:\s*(.+?)(?:\n|$)", content)
        if area_match:
            area = area_match.group(1).strip().lower()
            area_node_map = {
                "performa": "daily-report", "performance": "daily-report", "arsitektur": "siimut",
                "architecture": "siimut", "security": "siimut", "konfigurasi": "env-config",
                "configuration": "env-config", "dependency": "cmd-composer", "ui": "filament",
            }
            target = area_node_map.get(area, "siimut")
            _add_edge(edges, safe_issue, target, "related_to", filename, nodes)

    for dec_id in re.findall(r"\*\*ID\*\*:\s*(DEC-\d+)", content):
        safe_dec = dec_id.lower().replace("-", "-")
        context_lower = content.lower()
        if "modular" in context_lower or "arsitektur" in context_lower:
            _add_edge(edges, safe_dec, "siimut", "affects", filename, nodes)
        if "query" in context_lower or "performa" in context_lower:
            _add_edge(edges, safe_dec, "daily-report", "affects", filename, nodes)
        if "dokumentasi" in context_lower or "graphrag" in context_lower:
            _add_edge(edges, safe_dec, "siimut", "affects", filename, nodes)

    if re.search(r"##\s+added|##\s+changed|##\s+fixed", content):
        for v in re.findall(r"v(\d+\.\d+\.\d+)", content):
            safe = f"release-v{v.replace('.', '-')}"
            safe_change = f"change-{v.replace('.', '-')}"
            _add_node(nodes, safe_change, "Change", f"Changes in v{v}", filename)
            _add_edge(edges, safe, safe_change, "includes", filename, nodes)

    if re.search(r"bottleneck|30.sec|n.1.query", lower):
        _add_edge(edges, "known-issue-kernel", "daily-report", "related_to", filename, nodes)

    if "docker-compose" in lower:
        _add_node(nodes, "docker-compose", "Container", "Docker Compose", filename)
        _add_edge(edges, "docker", "docker-compose", "depends_on", filename, nodes)

    for node_id, node_data in nodes.items():
        if node_data.get("source") != filename:
            continue
        for key, rel_type in [
            ("related_services", "uses"), ("related_commands", "has_command"),
            ("related_issues", "has_issue"), ("related_decisions", "decided_by"),
            ("related_modules", "related_to")
        ]:
            if key in node_data:
                for item in node_data[key]:
                    if item.lower() != "none" and "needs verification" not in item.lower():
                        target_id = item.lower()
                        _add_edge(edges, node_id, target_id, rel_type, filename, nodes)

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
