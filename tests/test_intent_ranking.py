"""Tests for deterministic therapeutic-intent ranking."""

import pandas as pd

from targetintel.intent_ranking import (
    add_intent_ranks,
    add_opentargets_rank,
    add_rank_shift_vs_opentargets,
    assign_priority_label,
)


def test_priority_label_boundaries() -> None:
    assert assign_priority_label(0.90) == "high"
    assert assign_priority_label(0.70) == "high"
    assert assign_priority_label(0.69) == "medium"
    assert assign_priority_label(0.45) == "medium"
    assert assign_priority_label(0.11) == "low"
    assert assign_priority_label(0.10) == "not prioritized"
    assert assign_priority_label(0.00) == "not prioritized"
    assert assign_priority_label(float("nan")) == "not prioritized"


def test_only_retrieved_targets_receive_opentargets_rank() -> None:
    df = pd.DataFrame(
        {
            "target_symbol": ["BRAF", "CTLA4", "B2M"],
            "opentargets_score": [0.85, 0.60, 0.0],
            "opentargets_evidence_available": [True, True, False],
        }
    )

    ranked = add_opentargets_rank(df)

    assert ranked.loc[0, "opentargets_rank"] == 1
    assert ranked.loc[1, "opentargets_rank"] == 2
    assert pd.isna(ranked.loc[2, "opentargets_rank"])


def test_intent_rank_uses_opentargets_as_tie_breaker() -> None:
    df = pd.DataFrame(
        {
            "target_symbol": ["LOW_OT", "HIGH_OT", "BEST"],
            "opentargets_score": [0.20, 0.80, 0.50],
            "antibody_io_final_score": [0.50, 0.50, 0.90],
        }
    )

    ranked = add_intent_ranks(
        df,
        profile_ids=["antibody_io"],
    )

    ranks = ranked.set_index("target_symbol")["antibody_io_rank"]

    assert ranks["BEST"] == 1
    assert ranks["HIGH_OT"] == 2
    assert ranks["LOW_OT"] == 3


def test_rank_shift_is_missing_without_opentargets_evidence() -> None:
    df = pd.DataFrame(
        {
            "target_symbol": ["BRAF", "B2M"],
            "opentargets_score": [0.85, 0.0],
            "opentargets_evidence_available": [True, False],
            "small_molecule_final_score": [0.90, 0.10],
        }
    )

    df = add_opentargets_rank(df)
    df = add_intent_ranks(
        df,
        profile_ids=["small_molecule"],
    )
    df = add_rank_shift_vs_opentargets(
        df,
        profile_ids=["small_molecule"],
    )

    assert df.loc[0, "small_molecule_rank_shift_vs_opentargets"] == 0
    assert pd.isna(
        df.loc[1, "small_molecule_rank_shift_vs_opentargets"]
    )
