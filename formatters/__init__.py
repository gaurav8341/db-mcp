from .base import BaseFormatter
from .json_formatter import JsonFormatter
from .markdown_formatter import MarkdownFormatter

REGISTRY: dict[str, type[BaseFormatter]] = {
    "json": JsonFormatter,
    "markdown": MarkdownFormatter,
    "md": MarkdownFormatter,
}


def get_formatter(fmt: str) -> BaseFormatter:
    cls = REGISTRY.get(fmt.lower())
    if cls is None:
        raise ValueError(f"Unsupported format '{fmt}'. Supported: {list(REGISTRY)}")
    return cls()
