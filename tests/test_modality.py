"""Tests for modality-aware target reasoning."""

from targetintel.modality import assign_modality_fit
from targetintel.role_classifier import classify_gene


def _modality_call(symbol: str, resistance_axis: str):
    role = classify_gene(
        symbol,
        resistance_axis=resistance_axis,
    )

    return assign_modality_fit(
        gene_symbol=symbol,
        role_classification=role.role_classification,
        therapeutic_direction=role.therapeutic_direction,
        resistance_axis=resistance_axis,
    )


def test_lag3_is_antibody_io_candidate() -> None:
    call = _modality_call(
        "LAG3",
        "checkpoint_redundancy",
    )

    assert call.antibody_fit == "high"
    assert call.io_combination_fit == "high"
    assert call.small_molecule_fit == "low"
    assert call.poor_direct_target_flag is False
    assert call.best_modality == "antibody / IO-combination target"


def test_b2m_is_biomarker_candidate() -> None:
    call = _modality_call(
        "B2M",
        "antigen_presentation_loss",
    )

    assert call.biomarker_fit == "high"
    assert call.poor_direct_target_flag is False
    assert "biomarker" in call.best_modality.lower()


def test_braf_is_small_molecule_candidate() -> None:
    call = _modality_call(
        "BRAF",
        "tumor_intrinsic_driver",
    )

    assert call.small_molecule_fit == "high"
    assert call.antibody_fit == "low"
    assert call.poor_direct_target_flag is False
    assert "small molecule" in call.best_modality.lower()


def test_cdkn2a_is_poor_direct_target() -> None:
    call = _modality_call(
        "CDKN2A",
        "tumor_intrinsic_driver",
    )

    assert call.poor_direct_target_flag is True
    assert call.antibody_fit == "low"
    assert "biomarker" in call.best_modality.lower()
