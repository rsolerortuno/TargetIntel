"""Tests for therapeutic-intent scoring profiles."""

import pandas as pd

from targetintel.modality import assign_modality_fit
from targetintel.role_classifier import classify_gene
from targetintel.scoring import score_all_profiles


def _make_target_row(
    symbol: str,
    resistance_axis: str,
    opentargets_score: float = 0.60,
) -> dict[str, object]:
    role = classify_gene(
        symbol,
        resistance_axis=resistance_axis,
    )

    modality = assign_modality_fit(
        gene_symbol=symbol,
        role_classification=role.role_classification,
        therapeutic_direction=role.therapeutic_direction,
        resistance_axis=resistance_axis,
    )

    return {
        "target_symbol": symbol,
        "opentargets_score": opentargets_score,
        "resistance_axis": resistance_axis,
        "resistance_axis_score": 1.0,
        "role_classification": role.role_classification,
        "role_confidence": role.role_confidence,
        "therapeutic_direction": role.therapeutic_direction,
        "antibody_fit": modality.antibody_fit,
        "small_molecule_fit": modality.small_molecule_fit,
        "biomarker_fit": modality.biomarker_fit,
        "io_combination_fit": modality.io_combination_fit,
        "poor_direct_target_flag": modality.poor_direct_target_flag,
        "best_modality": modality.best_modality,
        "confidence_level": "high confidence",
        "contradiction_score": 0.10,
    }


def test_scoring_creates_all_intent_scores() -> None:
    df = pd.DataFrame(
        [
            _make_target_row(
                "LAG3",
                "checkpoint_redundancy",
            )
        ]
    )

    scored = score_all_profiles(df)

    assert "antibody_io_final_score" in scored.columns
    assert "biomarker_final_score" in scored.columns
    assert "small_molecule_final_score" in scored.columns


def test_lag3_prefers_antibody_io_mode() -> None:
    scored = score_all_profiles(
        pd.DataFrame(
            [
                _make_target_row(
                    "LAG3",
                    "checkpoint_redundancy",
                )
            ]
        )
    ).iloc[0]

    assert (
        scored["antibody_io_final_score"]
        > scored["small_molecule_final_score"]
    )


def test_b2m_prefers_biomarker_mode() -> None:
    scored = score_all_profiles(
        pd.DataFrame(
            [
                _make_target_row(
                    "B2M",
                    "antigen_presentation_loss",
                )
            ]
        )
    ).iloc[0]

    assert (
        scored["biomarker_final_score"]
        > scored["antibody_io_final_score"]
    )

    assert (
        scored["biomarker_final_score"]
        > scored["small_molecule_final_score"]
    )


def test_braf_prefers_small_molecule_mode() -> None:
    scored = score_all_profiles(
        pd.DataFrame(
            [
                _make_target_row(
                    "BRAF",
                    "tumor_intrinsic_driver",
                    opentargets_score=0.85,
                )
            ]
        )
    ).iloc[0]

    assert (
        scored["small_molecule_final_score"]
        > scored["antibody_io_final_score"]
    )

    assert (
        scored["small_molecule_final_score"]
        > scored["biomarker_final_score"]
    )
