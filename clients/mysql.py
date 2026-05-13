import mysql.connector

from .base import BaseClient

ROW_LIMIT = 500


class MySQLClient(BaseClient):
    def connect(self) -> None:
        self._conn = mysql.connector.connect(
            host=self.cfg["host"],
            port=self.cfg.get("port", 3306),
            user=self.cfg["user"],
            password=self.cfg["password"],
            database=self.cfg.get("database"),
            connection_timeout=10,
        )

    def execute(self, query: str) -> tuple[list[dict], bool]:
        cursor = self._conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchmany(ROW_LIMIT)
        truncated = cursor.fetchone() is not None
        cursor.close()
        return rows, truncated

    def close(self) -> None:
        if self._conn and self._conn.is_connected():
            self._conn.close()
