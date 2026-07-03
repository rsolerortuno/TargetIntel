import pandas as pd


def minmax_scale(series: pd.Series) -> pd.Series:
    """
    Min-max scale a pandas Series from 0 to 1.
    """
    min_value = series.min()
    max_value = series.max()

    if max_value == min_value:
        return series * 0

    return (series - min_value) / (max_value - min_value)


def add_initial_target_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Version 0.1 score.

    Uses only Open Targets disease association evidence.
    """
    df = df.copy()

    df["opentargets_score_scaled"] = minmax_scale(df["opentargets_score"])
    df["final_score"] = df["opentargets_score_scaled"] * 100

    df = df.sort_values("final_score", ascending=False)

    return df


def add_io_weighted_target_score(
    df: pd.DataFrame,
    opentargets_weight: float = 0.7,
    io_weight: float = 0.3,
) -> pd.DataFrame:
    """
    Version 0.2 score.

    Combines Open Targets melanoma association evidence with a simple
    immuno-oncology relevance score.
    """
    df = df.copy()

    df["opentargets_score_scaled"] = minmax_scale(df["opentargets_score"])

    if "immuno_oncology_score" not in df.columns:
        df["immuno_oncology_score"] = 0.0

    df["final_score"] = (
        opentargets_weight * df["opentargets_score_scaled"]
        + io_weight * df["immuno_oncology_score"]
    ) * 100

    df = df.sort_values("final_score", ascending=False)

    return df
