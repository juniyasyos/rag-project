import sys
import argparse
from rag_project.config import load_config
from rag_project.sync import sync_docs
from rag_project.ingest import run_ingest
from rag_project.query import run_query
from rag_project.freshness import write_metadata, check_freshness
from rag_project.paths import GRAPH_PATH
from rag_project.scanner import run_scan

def main():
    load_config()
    parser = argparse.ArgumentParser(description="Project Intelligence RAG CLI")
    parser.add_argument("command", choices=["sync", "ingest", "scan", "search", "query", "graph", "inspect", "context", "refresh", "check", "rebuild"])
    parser.add_argument("arg", nargs="?", default="")
    parser.add_argument("--intent", type=str, help="Intent of the query (e.g. project_overview, service_lookup)")
    parser.add_argument("--subject", type=str, help="Subject of the query")
    parser.add_argument("--entity", type=str, action="append", help="Entity related to the query")
    parser.add_argument("--key", type=str, action="append", help="Key for search")
    parser.add_argument("--domain", type=str, action="append", help="Filter search by domain (e.g. docs, database, routes, services, models)")
    parser.add_argument("--top", type=int, default=3, help="Top K chunks to retrieve")
    parser.add_argument("--mode", type=str, choices=["librarian", "handoff"], default="librarian", help="Mode for output (librarian, handoff)")
    parser.add_argument("--debug", action="store_true", help="Print debug information during query")
    args = parser.parse_args()

    if args.command == "sync":
        print("  Command 'sync' is deprecated. RAG now reads directly from the docs without copying.")
    elif args.command == "ingest":
        run_ingest()
        write_metadata()
    elif args.command == "scan":
        run_scan()
        write_metadata()
    elif args.command in ["rebuild", "refresh"]:
        run_ingest()
        run_scan()
        write_metadata()
    elif args.command in ["query", "search"]:
        if not args.intent:
            print("Error: --intent is required for query/search.")
            print("Examples:")
            print("  rag query --intent project_overview")
            print("  rag query --intent service_lookup --entity LaporanImut --key migrate")
            sys.exit(1)
        
        valid_intents = [
            "project_overview", "architecture_analysis", "service_lookup", 
            "data_model_lookup", "command_lookup", "api_reference", 
            "troubleshooting", "rag_usage", "docs_lookup"
        ]
        if args.intent not in valid_intents:
            print(f"Error: Invalid intent '{args.intent}'.\nValid intents: {', '.join(valid_intents)}")
            sys.exit(1)
            
        run_query(
            intent=args.intent,
            subject=args.subject,
            entities=args.entity or [],
            keys=args.key or [],
            domains=args.domain or [],
            top_k=args.top,
            mode=args.mode,
            debug=args.debug
        )
    elif args.command == "context":
        from rag_project.query import run_context
        # Use arg as subject or intent for backwards compat, though context command should be updated too
        print(run_context(args.arg, args.domain and [args.domain] or []))
    elif args.command == "graph":
        import json
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
            if args.arg.lower() == "stats":
                node_types = {}
                for n in graph["nodes"]:
                    ntype = n.get("type", "unknown")
                    node_types[ntype] = node_types.get(ntype, 0) + 1
                edge_types = {}
                for e in graph["edges"]:
                    etype = e.get("type", "unknown")
                    edge_types[etype] = edge_types.get(etype, 0) + 1
                
                print("=== GRAPH STATS ===")
                print(f"Total Nodes: {len(graph['nodes'])}")
                print(f"Total Edges: {len(graph['edges'])}")
                print("\nNode Types:")
                for k, v in node_types.items(): print(f"  - {k}: {v}")
                print("\nEdge Types:")
                for k, v in edge_types.items(): print(f"  - {k}: {v}")
                return
                
            for n in graph["nodes"]:
                if args.arg.lower() in n["label"].lower() or args.arg.lower() in n["id"].lower():
                    print(f"Node: {n}")
                    for e in graph["edges"]:
                        if e["from"] == n["id"] or e["to"] == n["id"]:
                            print(f"  Edge: {e['from']} --[{e['type']}]--> {e['to']}")
        except FileNotFoundError:
            print("Graph not found. Run ingest or scan first.")
    elif args.command == "inspect":
        import json
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
            found = False
            for n in graph["nodes"]:
                if n["id"].lower() == args.arg.lower():
                    found = True
                    print(f"Node: {json.dumps(n, indent=2)}")
                    print("Edges:")
                    for e in graph["edges"]:
                        if e["from"] == n["id"] or e["to"] == n["id"]:
                            print(f"  {e['from']} --[{e['type']}]--> {e['to']}")
            if not found:
                print(f"Node '{args.arg}' not found.")
        except FileNotFoundError:
            print("Graph not found. Run ingest or scan first.")
    elif args.command == "check":
        check_freshness()

if __name__ == "__main__":
    main()
