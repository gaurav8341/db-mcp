import json
import os
import re

import yaml
from mcp.server.fastmcp import FastMCP

from clients import get_client
from formatters import get_formatter

CONFIG_PATH = os.path.expanduser("~/.config/db-mcp/config.yaml")

WRITE_PATTERN = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE"
    r"|REPLACE|RENAME|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

mcp = FastMCP("db-mcp")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        raw = os.path.expandvars(f.read())
    return yaml.safe_load(raw)


def _get_source(datasource: str) -> dict | None:
    sources = load_config().get("datasources", {})
    return sources.get(datasource), list(sources.keys())


@mcp.tool()
def list_datasources() -> str:
    """List all configured datasources."""
    config = load_config()
    sources = config.get("datasources", {})
    result = [
        {
            "name": k,
            "type": v["type"],
            "host": v.get("host", v.get("url", "")),
            "database": v.get("database", ""),
        }
        for k, v in sources.items()
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
def execute(datasource: str, query: str) -> str:
    """
    Run a read-only query on a named datasource. Results capped at 500 rows.
    Use list_datasources() to see available datasource names.
    """
    if WRITE_PATTERN.match(query):
        return "Error: write queries are not allowed"

    cfg, available = _get_source(datasource)
    if cfg is None:
        return f"Error: unknown datasource '{datasource}'. Available: {available}"

    with get_client(cfg) as client:
        rows, truncated = client.execute(query)

    out: dict = {"rows": rows, "count": len(rows)}
    if truncated:
        out["warning"] = "Results truncated at 500 rows. Add LIMIT to your query."
    return json.dumps(out, indent=2, default=str)


@mcp.tool()
def export(datasource: str, query: str, fmt: str, path: str) -> str:
    """
    Run a read-only query and save output to a file.
    fmt: 'json' or 'markdown' (or 'md').
    path: absolute file path to write (e.g. /tmp/results.md).
    """
    if WRITE_PATTERN.match(query):
        return "Error: write queries are not allowed"

    cfg, available = _get_source(datasource)
    if cfg is None:
        return f"Error: unknown datasource '{datasource}'. Available: {available}"

    try:
        formatter = get_formatter(fmt)
    except ValueError as e:
        return f"Error: {e}"

    with get_client(cfg) as client:
        rows, truncated = client.execute(query)

    meta = {
        "datasource": datasource,
        "query": query,
        "truncated": truncated,
    }
    content = formatter.format(rows, meta)

    output_path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)

    return f"Saved {len(rows)} rows to {output_path}"


if __name__ == "__main__":
    mcp.run()
