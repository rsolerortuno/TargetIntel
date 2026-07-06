"""
Simple JSON caching utilities for TargetIntel-IO.

The project uses public APIs such as Open Targets, PubMed, and ClinicalTrials.gov.
To make the workflow reproducible and avoid repeated API calls, fetched results
are stored locally and reused unless refresh=True is requested.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_CACHE_DIR = Path("data/cache")


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).isoformat()


def ensure_parent_dir(path: str | Path) -> Path:
    """Create the parent directory for a file path if it does not exist."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: str | Path) -> Any:
    """
    Load a JSON file.

    Parameters
    ----------
    path:
        Path to JSON file.

    Returns
    -------
    Any
        Parsed JSON content.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Cache file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data: Any, path: str | Path, indent: int = 2) -> Path:
    """
    Save data as JSON.

    Parameters
    ----------
    data:
        JSON-serializable object.
    path:
        Output JSON path.
    indent:
        JSON indentation level.

    Returns
    -------
    pathlib.Path
        Path where the JSON file was saved.
    """
    path = ensure_parent_dir(path)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent, ensure_ascii=False)

    return path


def cache_exists(path: str | Path) -> bool:
    """Check whether a cache file exists."""
    return Path(path).exists()


def get_or_fetch_json(
    cache_path: str | Path,
    fetch_fn: Callable[[], Any],
    refresh: bool = False,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """
    Load data from cache if available, otherwise fetch and cache it.

    Parameters
    ----------
    cache_path:
        Path to the cache JSON file.
    fetch_fn:
        Function that fetches or generates the data if cache is missing.
    refresh:
        If True, ignore existing cache and fetch data again.
    source:
        Optional name of the data source.
    metadata:
        Optional metadata to store alongside the cached data.

    Returns
    -------
    Any
        Cached or freshly fetched data payload.

    Notes
    -----
    The saved cache file has the following structure:

    {
      "created_at": "...",
      "source": "...",
      "metadata": {...},
      "data": ...
    }

    The function returns only the "data" field to downstream code.
    """
    cache_path = Path(cache_path)

    if cache_path.exists() and not refresh:
        cached = load_json(cache_path)

        if isinstance(cached, dict) and "data" in cached:
            return cached["data"]

        # Backward-compatible behavior if a raw JSON object was cached.
        return cached

    data = fetch_fn()

    cache_payload = {
        "created_at": utc_now_iso(),
        "source": source,
        "metadata": metadata or {},
        "data": data,
    }

    save_json(cache_payload, cache_path)

    return data


def clear_cache_file(path: str | Path) -> None:
    """
    Delete a cache file if it exists.

    This is useful for tests or manual refresh workflows.
    """
    path = Path(path)

    if path.exists():
        path.unlink()
