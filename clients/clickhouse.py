import clickhouse_connect

from .base import BaseClient

ROW_LIMIT = 500


class ClickHouseClient(BaseClient):
    def connect(self) -> None:
        self._client = clickhouse_connect.get_client(
            host=self.cfg["host"],
            port=self.cfg.get("port", 8123),
            username=self.cfg.get("user", "default"),
            password=self.cfg.get("password", ""),
            database=self.cfg.get("database", "default"),
            secure=self.cfg.get("secure", False),
            connect_timeout=10,
            settings={"readonly": 1},  # server-side guard against writes
        )

    def execute(self, query: str) -> tuple[list[dict], bool]:
        result = self._client.query(query)
        cols = result.column_names
        rows = [dict(zip(cols, row)) for row in result.result_rows[: ROW_LIMIT + 1]]
        truncated = len(rows) > ROW_LIMIT
        return rows[:ROW_LIMIT], truncated

    def close(self) -> None:
        self._client.close()
