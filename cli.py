#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys

import yaml

from clients import get_client
from formatters import get_formatter

CONFIG_PATH = os.path.expanduser("~/.config/db-mcp/config.yaml")

WRITE_PATTERN = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE"
    r"|REPLACE|RENAME|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        raw = os.path.expandvars(f.read())
    return yaml.safe_load(raw)


def get_source(datasource: str) -> dict:
    sources = load_config().get("datasources", {})
    if datasource not in sources:
        print(f"Error: unknown datasource '{datasource}'. Available: {list(sources)}")
        sys.exit(1)
    return sources[datasource]


def run_query(datasource: str, query: str) -> tuple[list[dict], bool]:
    if WRITE_PATTERN.match(query):
        print("Error: write queries are not allowed")
        sys.exit(1)
    cfg = get_source(datasource)
    with get_client(cfg) as client:
        return client.execute(query)


def cmd_execute(args):
    rows, truncated = run_query(args.datasource, args.query)
    out = {"rows": rows, "count": len(rows)}
    if truncated:
        out["warning"] = "Results truncated at 500 rows."
    print(json.dumps(out, indent=2, default=str))


def cmd_export(args):
    rows, truncated = run_query(args.datasource, args.query)
    formatter = get_formatter(args.fmt)
    meta = {
        "datasource": args.datasource,
        "query": args.query,
        "truncated": truncated,
    }
    content = formatter.format(rows, meta)
    output_path = os.path.expanduser(args.path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Saved {len(rows)} rows to {output_path}")


def cmd_list(args):
    sources = load_config().get("datasources", {})
    for name, cfg in sources.items():
        print(f"{name}  [{cfg['type']}]  {cfg.get('host', cfg.get('url', ''))}  {cfg.get('database', '')}")


def main():
    parser = argparse.ArgumentParser(prog="db-mcp")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List configured datasources")

    # execute
    p_exec = sub.add_parser("execute", help="Run a query and print JSON output")
    p_exec.add_argument("datasource", help="Datasource name")
    p_exec.add_argument("query", help="SQL query")

    # export
    p_export = sub.add_parser("export", help="Run a query and save to file")
    p_export.add_argument("datasource", help="Datasource name")
    p_export.add_argument("query", help="SQL query")
    p_export.add_argument("fmt", choices=["json", "markdown", "md"], help="Output format")
    p_export.add_argument("path", help="Output file path")

    args = parser.parse_args()
    {"list": cmd_list, "execute": cmd_execute, "export": cmd_export}[args.command](args)


if __name__ == "__main__":
    main()
