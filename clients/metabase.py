import httpx

from .base import BaseClient

ROW_LIMIT = 500


class MetabaseClient(BaseClient):
    def connect(self) -> None:
        res = httpx.post(
            f"{self.cfg['url'].rstrip('/')}/api/session",
            json={"username": self.cfg["username"], "password": self.cfg["password"]},
            timeout=10,
        )
        res.raise_for_status()
        self._token = res.json()["id"]
        self._base_url = self.cfg["url"].rstrip("/")

    def execute(self, query: str) -> tuple[list[dict], bool]:
        # query here is expected to be a card (question) ID or native SQL
        # For native SQL, POST to /api/dataset
        with httpx.Client() as client:
            res = client.post(
                f"{self._base_url}/api/dataset",
                headers={"X-Metabase-Session": self._token},
                json={
                    "database": self.cfg["database_id"],
                    "type": "native",
                    "native": {"query": query},
                },
                timeout=60,
            )
            res.raise_for_status()
            data = res.json()

        cols = [col["name"] for col in data["data"]["cols"]]
        rows = [dict(zip(cols, row)) for row in data["data"]["rows"]]
        truncated = len(rows) > ROW_LIMIT
        return rows[:ROW_LIMIT], truncated

    def close(self) -> None:
        httpx.delete(
            f"{self._base_url}/api/session",
            headers={"X-Metabase-Session": self._token},
            timeout=10,
        )
