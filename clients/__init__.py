from .base import BaseClient
from .clickhouse import ClickHouseClient
from .metabase import MetabaseClient
from .mongo import MongoDBClient
from .mysql import MySQLClient
from .redash import RedashClient

REGISTRY: dict[str, type[BaseClient]] = {
    "mysql": MySQLClient,
    "mongodb": MongoDBClient,
    "clickhouse": ClickHouseClient,
    "redash": RedashClient,
    "metabase": MetabaseClient,
}


def get_client(cfg: dict) -> BaseClient:
    ds_type = cfg.get("type")
    cls = REGISTRY.get(ds_type)
    if cls is None:
        raise ValueError(f"Unsupported datasource type '{ds_type}'. Supported: {list(REGISTRY)}")
    return cls(cfg)
