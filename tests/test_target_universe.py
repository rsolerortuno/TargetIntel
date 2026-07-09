"""Tests for benchmark target-universe augmentation."""

import pandas as pd

from targetintel.target_universe import augment_target_universe


def _base_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "target_id": ["ENSG_BRAF", "ENSG_CTLA4"],
            "target_symbol": ["BRAF", "CTLA4"],
            "target_name": ["B-Raf", "CTLA-4"],
            "biotype": ["protein_coding", "protein_coding"],
            "disease_id": ["MONDO_0005105", "MONDO_0005105"],
            "disease_name": ["melanoma", "melanoma"],
            "opentargets_score": [0.85, 0.60],
            "datatype_scores": [{}, {}],
            "datasource_scores": [{}, {}],
        }
    )


def test_missing_required_target_is_added() -> None:
    augmented = augment_target_universe(
        _base_dataframe(),
        required_symbols=["BRAF", "B2M"],
    )

    assert len(augmented) == 3
    assert set(augmented["target_symbol"]) == {
        "BRAF",
        "CTLA4",
        "B2M",
    }

    b2m = augmented.loc[
        augmented["target_symbol"].eq("B2M")
    ].iloc[0]

    assert float(b2m["opentargets_score"]) == 0.0
    assert bool(b2m["opentargets_evidence_available"]) is False
    assert b2m["target_universe_source"] == "required_symbol"
    assert b2m["disease_id"] == "MONDO_0005105"


def test_retrieved_targets_keep_opentargets_source() -> None:
    augmented = augment_target_universe(
        _base_dataframe(),
        required_symbols=["B2M"],
    )

    braf = augmented.loc[
        augmented["target_symbol"].eq("BRAF")
    ].iloc[0]

    assert bool(braf["opentargets_evidence_available"]) is True
    assert braf["target_universe_source"] == "opentargets"
    assert float(braf["opentargets_score"]) == 0.85


def test_required_symbols_are_normalized_and_deduplicated() -> None:
    augmented = augment_target_universe(
        _base_dataframe(),
        required_symbols=[" b2m ", "B2M", "tap1"],
    )

    assert augmented["target_symbol"].tolist().count("B2M") == 1
    assert augmented["target_symbol"].tolist().count("TAP1") == 1
