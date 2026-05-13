import json
import os
import re

import mysql.connector
import yaml
from mcp.server.fastmcp import FastMCP

CONFIG_PATH = os.path.expanduser("~/.config/db-mcp/config.yaml")
ROW_LIMIT = 500

WRITE_PATTERN = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE|RENAME|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

mcp = FastMCP("db-mcp")


def load_config():
    with open(CONFIG_PATH) as f:
        raw = os.path.expandvars(f.read())
    return yaml.safe_load(raw)


def run_mysql(cfg, query):
    conn = mysql.connector.connect(
        host=cfg["host"],
        port=cfg.get("port", 3306),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg.get("database"),
        connection_timeout=10,
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchmany(ROW_LIMIT)
        truncated = cursor.fetchone() is not None
        cursor.close()
        return rows, truncated
    finally:
        conn.close()


RUNNERS = {
    "mysql": run_mysql,
}


@mcp.tool()
def list_datasources() -> str:
    """List all configured datasources."""
    config = load_config()
    sources = config.get("datasources", {})
    result = [
        {
            "name": k,
            "type": v["type"],
            "host": v.get("host", ""),
            "database": v.get("database", ""),
        }
        for k, v in sources.items()
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
def execute(datasource: str, query: str) -> str:
    """
    Run a read-only SQL query on a named datasource. Results capped at 500 rows.
    Use list_datasources() to see available datasource names.
    """
    if WRITE_PATTERN.match(query):
        return "Error: write queries are not allowed"

    config = load_config()
    sources = config.get("datasources", {})

    if datasource not in sources:
        available = list(sources.keys())
        return f"Error: unknown datasource '{datasource}'. Available: {available}"

    ds = sources[datasource]
    runner = RUNNERS.get(ds["type"])
    if runner is None:
        return f"Error: unsupported datasource type '{ds['type']}'"

    rows, truncated = runner(ds, query)
    out = {"rows": rows, "count": len(rows)}
    if truncated:
        out["warning"] = f"Results truncated at {ROW_LIMIT} rows. Add LIMIT to your query."
    return json.dumps(out, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
