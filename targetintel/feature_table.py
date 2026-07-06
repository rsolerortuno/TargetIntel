"""
Feature table construction for TargetIntel-IO.

This module combines the Open Targets melanoma association table with the
curated anti-PD-1 resistance ontology. The resulting table is the first
TargetIntel-IO feature table used by downstream role classification,
modality reasoning, scoring, and benchmarking.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from targetintel.opentargets import get_melanoma_associated_targets
from targetintel.resistance_ontology import annotate_dataframe


DEFAULT_FEATURE_TABLE_PATH = Path(
    "data/processed/targetintel_feature_table_v0_1.csv"
)


def build_feature_table(
    page_size: int = 100,
    max_pages: int = 3,
    refresh: bool = False,
) -> pd.DataFrame:
    """
    Build the first TargetIntel-IO feature table.

    Parameters
    ----------
    page_size:
        Number of Open Targets records per API page.
    max_pages:
        Maximum number of Open Targets pages to retrieve.
    refresh:
        If True, refresh the Open Targets cache.

    Returns
    -------
    pandas.DataFrame
        Feature table containing Open Targets association features plus
        resistance-axis ontology annotations.
    """
    opentargets_df = get_melanoma_associated_targets(
        page_size=page_size,
        max_pages=max_pages,
        refresh=refresh,
    )

    feature_df = annotate_dataframe(
        opentargets_df,
        gene_column="target_symbol",
    )

    feature_df = add_initial_translational_features(feature_df)

    return feature_df


def add_initial_translational_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add simple first-pass translational features.

    These are intentionally conservative placeholders. More detailed role
    classification, modality reasoning, evidence auditing, and confidence
    scoring will be implemented in separate modules.
    """
    df = df.copy()

    df["role_classification"] = df["expected_role_from_axis"]
    df["therapeutic_direction"] = df["therapeutic_direction_from_axis"]

    df["has_resistance_axis_match"] = df["resistance_axis"].ne("unmapped")

    df["initial_priority_note"] = df.apply(
        _make_initial_priority_note,
        axis=1,
    )

    return df


def _make_initial_priority_note(row: pd.Series) -> str:
    """
    Create a short transparent note for the first feature table.
    """
    symbol = row.get("target_symbol", "unknown")
    axis = row.get("matched_resistance_programs", "")
    score = row.get("opentargets_score", None)

    if row.get("resistance_axis") == "unmapped":
        return (
            f"{symbol} is associated with melanoma in Open Targets but is not "
            "currently mapped to a curated anti-PD-1 resistance axis."
        )

    return (
        f"{symbol} is associated with melanoma in Open Targets "
        f"(score={score:.3f}) and maps to the curated resistance program: {axis}."
    )


def save_feature_table(
    df: pd.DataFrame,
    output_path: str | Path = DEFAULT_FEATURE_TABLE_PATH,
) -> Path:
    """
    Save the TargetIntel-IO feature table to CSV.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    return output_path
