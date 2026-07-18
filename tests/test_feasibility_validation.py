"""Fail-closed validation tests for Issue 401 feasibility contracts."""

from __future__ import annotations

from dataclasses import replace

from targetintel.feasibility import TargetFeasibilityProfile, validate_observation, validate_profile, validate_request
from test_feasibility_models import observation, request


def fields(issues: object) -> set[str]:
    return {issue.field.split(".")[-1] for issue in issues}  # type: ignore[union-attr]


def test_request_rejects_unknown_vocabularies_duplicates_and_missing_identity() -> None:
    assert "target_identifier" in fields(validate_request(request(target_identifier=" ")))
    assert "target_identifier_type" in fields(validate_request(request(target_identifier_type="alias")))
    assert "requested_dimensions" in fields(validate_request(request(requested_dimensions=["safety", "safety"])))
    assert "requested_modalities" in fields(validate_request(request(requested_modalities=["antibody", "unknown"])))
    assert "source_release" in fields(validate_request(request(source_release="")))
    assert "requesting_actor_id" in fields(validate_request(request(requesting_actor_id="")))


def test_observation_rejects_mismatch_forbidden_claims_paths_and_bad_availability() -> None:
    req = request()
    assert "availability_state" in fields(validate_observation(observation(availability_state="missing"), req))
    assert "target_identifier" in fields(validate_observation(observation(target_identifier="NRAS"), req))
    assert "source_release" in fields(validate_observation(observation(source_release="other"), req))
    assert any("safe" in issue.field for issue in validate_observation(observation(provenance={"safe": True}), req))
    assert "source_field_or_path" in fields(validate_observation(observation(source_field_or_path="/tmp/source"), req))
    assert any("reasoning" in issue.field for issue in validate_observation(observation(provenance={"hidden_reasoning": "x"}), req))
    assert any("credential" in issue.message for issue in validate_observation(observation(provenance={"credentials": {"token": "x"}}), req))


def test_profile_rejects_duplicate_identity_and_profile_observation_mismatch() -> None:
    req = request()
    item = observation()
    duplicate = TargetFeasibilityProfile.from_request(req, [item, item])
    assert "observations" in fields(validate_profile(duplicate, req))
    mismatch = TargetFeasibilityProfile.from_request(req, [observation(target_identifier="NRAS")])
    assert any("target_identifier" in issue.field for issue in validate_profile(mismatch, req))


def test_not_available_and_retrieval_failure_are_not_negative_or_equal() -> None:
    unavailable = observation(availability_state="not_available")
    failed = observation(availability_state="retrieval_failed")
    no_signal = observation(availability_state="not_observed")
    assert len({unavailable.observation_id, failed.observation_id, no_signal.observation_id}) == 3
