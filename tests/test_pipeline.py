"""Tests for the TargetIntel-IO end-to-end pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import targetintel.pipeline as pipeline


def test_run_core_pipeline_builds_data_once(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[
        tuple[str, object]
    ] = []

    feature_df = pd.DataFrame(
        {
            "target_symbol": [
                "CTLA4",
                "B2M",
                "BRAF",
            ],
            "opentargets_score": [
                0.8,
                0.7,
                0.9,
            ],
        }
    )

    ranked_df = feature_df.assign(
        antibody_io_rank=[
            1,
            2,
            3,
        ],
        biomarker_rank=[
            2,
            1,
            3,
        ],
        small_molecule_rank=[
            3,
            2,
            1,
        ],
    )

    def fake_build_feature_table(
        *,
        page_size: int,
        max_pages: int,
        refresh: bool,
    ) -> pd.DataFrame:
        calls.append(
            (
                "build_feature_table",
                (
                    page_size,
                    max_pages,
                    refresh,
                ),
            )
        )

        return feature_df

    def fake_save_feature_table(
        dataframe: pd.DataFrame,
        output_path: Path,
    ) -> Path:
        calls.append(
            (
                "save_feature_table",
                output_path,
            )
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataframe.to_csv(
            output_path,
            index=False,
        )

        return output_path

    def fake_build_intent_rankings(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        calls.append(
            (
                "build_intent_rankings",
                len(dataframe),
            )
        )

        return ranked_df

    def fake_save_ranked_targets(
        dataframe: pd.DataFrame,
        output_path: Path,
    ) -> Path:
        calls.append(
            (
                "save_ranked_targets",
                output_path,
            )
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataframe.to_csv(
            output_path,
            index=False,
        )

        return output_path

    def fake_write_cards(
        dataframe: pd.DataFrame,
        *,
        output_dir: Path,
        top_n_per_mode: int,
    ) -> list[Path]:
        calls.append(
            (
                "write_cards",
                top_n_per_mode,
            )
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = output_dir / "CTLA4.md"
        path.write_text(
            "# CTLA4\n",
            encoding="utf-8",
        )

        return [
            path,
        ]

    def fake_write_html(
        dataframe: pd.DataFrame,
        *,
        output_dir: Path,
        top_n_per_mode: int,
    ) -> list[Path]:
        calls.append(
            (
                "write_html",
                top_n_per_mode,
            )
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = output_dir / "index.html"
        path.write_text(
            "<html></html>\n",
            encoding="utf-8",
        )

        return [
            path,
        ]

    def fake_generate_figures(
        dataframe: pd.DataFrame,
        *,
        output_dir: Path,
        top_n: int,
        heatmap_top_n_per_mode: int,
    ) -> list[Path]:
        calls.append(
            (
                "generate_figures",
                (
                    top_n,
                    heatmap_top_n_per_mode,
                ),
            )
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = output_dir / "overview.png"
        path.write_bytes(
            b"png"
        )

        return [
            path,
        ]

    monkeypatch.setattr(
        pipeline,
        "build_feature_table",
        fake_build_feature_table,
    )
    monkeypatch.setattr(
        pipeline,
        "save_feature_table",
        fake_save_feature_table,
    )
    monkeypatch.setattr(
        pipeline,
        "build_intent_rankings",
        fake_build_intent_rankings,
    )
    monkeypatch.setattr(
        pipeline,
        "save_ranked_targets",
        fake_save_ranked_targets,
    )
    monkeypatch.setattr(
        pipeline,
        "write_top_target_cards",
        fake_write_cards,
    )
    monkeypatch.setattr(
        pipeline,
        "write_top_html_reports",
        fake_write_html,
    )
    monkeypatch.setattr(
        pipeline,
        "generate_summary_figures",
        fake_generate_figures,
    )

    outputs = pipeline.run_core_pipeline(
        page_size=50,
        max_pages=2,
        refresh=True,
        top_n_per_mode=4,
        project_root=tmp_path,
    )

    assert [
        name
        for name, _ in calls
    ] == [
        "build_feature_table",
        "save_feature_table",
        "build_intent_rankings",
        "save_ranked_targets",
        "write_cards",
        "write_html",
        "generate_figures",
    ]

    assert outputs.feature_table.is_file()
    assert outputs.ranked_targets.is_file()
    assert (
        outputs.html_reports_dir
        / "index.html"
    ).is_file()

    assert outputs.benchmark_dir is None
    assert outputs.sensitivity_dir is None


def test_validation_pipeline_runs_expected_commands(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commands: list[
        list[str]
    ] = []

    def fake_run_command(
        command,
        *,
        project_root: Path,
    ) -> None:
        assert project_root == tmp_path.resolve()

        commands.append(
            list(command)
        )

    monkeypatch.setattr(
        pipeline,
        "_run_command",
        fake_run_command,
    )

    benchmark_dir, sensitivity_dir = (
        pipeline.run_validation_pipeline(
            page_size=50,
            max_pages=2,
            refresh=True,
            project_root=tmp_path,
        )
    )

    assert len(commands) == 4

    assert (
        "scripts/09_build_benchmark_universe.py"
        in commands[0]
    )
    assert "--refresh" in commands[0]

    assert (
        "scripts/08_run_benchmark.py"
        in commands[1]
    )
    assert (
        "scripts/11_run_sensitivity_analysis.py"
        in commands[2]
    )
    assert (
        "scripts/12_generate_sensitivity_figure.py"
        in commands[3]
    )

    assert benchmark_dir == (
        tmp_path.resolve()
        / "results"
        / "benchmark"
    )

    assert sensitivity_dir == (
        tmp_path.resolve()
        / "results"
        / "sensitivity"
    )


def test_pipeline_rejects_invalid_positive_arguments(
    tmp_path: Path,
) -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="page_size",
    ):
        pipeline.run_core_pipeline(
            page_size=0,
            project_root=tmp_path,
        )

    with pytest.raises(
        ValueError,
        match="top_n_per_mode",
    ):
        pipeline.run_core_pipeline(
            top_n_per_mode=0,
            project_root=tmp_path,
        )
