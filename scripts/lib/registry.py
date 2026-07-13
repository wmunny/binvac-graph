"""Registro canónico ESAW/CNAE → slug de entidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from .normalize import (
    agente_family,
    cnae_division,
    is_corrupt_text,
    norm,
    slugify,
    validate_agente_code,
    validate_cnae_code,
    validate_desviacion_code,
    validate_forma_code,
)

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT / "data" / "canonical_registry.yaml"

DIMENSIONS = {
    "forma": ("formas", validate_forma_code),
    "desviacion": ("desviaciones", validate_desviacion_code),
    "agente_material": ("agentes-materiales", validate_agente_code),
    "sector": ("sectores", validate_cnae_code),
}


@dataclass
class EntityRef:
    slug: str
    titulo: str
    auto: bool = False


@dataclass
class Registry:
    entries: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> "Registry":
        if yaml is None or not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(entries=data)

    def get_entry(self, dimension: str, code: str) -> dict[str, Any] | None:
        return self.entries.get(dimension, {}).get(code)

    def _match_text_override(self, dimension: str, code: str, text: str) -> dict[str, Any] | None:
        entry = self.get_entry(dimension, code)
        if not entry:
            return None
        overrides = entry.get("text_overrides", [])
        ntext = norm(text)
        for ov in overrides:
            pattern = norm(ov.get("pattern", ""))
            if pattern and pattern in ntext:
                return {
                    "slug": ov["slug"],
                    "titulo": ov.get("titulo", entry.get("titulo", "")),
                }
        return None

    def _auto_ref(self, folder: str, lookup: str, text: str) -> EntityRef:
        return EntityRef(
            slug=f"{folder}/_auto/esaw-{lookup}",
            titulo=text or lookup,
            auto=True,
        )

    def resolve(
        self,
        dimension: str,
        code: str,
        text: str = "",
    ) -> EntityRef | None:
        if dimension not in DIMENSIONS:
            return None
        folder, validator = DIMENSIONS[dimension]

        if dimension == "agente_material":
            if not validate_agente_code(code):
                if text and not is_corrupt_text(text):
                    return EntityRef(
                        slug=f"{folder}/_auto/{slugify(text)}",
                        titulo=text,
                        auto=True,
                    )
                return None
            override = self._match_text_override(dimension, code, text)
            if override:
                return EntityRef(slug=override["slug"], titulo=override["titulo"])
            entry = self.get_entry(dimension, code)
            if entry:
                return EntityRef(slug=entry["slug"], titulo=entry.get("titulo", text))
            fam_entry = self.get_entry(dimension, agente_family(code))
            if fam_entry:
                return EntityRef(slug=fam_entry["slug"], titulo=fam_entry.get("titulo", text))
            return self._auto_ref(folder, code, text)

        if dimension == "sector":
            lookup_code = cnae_division(code) if code else ""
            if not lookup_code:
                if text and not is_corrupt_text(text):
                    return EntityRef(
                        slug=f"{folder}/_auto/{slugify(text)}",
                        titulo=text,
                        auto=True,
                    )
                return None
        else:
            if not code or not validator(code):
                if text and not is_corrupt_text(text):
                    return EntityRef(
                        slug=f"{folder}/_auto/{slugify(text)}",
                        titulo=text,
                        auto=True,
                    )
                return None
            lookup_code = code

        override = self._match_text_override(dimension, lookup_code, text)
        if override:
            return EntityRef(slug=override["slug"], titulo=override["titulo"])

        entry = self.get_entry(dimension, lookup_code)
        if entry:
            return EntityRef(slug=entry["slug"], titulo=entry.get("titulo", text))

        return self._auto_ref(folder, lookup_code, text)
