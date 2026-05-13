from .base import BaseClient
from .metabase import MetabaseClient
from .mysql import MySQLClient
from .redash import RedashClient

REGISTRY: dict[str, type[BaseClient]] = {
    "mysql": MySQLClient,
    "redash": RedashClient,
    "metabase": MetabaseClient,
}


def get_client(cfg: dict) -> BaseClient:
    ds_type = cfg.get("type")
    cls = REGISTRY.get(ds_type)
    if cls is None:
        raise ValueError(f"Unsupported datasource type '{ds_type}'. Supported: {list(REGISTRY)}")
    return cls(cfg)
