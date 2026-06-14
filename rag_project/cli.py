import sys
import argparse
from rag_project.config import load_config
from rag_project.sync import sync_docs
from rag_project.ingest import run_ingest
from rag_project.query import run_query
from rag_project.freshness import write_metadata, check_freshness
from rag_project.paths import GRAPH_PATH

def main():
    load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["sync", "ingest", "rebuild", "query", "graph", "check"])
    parser.add_argument("arg", nargs="?", default="")
    args = parser.parse_args()

    if args.command == "sync":
        sync_docs()
    elif args.command == "ingest":
        run_ingest()
        write_metadata()
    elif args.command == "rebuild":
        sync_docs()
        run_ingest()
        write_metadata()
    elif args.command == "query":
        run_query(args.arg)
    elif args.command == "graph":
        import json
        with open(GRAPH_PATH, "r", encoding="utf-8") as f: graph = json.load(f)
        for n in graph["nodes"]:
            if args.arg.lower() in n["label"].lower() or args.arg.lower() in n["id"].lower():
                print(f"Node: {n}")
                for e in graph["edges"]:
                    if e["from"] == n["id"] or e["to"] == n["id"]:
                        print(f"  Edge: {e['from']} --[{e['type']}]--> {e['to']}")
    elif args.command == "check":
        check_freshness()
