"""Isolation locks: constructed dependency evidence is presentation-only."""
from __future__ import annotations

import ast
import builtins
import io
from pathlib import Path
import socket
import urllib.request

import pandas as pd
import requests

import targetintel.pipeline as pipeline
from targetintel.functional_dependency.presentation import render_dependency_html, render_dependency_markdown
from targetintel.html_reports import make_target_html_report, write_top_html_reports
from targetintel.hypothesis_cards import make_target_card, write_top_target_cards
from test_depmap_reporting_regression import _evidence, _row


def _forbidden(*_args, **_kwargs):
    raise AssertionError("upstream, file, environment, or network access invoked")


def _guard_network(monkeypatch) -> None:
    """Fail on each common transport surface, not only socket creation."""
    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)
    monkeypatch.setattr(requests, "request", _forbidden)
    monkeypatch.setattr(requests, "get", _forbidden)
    monkeypatch.setattr(requests, "post", _forbidden)
    monkeypatch.setattr(requests, "Session", _forbidden)


def test_pure_renderers_are_in_memory_and_do_not_import_execution_or_snapshot_layers(monkeypatch) -> None:
    import os
    root = Path(__file__).parents[1] / "targetintel" / "functional_dependency"
    source_by_name = {
        name: (root / name).read_text(encoding="utf-8")
        for name in ("report_contract.py", "report_snapshot.py", "presentation.py")
    }
    monkeypatch.setattr(builtins, "open", _forbidden)
    monkeypatch.setattr(io, "open", _forbidden)
    monkeypatch.setattr(Path, "open", _forbidden)
    monkeypatch.setattr(os, "getenv", _forbidden)
    _guard_network(monkeypatch)
    evidence = _evidence()
    assert "Functional dependency" in render_dependency_markdown(evidence)
    assert "functional-dependency" in render_dependency_html(evidence)
    forbidden_imports = {
        "report_snapshot", "hypothesis_cards", "html_reports", "pipeline", "ingestion", "profiles",
        "benchmark", "integration",
    }
    for name, source in source_by_name.items():
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[-1]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
            for alias in node.names
        }
        assert not imports & forbidden_imports
    assert "dependency_profiles.jsonl" not in source_by_name["presentation.py"]
    assert "CRISPRGeneEffect" not in source_by_name["presentation.py"]
    assert "CRISPRGeneDependency" not in source_by_name["presentation.py"]


def test_card_and_html_rendering_survive_forbidden_upstream_systems(monkeypatch) -> None:
    import targetintel.feature_table as feature_table
    import targetintel.intent_ranking as ranking
    import targetintel.role_classifier as roles
    import targetintel.scoring as scoring
    import targetintel.functional_dependency.depmap_ingestion as ingestion
    import targetintel.functional_dependency.depmap_profiles as profiles
    for module, name in ((feature_table, "build_feature_table"), (ranking, "build_intent_rankings"),
                         (roles, "classify_gene"), (scoring, "score_all_profiles"),
                         (ingestion, "ingest_local_release"), (profiles, "build_dependency_profiles")):
        monkeypatch.setattr(module, name, _forbidden)
    _guard_network(monkeypatch)
    assert "Functional dependency" in make_target_card(_row(), dependency_evidence=_evidence())
    assert "functional-dependency" in make_target_html_report(_row(), dependency_evidence=_evidence())


def test_rendering_cannot_open_depmap_matrices_or_profile_artifacts(monkeypatch) -> None:
    """Synthetic report evidence must make all matrix and JSONL I/O unnecessary."""
    import os
    monkeypatch.setattr(builtins, "open", _forbidden)
    monkeypatch.setattr(io, "open", _forbidden)
    monkeypatch.setattr(Path, "open", _forbidden)
    monkeypatch.setattr(os, "getenv", _forbidden)
    _guard_network(monkeypatch)

    evidence = _evidence()
    assert "Functional dependency" in render_dependency_markdown(evidence)
    assert "functional-dependency" in render_dependency_html(evidence)
    assert "Functional dependency" in make_target_card(_row(), dependency_evidence=evidence)
    assert "functional-dependency" in make_target_html_report(_row(), dependency_evidence=evidence)


def test_writers_are_confined_to_explicit_tmp_destination_and_leave_inputs_unchanged(tmp_path: Path) -> None:
    frame = pd.DataFrame([_row("BRAF", 1), _row("NRAS", 2)])
    before = frame.copy(deep=True)
    mapping = {"BRAF": _evidence()}
    cards = write_top_target_cards(frame, tmp_path / "cards", top_n_per_mode=2, dependency_evidence_by_symbol=mapping)
    html = write_top_html_reports(frame, tmp_path / "html", top_n_per_mode=2, dependency_evidence_by_symbol=mapping)
    assert set(tmp_path.rglob("*")) == set(cards) | set(html) | {tmp_path / "cards", tmp_path / "html"}
    assert all(path.is_relative_to(tmp_path) for path in cards + html)
    pd.testing.assert_frame_equal(frame, before)
    assert mapping == {"BRAF": _evidence()}


def test_productive_pipeline_is_unwired_from_dependency_evidence(monkeypatch, tmp_path: Path) -> None:
    frame = pd.DataFrame([_row("BRAF", 1)])
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(pipeline, "build_feature_table", lambda **_k: frame.copy())
    monkeypatch.setattr(pipeline, "save_feature_table", lambda _df, path: path)
    monkeypatch.setattr(pipeline, "build_intent_rankings", lambda df: df.copy())
    monkeypatch.setattr(pipeline, "save_ranked_targets", lambda _df, path: path)
    def writer(name):
        def call(df, **kwargs):
            calls.append((name, (df.copy(), kwargs)))
            return []
        return call
    monkeypatch.setattr(pipeline, "write_top_target_cards", writer("cards"))
    monkeypatch.setattr(pipeline, "write_top_html_reports", writer("html"))
    monkeypatch.setattr(pipeline, "generate_summary_figures", lambda *_a, **_k: [])
    outputs = pipeline.run_core_pipeline(project_root=tmp_path, top_n_per_mode=1)
    assert outputs.target_cards_dir == tmp_path / "results" / "target_cards"
    assert [name for name, _ in calls] == ["cards", "html"]
    for _, (passed, kwargs) in calls:
        pd.testing.assert_frame_equal(passed, frame)
        assert "dependency_evidence_by_symbol" not in kwargs
