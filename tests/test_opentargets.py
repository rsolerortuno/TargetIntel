"""Tests for Open Targets payload conversion without network access."""

from targetintel.opentargets import (
    associated_targets_to_dataframe,
    scored_components_to_dict,
)


def test_scored_components_to_dict() -> None:
    result = scored_components_to_dict(
        [
            {"id": "genetic_association", "score": 0.8},
            {"id": "known_drug", "score": 0.4},
            {"id": None, "score": 0.2},
        ]
    )

    assert result == {
        "genetic_association": 0.8,
        "known_drug": 0.4,
    }


def test_associated_targets_payload_to_dataframe() -> None:
    payload = {
        "disease": {
            "id": "MONDO_0005105",
            "name": "melanoma",
        },
        "associatedTargets": {
            "count": 2,
            "rows": [
                {
                    "score": 0.50,
                    "datatypeScores": [],
                    "datasourceScores": [],
                    "target": {
                        "id": "ENSG_CTLA4",
                        "approvedSymbol": "CTLA4",
                        "approvedName": "CTLA-4",
                        "biotype": "protein_coding",
                    },
                },
                {
                    "score": 0.90,
                    "datatypeScores": [],
                    "datasourceScores": [],
                    "target": {
                        "id": "ENSG_BRAF",
                        "approvedSymbol": "BRAF",
                        "approvedName": "B-Raf",
                        "biotype": "protein_coding",
                    },
                },
            ],
        },
    }

    df = associated_targets_to_dataframe(payload)

    assert len(df) == 2
    assert df.iloc[0]["target_symbol"] == "BRAF"
    assert df.iloc[0]["opentargets_score"] == 0.90
    assert df.iloc[1]["target_symbol"] == "CTLA4"
    assert set(df["disease_id"]) == {"MONDO_0005105"}
