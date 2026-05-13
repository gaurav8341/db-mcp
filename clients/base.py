from abc import ABC, abstractmethod


class BaseClient(ABC):
    def __init__(self, cfg: dict):
        self.cfg = cfg

    @abstractmethod
    def connect(self) -> None:
        """Authenticate and open connection."""

    @abstractmethod
    def execute(self, query: str) -> tuple[list[dict], bool]:
        """
        Run query. Returns (rows, truncated).
        truncated=True means there were more rows beyond the limit.
        """

    @abstractmethod
    def close(self) -> None:
        """Release connection and clean up."""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
