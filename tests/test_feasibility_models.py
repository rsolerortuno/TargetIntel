"""Contract serialization and immutability tests for Issue 401."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from targetintel.feasibility import FeasibilityObservation, TargetFeasibilityProfile, TargetFeasibilityRequest
from targetintel.feasibility.models import OBSERVATION_FORMAT_VERSION, REQUEST_SCHEMA_ID, REQUEST_SCHEMA_VERSION


UTC = datetime(2026, 7, 19, 10, 0, tzinfo=timezone.utc)


def request(**changes: object) -> TargetFeasibilityRequest:
    values: dict[str, object] = dict(request_schema_id=REQUEST_SCHEMA_ID, request_schema_version=REQUEST_SCHEMA_VERSION,
        target_identifier="BRAF", target_identifier_type="gene_symbol", disease_context="MONDO:0005105",
        requested_dimensions=["tractability", "safety"], requested_modalities=["protac", "antibody"],
        source_name="Open Targets", source_release="24.06", requesting_actor_id="issue-401", operational_timestamp=UTC)
    values.update(changes)
    return TargetFeasibilityRequest(**values)  # type: ignore[arg-type]


def observation(**changes: object) -> FeasibilityObservation:
    values: dict[str, object] = dict(observation_format_version=OBSERVATION_FORMAT_VERSION, target_identifier="BRAF",
        target_identifier_type="gene_symbol", dimension="safety", modality=None, factor_identifier="safety_signal",
        normalized_value=None, normalized_value_type="null", availability_state="not_available", source_name="Open Targets",
        source_release="24.06", source_record_identifier="record-1", source_field_or_path="associatedTargets.rows",
        provenance={"query": {"type": "direct"}}, limitations=["Coverage is incomplete"], operational_retrieval_timestamp=UTC)
    values.update(changes)
    return FeasibilityObservation(**values)  # type: ignore[arg-type]


def test_request_is_immutable_canonical_and_timestamp_is_not_identity() -> None:
    first = request()
    reordered = request(requested_dimensions=["safety", "tractability"], requested_modalities=["antibody", "protac"], operational_timestamp=UTC.replace(minute=1))
    assert first.request_schema_id == REQUEST_SCHEMA_ID
    assert first.request_schema_version == REQUEST_SCHEMA_VERSION
    assert first.request_id == reordered.request_id
    assert first.to_dict() == TargetFeasibilityRequest.from_dict(first.to_dict()).to_dict()
    with pytest.raises(FrozenInstanceError): first.source_name = "other"  # type: ignore[misc]


def test_observation_deeply_freezes_and_distinguishes_null_false() -> None:
    null = observation()
    false = observation(normalized_value=False, normalized_value_type="boolean", availability_state="observed")
    assert null.observation_id != false.observation_id
    with pytest.raises(TypeError): null.provenance["query"] = {}  # type: ignore[index]
    with pytest.raises(TypeError): null.provenance["query"]["type"] = "ranked"  # type: ignore[index]
    assert FeasibilityObservation.from_dict(null.to_dict()).to_dict() == null.to_dict()


def test_profile_canonicalizes_observations_and_retains_contradiction() -> None:
    req = request()
    first = observation(normalized_value="signal", normalized_value_type="string", availability_state="observed")
    second = observation(normalized_value="no_signal", normalized_value_type="string", availability_state="observed", source_record_identifier="record-2")
    profile = TargetFeasibilityProfile.from_request(req, [second, first])
    assert [item.observation_id for item in profile.observations] == sorted([first.observation_id, second.observation_id])
    assert profile.contradiction_indicators["has_contradictions"] is True
    assert profile.no_score_calculated and profile.no_ranking_modified and profile.no_role_modified
    assert profile.no_clinical_conclusion_generated and profile.research_only
    assert TargetFeasibilityProfile.from_dict(profile.to_dict()).to_dict() == profile.to_dict()
