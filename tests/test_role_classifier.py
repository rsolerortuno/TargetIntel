"""Tests for the stable translational role classifier."""

import pytest

from targetintel.role_classifier import classify_gene, normalize_symbol


@pytest.mark.parametrize(
    ("symbol", "expected_role"),
    [
        ("LAG3", "anti-PD-1 combination target"),
        ("B2M", "antigen-presentation resistance biomarker"),
        ("JAK1", "IFN-gamma resistance mechanism / biomarker"),
        ("TREM2", "myeloid/TME anti-PD-1 combination target"),
        ("BRAF", "tumor-intrinsic driver / small-molecule target"),
        (
            "CDKN2A",
            "tumor-intrinsic driver / poor direct therapeutic target",
        ),
        ("NRAS", "tumor-intrinsic driver / biomarker"),
        ("PRF1", "immune-context marker"),
        (
            "FOXP3",
            "Treg-suppression marker / possible IO-combination target",
        ),
    ],
)
def test_expected_role_classification(
    symbol: str,
    expected_role: str,
) -> None:
    call = classify_gene(symbol)

    assert call.role_classification == expected_role
    assert call.role_confidence
    assert call.therapeutic_direction


def test_unknown_gene_is_low_confidence() -> None:
    call = classify_gene("UNKNOWN_TARGET")

    assert call.role_classification == "unclear / low-confidence candidate"
    assert call.role_confidence == "low"
    assert call.therapeutic_direction == "unclear"


@pytest.mark.parametrize(
    ("input_symbol", "expected"),
    [
        (" lag3 ", "LAG3"),
        ("braf", "BRAF"),
        ("HLA-A", "HLA-A"),
        (None, ""),
    ],
)
def test_symbol_normalization(
    input_symbol: object,
    expected: str,
) -> None:
    assert normalize_symbol(input_symbol) == expected
