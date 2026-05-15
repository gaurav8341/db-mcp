from abc import ABC, abstractmethod


class BaseFormatter(ABC):
    @abstractmethod
    def format(self, rows: list[dict], meta: dict) -> str:
        """Convert rows + meta to a string ready for saving."""

    @property
    @abstractmethod
    def extension(self) -> str:
        """File extension (without dot)."""
