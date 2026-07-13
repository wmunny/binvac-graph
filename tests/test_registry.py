"""Tests del registro canónico."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.registry import Registry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_resolve_forma_63():
    reg = Registry.load(ROOT / "data" / "canonical_registry.yaml")
    ref = reg.resolve("forma", "63", "Quedar atrapado, quedar aplastado")
    assert ref is not None
    assert ref.slug == "formas/atrapamiento-o-aplastamiento"


def test_desviacion_33_vuelco_override():
    reg = Registry.load(ROOT / "data" / "canonical_registry.yaml")
    ref = reg.resolve("desviacion", "33", "Vuelco de la maquina")
    assert ref is not None
    assert ref.slug == "desviaciones/vuelco-de-la-maquina"


def test_desviacion_33_caida_default():
    reg = Registry.load(ROOT / "data" / "canonical_registry.yaml")
    ref = reg.resolve("desviacion", "33", "Resbalon, derrumbamiento de agente material")
    assert ref is not None
    assert ref.slug == "desviaciones/caida-de-agente-material"
