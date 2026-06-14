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
    parser.add_argument("--domain", type=str, help="Filter search by domain (e.g. docs, database, routes, services, models)")
    args = parser.parse_args()

    if args.command == "sync":
        print("  ℹ️  Command 'sync' is deprecated. RAG now reads directly from the docs without copying.")
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
        run_query(args.arg, args.domain)
    elif args.command == "context":
        from rag_project.query import run_context
        print(run_context(args.arg, args.domain))
    elif args.command == "graph":
        import json
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
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
