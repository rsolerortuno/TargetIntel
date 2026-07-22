"""Focused scientific-boundary checks for the repository README."""
from pathlib import Path
import re


def test_readme_describes_current_v050_boundary_without_publication_claims() -> None:
    text = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    required = ("v0.5.0", "DepMap Public 26Q1", "300 genes", "56-target", "331 unique identities",
                "18,531-gene", "not a productive ranking", "Baseline scores and ranks remain unchanged",
                "optional, post-ranking", "Production activation remains disabled", "human review remains mandatory",
                "DepMap cell-line dependency is not clinical anti-PD-1 response evidence",
                "absence of tumor-cell dependency does not invalidate an immune target", "targetintel run",
                "targetintel run --validate", "python -m pytest -q", "```mermaid", "## Citation", "## Author", "## License")
    for item in required:
        assert item.lower() in text.lower()
    assert "DepMap integration as future work" not in text
    assert "real DepMap Public 26Q1 repository snapshot publication is pending Issue 512" in text
    assert not re.search(r"(?:26Q1|snapshot).{0,50}(?:already )?(?:published|downloadable|released)", text, re.I)
    assert "/home/" not in text and "/media/" not in text
    for unsupported in ("treatment recommendations", "validated therapeutic targets", "qualified biomarkers", "clinical-response predictions"):
        assert unsupported in text
