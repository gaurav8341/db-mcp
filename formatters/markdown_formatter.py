from .base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    def format(self, rows: list[dict], meta: dict) -> str:
        lines = []
        lines.append(f"## Query")
        lines.append(f"**Datasource:** `{meta.get('datasource')}`  ")
        lines.append(f"**Query:**")
        lines.append(f"```sql")
        lines.append(meta.get("query", "").strip())
        lines.append(f"```")
        lines.append(f"**Rows returned:** {len(rows)}")
        if meta.get("truncated"):
            lines.append(f"> Results truncated at 500 rows.")
        lines.append("")

        if not rows:
            lines.append("_No results._")
            return "\n".join(lines)

        cols = list(rows[0].keys())
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join("---" for _ in cols) + " |")
        for row in rows:
            cells = [str(row.get(c, "")) if row.get(c) is not None else "" for c in cols]
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)

    @property
    def extension(self) -> str:
        return "md"
