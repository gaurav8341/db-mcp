# db-mcp

A Model Context Protocol (MCP) server that gives Claude read-only access to your databases. Configure multiple named datasources once; query any of them by name.

## How it works

Claude Code launches this server automatically at session start (stdio transport). You never run it manually. Two tools are exposed:

- **`list_datasources`** — show all configured datasources (name, type, host, database)
- **`execute(datasource, query)`** — run a read-only SQL query, get rows back as JSON

Usage in Claude:
```
list the datasources
run this on codex-staging: SELECT id, status FROM orders WHERE id = 12345
```

Write queries (INSERT, UPDATE, DELETE, DROP, etc.) are blocked server-side.
Results are capped at 500 rows — add a `LIMIT` clause for large tables.

## Supported datasources

| Type | Status |
|------|--------|
| MySQL | ✅ |
| MongoDB | ✅ (query is JSON: `{"collection": "x", "filter": {...}, "limit": 10}` or `{"collection": "x", "pipeline": [...]}`; `$out`/`$merge` blocked) |
| ClickHouse | ✅ (SQL; connection opened with `readonly=1`) |
| Redash | planned |
| Metabase | planned |

## Setup

### 1. Install dependencies

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd ~/repos/db-mcp
uv sync
```

### 2. Create your config

```bash
mkdir -p ~/.config/db-mcp
cp config.example.yaml ~/.config/db-mcp/config.yaml
```

Edit `~/.config/db-mcp/config.yaml`:

```yaml
datasources:
  codex-prod:
    type: mysql
    host: <ec2-ip>
    port: 3306
    user: readonly
    password: ${CODEX_PROD_DB_PASS}   # env var expansion supported
    database: codex

  codex-staging:
    type: mysql
    host: <ec2-ip>
    port: 3306
    user: readonly
    password: ${CODEX_STAGING_DB_PASS}
    database: codex
```

Passwords can be hardcoded strings or `${ENV_VAR}` references — the server expands env vars at load time.

### 3. Register with Claude Code

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "db-mcp": {
      "type": "stdio",
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--project",
        "/path/to/db-mcp",
        "/path/to/db-mcp/server.py"
      ]
    }
  }
}
```

Restart Claude Code. The server starts automatically each session.

## Adding a new datasource

Add a new entry to `~/.config/db-mcp/config.yaml` — no server restart needed, config is loaded fresh on each query.

## Project structure

```
db-mcp/
  server.py             # MCP server (FastMCP, two tools)
  pyproject.toml        # uv dependencies
  config.example.yaml   # template — copy to ~/.config/db-mcp/config.yaml
```

## Security

- Write queries are blocked by regex on the server side
- Config lives outside the repo (`~/.config/db-mcp/`) — never committed
- MySQL connections are read-only by the DB user — use a `readonly` or `SELECT`-only grant
