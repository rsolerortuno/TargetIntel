"""Regression boundary tests: feasibility cannot touch the deterministic pipeline."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd

from targetintel.feasibility import TargetFeasibilityProfile, require_valid_observation, require_valid_profile, require_valid_request
from targetintel.intent_ranking import add_intent_ranks
from targetintel.role_classifier import classify_gene
from test_feasibility_models import observation, request


def _canonical_frame(frame: pd.DataFrame) -> str:
    return frame.to_json(orient="split", index=False, date_format="iso")


def _construct() -> None:
    req = request()
    item = observation()
    profile = TargetFeasibilityProfile.from_request(req, [item])
    require_valid_request(req)
    require_valid_observation(item, req)
    require_valid_profile(profile, req)
    json.dumps(profile.to_dict(), sort_keys=True)


def _has_forbidden_architectural_import(source: str, forbidden: set[str]) -> bool:
    """Return whether source imports a prohibited architectural layer."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                forbidden.intersection(alias.name.split("."))
                for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            module_parts = (node.module or "").split(".")
            imported_parts = [
                part
                for alias in node.names
                for part in alias.name.split(".")
            ]
            if forbidden.intersection(module_parts + imported_parts):
                return True
    return False


def test_feasibility_does_not_mutate_representative_scores_ranks_roles_or_features() -> None:
    features = pd.DataFrame({"target_symbol": ["BRAF", "LAG3"], "opentargets_score": [0.9, 0.8],
        "antibody_io_final_score": [0.1, 0.9], "biomarker_final_score": [0.2, 0.3], "small_molecule_final_score": [0.9, 0.1]})
    ranked = add_intent_ranks(features)
    roles = [classify_gene("BRAF", "tumor_intrinsic_driver"), classify_gene("LAG3", "checkpoint_redundancy")]
    before = (_canonical_frame(features), _canonical_frame(ranked), repr(roles))
    _construct()
    assert before == (_canonical_frame(features), _canonical_frame(ranked), repr(roles))


def test_feasibility_modules_have_no_forbidden_architectural_imports() -> None:
    root = Path(__file__).parents[1] / "targetintel" / "feasibility"
    forbidden = {"scoring", "intent_ranking", "role_classifier", "llm", "modality"}
    for path in root.glob("*.py"):
        assert not _has_forbidden_architectural_import(
            path.read_text(encoding="utf-8"), forbidden
        ), f"forbidden architectural import in {path}"


def test_import_isolation_detects_all_supported_python_import_styles() -> None:
    forbidden = {"scoring", "intent_ranking", "role_classifier", "llm", "modality"}
    for source in (
        "import targetintel.scoring",
        "from targetintel import scoring",
        "from targetintel.scoring import score_all_profiles",
        "from targetintel import llm",
        "from . import modality",
    ):
        assert _has_forbidden_architectural_import(source, forbidden), source


def test_feasibility_does_not_invoke_scoring_ranking_role_or_llm(monkeypatch) -> None:
    import targetintel.intent_ranking as intent_ranking
    import targetintel.llm.execution as execution
    import targetintel.role_classifier as role_classifier
    import targetintel.scoring as scoring

    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden deterministic or LLM system was invoked")

    monkeypatch.setattr(scoring, "score_all_profiles", forbidden)
    monkeypatch.setattr(intent_ranking, "add_intent_ranks", forbidden)
    monkeypatch.setattr(role_classifier, "classify_gene", forbidden)
    monkeypatch.setattr(execution, "execute_request", forbidden)
    _construct()
