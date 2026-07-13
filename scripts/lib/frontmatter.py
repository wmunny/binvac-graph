"""Parseo y escritura segura de frontmatter YAML."""

from __future__ import annotations

import re
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end]
    body = text[end + 4 :].lstrip("\n")
    if yaml is not None:
        data = yaml.safe_load(block) or {}
        if not isinstance(data, dict):
            data = {}
        return data, body
  # Fallback regex simple
    data: dict[str, Any] = {}
    for line in block.splitlines():
        m = re.match(r'^([\w_]+):\s*(.*)$', line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith('"') and raw.endswith('"'):
            data[key] = raw[1:-1]
        elif raw.startswith("[") and raw.endswith("]"):
            data[key] = [x.strip().strip('"') for x in raw[1:-1].split(",") if x.strip()]
        else:
            data[key] = raw.strip('"')
    return data, body


def dump_frontmatter(data: dict[str, Any]) -> str:
    if yaml is not None:
        block = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{block}\n---"
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f'  - "{item}"')
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f'{key}: "{value}"')
    lines.append("---")
    return "\n".join(lines)


def merge_frontmatter_field(data: dict[str, Any], key: str, value: Any) -> None:
    data[key] = value
