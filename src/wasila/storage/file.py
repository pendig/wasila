from __future__ import annotations

from pathlib import Path
from typing import Any

from wasila.core.ports import CustomerMemoryStore, KnowledgeLoader


class CustomerMarkdownStore(CustomerMemoryStore):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)

    def memory_path(self, customer_id: str) -> Path:
        return self.base_dir / customer_id / "customer.md"

    def ensure(self, customer_id: str, display_name: str | None = None) -> Path:
        path = self.memory_path(customer_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            header = f"# Customer Memory\n\n## Identity\n- Customer ID: {customer_id}\n"
            if display_name:
                header += f"- Display Name: {display_name}\n"
            header += "\n## Preferences\n\n## Special Handling\n\n## Important History\n\n## Open Risks\n\n## Owner Notes\n"
            path.write_text(header + "\n", encoding="utf-8")
        return path

    def read(self, customer_id: str) -> str:
        path = self.memory_path(customer_id)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def upsert_section(self, customer_id: str, section: str, body: str) -> None:
        path = self.ensure(customer_id)
        text = path.read_text(encoding="utf-8")
        marker = f"## {section}"
        lines = text.splitlines()
        try:
            index = lines.index(marker)
            insert_at = index + 1
            while insert_at < len(lines) and not lines[insert_at].startswith("## "):
                insert_at += 1
            block = [f"- {body.strip()}"]
            lines[insert_at:insert_at] = block
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
        except ValueError:
            pass

        if not text.endswith("\n"):
            text += "\n"
        text += f"\n{marker}\n- {body.strip()}\n"
        path.write_text(text, encoding="utf-8")


class MarkdownKnowledgeLoader(KnowledgeLoader):
    FILES = ("business.md", "products.md", "policies.md", "support.md", "owner.md")

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = Path(knowledge_dir)

    def load_markdown(self) -> str:
        parts: list[str] = []
        for filename in self.FILES:
            path = self.knowledge_dir / filename
            if not path.exists():
                continue
            body = path.read_text(encoding="utf-8")
            if not body.strip():
                continue
            parts.append(f"## {filename}\n")
            parts.append(body.strip())
            parts.append("\n")
        return "\n".join(parts)

    def read_file(self, name: str) -> str:
        path = self.knowledge_dir / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
