#!/usr/bin/env python3

"""
Build the first TargetIntel-IO feature table.

This script combines:
1. Open Targets melanoma-associated targets
2. Curated anti-PD-1 resistance-axis ontology annotations

The output is the first reproducible TargetIntel-IO feature table.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from targetintel.feature_table import build_feature_table, save_feature_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the TargetIntel-IO feature table."
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of Open Targets API records per page.",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of Open Targets API pages to fetch.",
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh cached Open Targets API data.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/targetintel_feature_table_v0_1.csv"),
        help="Output feature table CSV path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    feature_df = build_feature_table(
        page_size=args.page_size,
        max_pages=args.max_pages,
        refresh=args.refresh,
    )

    output_path = save_feature_table(feature_df, args.out)

    print(f"Saved feature table to: {output_path}")
    print(f"Rows: {len(feature_df)}")
    print(f"Columns: {len(feature_df.columns)}")

    preview_columns = [
        "target_symbol",
        "opentargets_score",
        "resistance_axis",
        "matched_resistance_programs",
        "role_classification",
        "therapeutic_direction",
    ]

    available_preview_columns = [
        column for column in preview_columns if column in feature_df.columns
    ]

    print()
    print(feature_df[available_preview_columns].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
