"""Tests de normalización ESAW/CNAE."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.normalize import (  # noqa: E402
    cnae_division,
    norm,
    validate_desviacion_code,
    validate_forma_code,
)


def test_norm_unifica_guiones():
    assert norm("Quedar atrapado – entre") == norm("Quedar atrapado - entre")


def test_validate_forma_code():
    assert validate_forma_code("63")
    assert not validate_forma_code("40140301001011040111000000")


def test_validate_desviacion_code():
    assert validate_desviacion_code("33")
    assert not validate_desviacion_code("3304")


def test_cnae_division():
    assert cnae_division("412") == "41"
    assert cnae_division("310") == "31"
    assert cnae_division("454") == "45"
