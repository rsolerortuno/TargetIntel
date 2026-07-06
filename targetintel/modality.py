"""
Modality-aware reasoning for TargetIntel-IO.

This module evaluates whether each candidate is a plausible fit for different
therapeutic or translational modalities:

- antibody
- small molecule
- biomarker
- IO-combination target
- poor direct therapeutic target

The logic is intentionally rule-based and transparent for the MVP.
It does not replace full target tractability assessment from resources such as
Open Targets, nor does it claim validated druggability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ModalityCall:
    """Container for modality-fit annotation."""

    antibody_fit: str
    small_molecule_fit: str
    biomarker_fit: str
    io_combination_fit: str
    poor_direct_target_flag: bool
    best_modality: str
    modality_rationale: str


SURFACE_CHECKPOINT_TARGETS = {
    "PDCD1",
    "CD274",
    "CTLA4",
    "LAG3",
    "TIGIT",
    "HAVCR2",
}

SURFACE_MYELOID_TME_TARGETS = {
    "CSF1R",
    "TREM2",
    "MARCO",
    "LILRB1",
    "LILRB2",
    "LILRB3",
    "MERTK",
    "CD163",
}

SURFACE_TREG_TARGETS = {
    "IL2RA",
    "TNFRSF18",
    "CTLA4",
}

SECRETED_OR_LIGAND_AXIS_TARGETS = {
    "TGFB1",
    "CXCL12",
}

RECEPTOR_OR_SURFACE_AXIS_TARGETS = {
    "TGFBR1",
    "TGFBR2",
    "CXCR4",
    "FAP",
}

SMALL_MOLECULE_COMPATIBLE_TARGETS = {
    "BRAF",
    "MAP2K1",
    "MAP2K2",
    "KIT",
    "CDK4",
    "MERTK",
    "AXL",
    "TGFBR1",
    "TGFBR2",
    "CXCR4",
    "IDO1",
    "ARG1",
}

BIOMARKER_RESISTANCE_TARGETS = {
    "B2M",
    "HLA-A",
    "HLA-B",
    "HLA-C",
    "TAP1",
    "TAP2",
    "JAK1",
    "JAK2",
    "IFNGR1",
    "IFNGR2",
    "STAT1",
    "IRF1",
}

POOR_DIRECT_TARGETS = {
    "CDKN2A",
    "PTEN",
    "NF1",
    "BAP1",
    "TP53",
    "RB1",
}

TUMOR_INTRINSIC_BIOMARKERS = {
    "NRAS",
    "MITF",
    "TERT",
}

IMMUNE_CONTEXT_MARKERS = {
    "CD8A",
    "CD8B",
    "GZMB",
    "PRF1",
    "CXCL9",
    "CXCL10",
    "FOXP3",
}


def normalize_symbol(gene_symbol: Any) -> str:
    """Normalize a gene symbol for rule matching."""
    if pd.isna(gene_symbol):
        return ""

    return str(gene_symbol).strip().upper()


def assign_modality_fit(
    gene_symbol: str,
    role_classification: str | None = None,
    therapeutic_direction: str | None = None,
    resistance_axis: str | None = None,
) -> ModalityCall:
    """
    Assign modality-fit labels to one candidate gene.

    Parameters
    ----------
    gene_symbol:
        HGNC-style gene symbol.
    role_classification:
        Stable role from role_classifier.py.
    therapeutic_direction:
        Therapeutic direction from role_classifier.py.
    resistance_axis:
        Resistance-axis annotation from resistance_ontology.py.

    Returns
    -------
    ModalityCall
        Modality-fit labels and rationale.
    """
    symbol = normalize_symbol(gene_symbol)
    role = (role_classification or "").lower()
    direction = (therapeutic_direction or "").lower()
    axis = (resistance_axis or "").lower()

    if symbol in SURFACE_CHECKPOINT_TARGETS:
        return ModalityCall(
            antibody_fit="high",
            small_molecule_fit="low",
            biomarker_fit="medium",
            io_combination_fit="high",
            poor_direct_target_flag=False,
            best_modality="antibody / IO-combination target",
            modality_rationale=(
                f"{symbol} is a checkpoint-axis candidate. Surface/checkpoint "
                "biology supports antibody or bispecific IO-combination strategies, "
                "while small-molecule fit is lower for this MVP."
            ),
        )

    if symbol in SURFACE_MYELOID_TME_TARGETS:
        return ModalityCall(
            antibody_fit="medium-high",
            small_molecule_fit="medium" if symbol in SMALL_MOLECULE_COMPATIBLE_TARGETS else "low-medium",
            biomarker_fit="medium",
            io_combination_fit="medium-high",
            poor_direct_target_flag=False,
            best_modality="myeloid/TME IO-combination target",
            modality_rationale=(
                f"{symbol} maps to suppressive myeloid/TME biology. This supports "
                "IO-combination hypotheses, especially for surface-accessible "
                "myeloid targets, but therapeutic direction may be context-dependent."
            ),
        )

    if symbol in SURFACE_TREG_TARGETS:
        return ModalityCall(
            antibody_fit="medium-high",
            small_molecule_fit="low",
            biomarker_fit="medium",
            io_combination_fit="medium",
            poor_direct_target_flag=False,
            best_modality="antibody / Treg-associated IO-combination candidate",
            modality_rationale=(
                f"{symbol} is associated with Treg-mediated suppression. It may "
                "fit antibody-based depletion or blockade hypotheses, but safety "
                "and immune tolerance concerns require caution."
            ),
        )

    if symbol in SECRETED_OR_LIGAND_AXIS_TARGETS:
        return ModalityCall(
            antibody_fit="medium-high",
            small_molecule_fit="low-medium",
            biomarker_fit="medium",
            io_combination_fit="medium-high",
            poor_direct_target_flag=False,
            best_modality="ligand blockade / IO-combination target",
            modality_rationale=(
                f"{symbol} is part of a secreted ligand or stromal axis. Ligand "
                "blockade can be conceptually compatible with antibody strategies, "
                "but biology is pleiotropic and patient selection may be important."
            ),
        )

    if symbol in RECEPTOR_OR_SURFACE_AXIS_TARGETS:
        return ModalityCall(
            antibody_fit="medium",
            small_molecule_fit="medium-high" if symbol in SMALL_MOLECULE_COMPATIBLE_TARGETS else "medium",
            biomarker_fit="medium",
            io_combination_fit="medium",
            poor_direct_target_flag=False,
            best_modality="TME pathway targeting / IO-combination candidate",
            modality_rationale=(
                f"{symbol} belongs to a stromal or immune-exclusion axis. It may "
                "fit pathway targeting or IO-combination hypotheses, but safety "
                "and context-dependence are important limitations."
            ),
        )

    if symbol in SMALL_MOLECULE_COMPATIBLE_TARGETS:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="high",
            biomarker_fit="medium",
            io_combination_fit="low-medium",
            poor_direct_target_flag=False,
            best_modality="small molecule / pathway targeting",
            modality_rationale=(
                f"{symbol} is best interpreted as a small-molecule or pathway "
                "target in this MVP. It should not be prioritized primarily as "
                "an antibody IO-combination target."
            ),
        )

    if symbol in BIOMARKER_RESISTANCE_TARGETS:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="low-medium",
            biomarker_fit="high",
            io_combination_fit="low-medium",
            poor_direct_target_flag=False,
            best_modality="resistance biomarker / patient stratification",
            modality_rationale=(
                f"{symbol} is best interpreted as a resistance biomarker or "
                "mechanistic marker. It may inform patient stratification but is "
                "not a strong direct therapeutic target in this MVP."
            ),
        )

    if symbol in POOR_DIRECT_TARGETS:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="low",
            biomarker_fit="medium",
            io_combination_fit="low",
            poor_direct_target_flag=True,
            best_modality="biomarker / pathway context only",
            modality_rationale=(
                f"{symbol} is biologically relevant to melanoma but is a poor "
                "direct therapeutic target for this MVP, especially for antibody "
                "or IO-combination modalities. It is better treated as pathway "
                "context, biomarker, or stratification information."
            ),
        )

    if symbol in TUMOR_INTRINSIC_BIOMARKERS:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="medium",
            biomarker_fit="medium-high",
            io_combination_fit="low-medium",
            poor_direct_target_flag=False,
            best_modality="tumor-intrinsic biomarker / pathway context",
            modality_rationale=(
                f"{symbol} is relevant to tumor-intrinsic melanoma biology. "
                "It may support biomarker or pathway-context interpretation, "
                "but direct actionability depends on downstream tractability."
            ),
        )

    if symbol in IMMUNE_CONTEXT_MARKERS:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="low",
            biomarker_fit="medium-high",
            io_combination_fit="low",
            poor_direct_target_flag=True,
            best_modality="immune-context biomarker",
            modality_rationale=(
                f"{symbol} is best interpreted as an immune-context marker rather "
                "than a causal therapeutic target. It may help describe immune-hot "
                "or immune-cold tumor states."
            ),
        )

    if "biomarker" in role or "mechanistic resistance marker" in role:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="low-medium",
            biomarker_fit="medium-high",
            io_combination_fit="low-medium",
            poor_direct_target_flag=False,
            best_modality="biomarker / patient stratification",
            modality_rationale=(
                f"{symbol} is classified as a biomarker or mechanistic marker. "
                "The strongest MVP modality is patient stratification rather than "
                "direct therapeutic targeting."
            ),
        )

    if "combination target" in role or "io-combination" in role:
        return ModalityCall(
            antibody_fit="medium",
            small_molecule_fit="low-medium",
            biomarker_fit="medium",
            io_combination_fit="medium-high",
            poor_direct_target_flag=False,
            best_modality="IO-combination target",
            modality_rationale=(
                f"{symbol} is classified as an IO-combination candidate. Modality "
                "fit is provisionally assigned from the role classifier because no "
                "more specific symbol-level modality rule exists yet."
            ),
        )

    if "tumor-intrinsic driver" in role:
        return ModalityCall(
            antibody_fit="low",
            small_molecule_fit="medium",
            biomarker_fit="medium",
            io_combination_fit="low",
            poor_direct_target_flag=False,
            best_modality="tumor-intrinsic / small-molecule context",
            modality_rationale=(
                f"{symbol} is classified as a tumor-intrinsic driver. It should be "
                "evaluated primarily in small-molecule, pathway, or biomarker modes, "
                "not as a primary antibody IO-combination target."
            ),
        )

    if axis and axis != "unmapped":
        return ModalityCall(
            antibody_fit="unclear",
            small_molecule_fit="unclear",
            biomarker_fit="medium",
            io_combination_fit="unclear",
            poor_direct_target_flag=False,
            best_modality="unclear / resistance-axis-associated candidate",
            modality_rationale=(
                f"{symbol} maps to resistance axis '{resistance_axis}', but no "
                "specific modality rule is currently available. More evidence is "
                "needed before assigning a confident modality fit."
            ),
        )

    return ModalityCall(
        antibody_fit="unclear",
        small_molecule_fit="unclear",
        biomarker_fit="unclear",
        io_combination_fit="unclear",
        poor_direct_target_flag=False,
        best_modality="unclear",
        modality_rationale=(
            f"{symbol} has no curated modality rule and is not currently mapped "
            "to a TargetIntel-IO resistance axis. Its therapeutic modality fit is unclear."
        ),
    )


def annotate_modality_dataframe(
    df: pd.DataFrame,
    gene_column: str = "target_symbol",
    role_column: str = "role_classification",
    therapeutic_direction_column: str = "therapeutic_direction",
    resistance_axis_column: str = "resistance_axis",
) -> pd.DataFrame:
    """
    Add modality-fit annotations to a dataframe.

    Parameters
    ----------
    df:
        Input dataframe containing candidate targets.
    gene_column:
        Column containing gene symbols.
    role_column:
        Column containing stable role classification.
    therapeutic_direction_column:
        Column containing therapeutic direction.
    resistance_axis_column:
        Column containing resistance-axis annotation.

    Returns
    -------
    pandas.DataFrame
        Input dataframe with modality-fit columns appended.
    """
    if gene_column not in df.columns:
        raise KeyError(f"Column not found in dataframe: {gene_column}")

    df = df.copy()

    calls = []

    for _, row in df.iterrows():
        call = assign_modality_fit(
            gene_symbol=row.get(gene_column),
            role_classification=row.get(role_column, ""),
            therapeutic_direction=row.get(therapeutic_direction_column, ""),
            resistance_axis=row.get(resistance_axis_column, ""),
        )
        calls.append(call.__dict__)

    calls_df = pd.DataFrame(calls)

    for column in calls_df.columns:
        df[column] = calls_df[column]

    return df
