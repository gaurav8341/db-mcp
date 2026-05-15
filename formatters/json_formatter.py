import json

from .base import BaseFormatter


class JsonFormatter(BaseFormatter):
    def format(self, rows: list[dict], meta: dict) -> str:
        out = {
            "datasource": meta.get("datasource"),
            "query": meta.get("query"),
            "count": len(rows),
            "rows": rows,
        }
        if meta.get("truncated"):
            out["warning"] = "Results truncated at 500 rows."
        return json.dumps(out, indent=2, default=str)

    @property
    def extension(self) -> str:
        return "json"
