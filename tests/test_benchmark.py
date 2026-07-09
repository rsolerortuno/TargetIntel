"""Tests for the internal therapeutic-intent benchmark."""

import pandas as pd

from targetintel.benchmark import (
    NONE_INTENT,
    benchmark_config_to_dataframe,
    infer_predicted_primary_intent,
    load_benchmark_config,
)


MODES = [
    "antibody_io",
    "biomarker",
    "small_molecule",
]


def test_benchmark_configuration_contains_56_unique_targets() -> None:
    config = load_benchmark_config(
        "configs/benchmark_targets.yaml"
    )

    benchmark_df = benchmark_config_to_dataframe(config)

    assert len(benchmark_df) == 56
    assert benchmark_df["target_symbol"].nunique() == 56
    assert set(config["benchmark"]["modes"]) == set(MODES)


def test_primary_intent_uses_highest_score() -> None:
    row = pd.Series(
        {
            "prediction_available": True,
            "antibody_io_final_score": 0.20,
            "biomarker_final_score": 0.82,
            "small_molecule_final_score": 0.10,
            "antibody_io_priority": "low",
            "biomarker_priority": "high",
            "small_molecule_priority": "not prioritized",
        }
    )

    intent, score = infer_predicted_primary_intent(
        row,
        modes=MODES,
    )

    assert intent == "biomarker"
    assert score == 0.82


def test_low_scores_are_classified_as_none() -> None:
    row = pd.Series(
        {
            "prediction_available": True,
            "antibody_io_final_score": 0.05,
            "biomarker_final_score": 0.08,
            "small_molecule_final_score": 0.10,
            "antibody_io_priority": "not prioritized",
            "biomarker_priority": "not prioritized",
            "small_molecule_priority": "not prioritized",
        }
    )

    intent, score = infer_predicted_primary_intent(
        row,
        modes=MODES,
        not_prioritized_threshold=0.10,
    )

    assert intent == NONE_INTENT
    assert score == 0.10


def test_missing_prediction_is_explicit() -> None:
    row = pd.Series(
        {
            "prediction_available": False,
        }
    )

    intent, score = infer_predicted_primary_intent(
        row,
        modes=MODES,
    )

    assert intent == "__missing_prediction__"
    assert score == 0.0
