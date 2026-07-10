"""Tests for the TargetIntel-IO command-line interface."""

from __future__ import annotations

from pathlib import Path

import targetintel.cli as cli
from targetintel.pipeline import (
    PipelineOutputs,
)


def test_cli_run_forwards_arguments(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[
        str,
        object,
    ] = {}

    outputs = PipelineOutputs(
        feature_table=tmp_path / "feature.csv",
        ranked_targets=tmp_path / "ranked.csv",
        target_cards_dir=tmp_path / "cards",
        html_reports_dir=tmp_path / "html",
        figures_dir=tmp_path / "figures",
        benchmark_dir=tmp_path / "benchmark",
        sensitivity_dir=tmp_path / "sensitivity",
    )

    def fake_run_pipeline(
        **kwargs,
    ) -> PipelineOutputs:
        captured.update(
            kwargs
        )

        return outputs

    monkeypatch.setattr(
        cli,
        "run_pipeline",
        fake_run_pipeline,
    )

    exit_code = cli.main(
        [
            "run",
            "--page-size",
            "50",
            "--max-pages",
            "2",
            "--top-n-per-mode",
            "4",
            "--refresh",
            "--validate",
        ]
    )

    assert exit_code == 0

    assert captured == {
        "page_size": 50,
        "max_pages": 2,
        "refresh": True,
        "top_n_per_mode": 4,
        "validate": True,
    }


def test_cli_help_is_available() -> None:
    parser = cli.build_parser()

    help_text = parser.format_help()

    assert "targetintel" in help_text
    assert "run" in help_text
