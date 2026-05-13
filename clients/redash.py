import time

import httpx

from .base import BaseClient

ROW_LIMIT = 500
POLL_INTERVAL = 1  # seconds


class RedashClient(BaseClient):
    def connect(self) -> None:
        self._headers = {"Authorization": f"Key {self.cfg['api_key']}"}
        self._base_url = self.cfg["url"].rstrip("/")
        self._data_source_id = self.cfg["data_source_id"]

    def execute(self, query: str) -> tuple[list[dict], bool]:
        payload = {
            "query": query,
            "data_source_id": self._data_source_id,
            "max_age": 0,
        }
        with httpx.Client(follow_redirects=True) as client:
            res = client.post(
                f"{self._base_url}/api/query_results",
                json=payload,
                headers=self._headers,
                timeout=30,
            )
            res.raise_for_status()
            data = res.json()

            if "query_result" in data:
                rows = data["query_result"]["data"]["rows"]
            elif "job" in data:
                rows = self._poll_job(client, data["job"]["id"])
            else:
                raise ValueError(f"Unexpected Redash response: {data}")

        truncated = len(rows) > ROW_LIMIT
        return rows[:ROW_LIMIT], truncated

    def _poll_job(self, client: httpx.Client, job_id: str) -> list[dict]:
        while True:
            res = client.get(
                f"{self._base_url}/api/jobs/{job_id}",
                headers=self._headers,
                timeout=30,
            )
            res.raise_for_status()
            job = res.json()["job"]
            status = job["status"]  # 1=pending 2=started 3=success 4=failure

            if status == 3:
                result_id = job["query_result_id"]
                final = client.get(
                    f"{self._base_url}/api/query_results/{result_id}",
                    headers=self._headers,
                    timeout=30,
                )
                final.raise_for_status()
                return final.json()["query_result"]["data"]["rows"]
            elif status == 4:
                raise RuntimeError(f"Redash query failed: {job.get('error')}")

            time.sleep(POLL_INTERVAL)

    def close(self) -> None:
        pass  # stateless HTTP — nothing to release
