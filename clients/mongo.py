import json

from bson import json_util
from pymongo import MongoClient

from .base import BaseClient

ROW_LIMIT = 500
WRITE_STAGES = {"$out", "$merge"}


class MongoDBClient(BaseClient):
    """
    Query is a JSON string (extended JSON allowed, e.g. {"$oid": "..."}):
      find:      {"collection": "orders", "filter": {...}, "projection": {...},
                  "sort": {"created": -1}, "limit": 10}
      aggregate: {"collection": "orders", "pipeline": [{"$match": {...}}, ...]}
    """

    def connect(self) -> None:
        if "uri" in self.cfg:
            self._client = MongoClient(self.cfg["uri"], serverSelectionTimeoutMS=10000)
        else:
            self._client = MongoClient(
                host=self.cfg["host"],
                port=self.cfg.get("port", 27017),
                username=self.cfg.get("user"),
                password=self.cfg.get("password"),
                authSource=self.cfg.get("auth_source", "admin"),
                serverSelectionTimeoutMS=10000,
            )
        self._db = self._client[self.cfg["database"]]

    def execute(self, query: str) -> tuple[list[dict], bool]:
        q = json_util.loads(query)
        coll = self._db[q["collection"]]

        if "pipeline" in q:
            pipeline = q["pipeline"]
            if any(set(stage) & WRITE_STAGES for stage in pipeline):
                raise ValueError("write stages ($out/$merge) are not allowed")
            cursor = coll.aggregate(pipeline + [{"$limit": ROW_LIMIT + 1}])
        else:
            limit = min(q.get("limit", ROW_LIMIT), ROW_LIMIT)
            cursor = coll.find(q.get("filter", {}), q.get("projection"))
            if q.get("sort"):
                cursor = cursor.sort(list(q["sort"].items()))
            cursor = cursor.limit(limit + 1)

        rows = list(cursor)
        truncated = len(rows) > ROW_LIMIT
        rows = rows[:ROW_LIMIT]
        # make ObjectId/datetime etc. JSON-safe
        return json.loads(json_util.dumps(rows)), truncated

    def close(self) -> None:
        self._client.close()
