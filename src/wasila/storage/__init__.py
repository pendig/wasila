"""Storage adapters for Wasila."""

from wasila.storage.file import CustomerMarkdownStore, MarkdownKnowledgeLoader
from wasila.storage.sqlite import SqliteStorage

__all__ = ["CustomerMarkdownStore", "MarkdownKnowledgeLoader", "SqliteStorage"]
