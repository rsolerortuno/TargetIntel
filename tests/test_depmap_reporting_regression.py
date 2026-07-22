"""Cross-module compatibility locks for optional DepMap report decoration."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from targetintel.evidence.reporting import EvidenceReportDecorator
from targetintel.functional_dependency.report_contract import DependencyReportEvidence
from targetintel.html_reports import make_target_html_report, write_top_html_reports
from targetintel.hypothesis_cards import make_target_card, write_top_target_cards
from test_feasibility_presentation import _annotation, _observation
from tests.test_evidence_models import evidence_item


def _evidence(symbol: str = "BRAF", **changes: object) -> DependencyReportEvidence:
    values: dict[str, object] = {
        "format_version": "v1", "release_identifier": "DepMap_Public_26Q1",
        "release_manifest_id": "manifest", "configuration_id": "configuration",
        "scientific_closure_identity": "closure", "context_identity": "melanoma_anti_pd1:v1",
        "gene_symbol": symbol, "canonical_gene_identity": f"{symbol}:1", "profile_available": True,
        "coverage_status": "sufficient_complete_coverage", "model_count": 10,
        "context_model_count": 4, "reference_model_count": 6,
        "available_context_observations": 4, "available_reference_observations": 6,
        "coverage_fraction": 1.0, "missing_value_state": "resolved", "unavailable_reason": None,
        "gene_effect": {"median": 0.0}, "dependency_probability": {"median": None},
        "context_reference_comparison": {"median_delta": -0.2}, "selectivity": {"value": 50.0},
        "dependency_interpretation_state": "valid", "baseline_rank": 7,
        "dependency_aware_candidate_rank": 5, "rank_delta": -2,
        "integration_state": "human_review_required", "baseline_preserved": True,
        "production_activation_enabled": False, "approved_authorization_emitted": False,
        "candidate_activation_readiness": "blocked", "human_review_required": True,
        "limitations": ("A local limitation.",),
        "provenance": {"source_artifact_names": ["a.json", "b.tsv"]},
    }
    values.update(changes)
    return DependencyReportEvidence.create(**values)


def _row(symbol: str = "BRAF", rank: int = 1) -> pd.Series:
    return pd.Series({"target_symbol": symbol, "target_name": f"{symbol} name", "opentargets_score": 0.7,
                      "opentargets_rank": rank, "role_classification": "tumor-intrinsic driver",
                      "antibody_io_rank": rank, "biomarker_rank": rank, "small_molecule_rank": rank})


def _ranked() -> pd.DataFrame:
    return pd.DataFrame([_row("BRAF", 1), _row("NRAS", 2)])


def _stored_evidence_card():
    item = evidence_item(evidence_id="stored", validation_status="citation_verified",
                         evidence_family="efam-v1:stored", evidence_family_basis="publication_id",
                         independence_eligible=True, independence_ineligibility_reason=None,
                         publication_id="PMID:1", experiment_id=None, patient_cohort_id=None)
    return EvidenceReportDecorator().make_card("BRAF", [item])


def _bytes(paths: list[Path]) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in paths}


def test_legacy_cards_and_html_are_byte_identical_without_dependency_evidence() -> None:
    row = _row()
    card = make_target_card(row)
    html = make_target_html_report(row)
    assert card == make_target_card(row, dependency_evidence=None)
    assert html == make_target_html_report(row, dependency_evidence=None)
    for rendered in (card, html):
        assert "Functional dependency" not in rendered
        for identifier in ("DepMap", "manifest", "configuration", "closure"):
            assert identifier not in rendered

    annotation = (_annotation("antibody", (_observation("tractability", "antibody"),)),)
    evidence_card = _stored_evidence_card()
    assert make_target_card(row, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol") == make_target_card(row, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol", dependency_evidence=None)
    assert make_target_html_report(row, evidence_card=evidence_card) == make_target_html_report(row, evidence_card=evidence_card, dependency_evidence=None)
    assert make_target_card(row, evidence_card=evidence_card, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol") == make_target_card(row, evidence_card=evidence_card, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol", dependency_evidence=None)
    assert make_target_html_report(row, evidence_card=evidence_card, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol") == make_target_html_report(row, evidence_card=evidence_card, feasibility_annotations=annotation, feasibility_target_identifier_type="gene_symbol", dependency_evidence=None)


def test_batch_writers_preserve_legacy_bytes_order_rows_and_mapping_inputs(tmp_path: Path) -> None:
    ranked = _ranked()
    before = ranked.copy(deep=True)
    mapping = {"BRAF": _evidence(), "unused": _evidence("unused")}
    mapping_before = {key: value.canonical_json() for key, value in mapping.items()}
    legacy_cards = write_top_target_cards(ranked, tmp_path / "legacy_cards", top_n_per_mode=2)
    none_cards = write_top_target_cards(ranked, tmp_path / "none_cards", top_n_per_mode=2, dependency_evidence_by_symbol=None)
    empty_cards = write_top_target_cards(ranked, tmp_path / "empty_cards", top_n_per_mode=2, dependency_evidence_by_symbol={})
    legacy_html = write_top_html_reports(ranked, tmp_path / "legacy_html", top_n_per_mode=2)
    none_html = write_top_html_reports(ranked, tmp_path / "none_html", top_n_per_mode=2, dependency_evidence_by_symbol=None)
    empty_html = write_top_html_reports(ranked, tmp_path / "empty_html", top_n_per_mode=2, dependency_evidence_by_symbol={})
    assert [p.name for p in legacy_cards] == [p.name for p in none_cards] == [p.name for p in empty_cards]
    assert _bytes(legacy_cards) == _bytes(none_cards) == _bytes(empty_cards)
    assert [p.name for p in legacy_html] == [p.name for p in none_html] == [p.name for p in empty_html]
    assert _bytes(legacy_html) == _bytes(none_html) == _bytes(empty_html)

    decorated_cards = write_top_target_cards(ranked, tmp_path / "decorated_cards", top_n_per_mode=2, dependency_evidence_by_symbol=mapping)
    decorated_html = write_top_html_reports(ranked, tmp_path / "decorated_html", top_n_per_mode=2, dependency_evidence_by_symbol=mapping)
    assert "Functional dependency" in (tmp_path / "decorated_cards" / "BRAF.md").read_text()
    assert (tmp_path / "decorated_cards" / "NRAS.md").read_bytes() == (tmp_path / "legacy_cards" / "NRAS.md").read_bytes()
    assert "Functional dependency" in (tmp_path / "decorated_html" / "BRAF.html").read_text()
    assert (tmp_path / "decorated_html" / "NRAS.html").read_bytes() == (tmp_path / "legacy_html" / "NRAS.html").read_bytes()
    assert (tmp_path / "decorated_html" / "index.html").read_bytes() == (tmp_path / "legacy_html" / "index.html").read_bytes()
    assert [p.name for p in decorated_cards] == [p.name for p in legacy_cards]
    assert [p.name for p in decorated_html] == [p.name for p in legacy_html]
    pd.testing.assert_frame_equal(ranked, before)
    assert {key: value.canonical_json() for key, value in mapping.items()} == mapping_before
    assert list(ranked["target_symbol"]) == ["BRAF", "NRAS"]
    assert set(ranked.columns) == set(before.columns)  # rendering introduces no score field
    for column in ("opentargets_score", "opentargets_rank", "antibody_io_rank", "biomarker_rank", "small_molecule_rank", "role_classification"):
        assert ranked[column].equals(before[column])


def test_all_decorations_have_deterministic_current_composition_order() -> None:
    row = _row()
    annotation = (_annotation("antibody", (_observation("tractability", "antibody"),)),)
    evidence_card = _stored_evidence_card()
    kwargs = {"evidence_card": evidence_card, "feasibility_annotations": annotation,
              "feasibility_target_identifier_type": "gene_symbol", "dependency_evidence": _evidence()}
    for rendered in (make_target_card(row, **kwargs), make_target_html_report(row, **kwargs)):
        headings = ("Stored evidence observations", "Target feasibility", "Functional dependency")
        # The feasibility HTML intentionally embeds its Markdown detail in a
        # ``pre`` element, so count its semantic section rather than its title
        # text; each optional decoration itself is emitted once.
        if rendered.startswith("<!doctype html>"):
            assert rendered.count('<section class="card"><h2>Target feasibility') == 1
            assert rendered.count('<section class="card functional-dependency">') == 1
            assert rendered.count('<h2>Stored evidence observations</h2>') == 1
        else:
            assert all(rendered.count(heading) == 1 for heading in headings)
        assert rendered.index(headings[0]) < rendered.index(headings[1]) < rendered.index(headings[2])
        dependency_section = rendered[rendered.index("Functional dependency"):]
        for claim in ("clinical recommendation", "target validation", "biomarker validation", "response prediction"):
            assert claim not in dependency_section.lower()


def test_available_and_unavailable_evidence_remain_calibrated_and_deterministic() -> None:
    row = _row()
    available = _evidence()
    unavailable = _evidence(profile_available=False, coverage_status="not_available", canonical_gene_identity=None,
                            model_count=None, context_model_count=None, reference_model_count=None,
                            available_context_observations=None, available_reference_observations=None,
                            coverage_fraction=None, missing_value_state=None, unavailable_reason="unresolved",
                            gene_effect=None, dependency_probability=None, context_reference_comparison=None,
                            selectivity=None, dependency_interpretation_state=None)
    rendered = make_target_card(row, dependency_evidence=available)
    absent = make_target_card(row, dependency_evidence=unavailable)
    assert "**Gene-effect summary:** {\"median\":0.0}" in rendered
    assert "not reported" in rendered and "0.0" in rendered
    assert "No dependency conclusion is drawn." in absent
    assert "not available" in absent and "Gene-effect summary" not in absent
    assert "non-dependent" not in absent.lower()
    assert make_target_card(row, dependency_evidence=available) == rendered
    assert make_target_html_report(row, dependency_evidence=available) == make_target_html_report(row, dependency_evidence=available)
    escaped = _evidence(gene_effect={"text": "<tag>&\""})
    escaped_html = make_target_html_report(row, dependency_evidence=escaped)
    assert "&amp;lt;tag&amp;gt;" in escaped_html and "<tag>" not in escaped_html
    reordered = {"other": _evidence("other"), "BRAF": available}
    assert make_target_card(row, dependency_evidence=reordered["BRAF"]) == rendered
    for forbidden in ("timestamp", "hostname", "/tmp/", "/home/", "mount"):
        assert forbidden not in rendered.lower()
    assert rendered.index("- A local limitation.") < rendered.index("- Absence of tumor-cell dependency")
    for marker in ("Baseline preserved:** yes", "Production activation enabled:** disabled", "Approved authorization emitted:** not emitted", "Human review required:** required"):
        assert marker in rendered
