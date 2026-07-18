"""Fail-closed deterministic validation for feasibility contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from collections.abc import Mapping
from typing import Any

from . import models


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class ValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{issue.field}: {issue.message}" for issue in issues))


_FORBIDDEN_KEYS = frozenset({
    "credential", "credentials", "password", "secret", "api_key", "access_token", "authorization", "token",
    "reasoning", "hidden_reasoning", "thinking", "hidden_thinking", "chain_of_thought",
    "score", "scores", "ranking", "rank", "role", "roles", "safe", "is_safe", "clinical_safety", "risk_free", "clinically_safe", "no_safety_risk",
    "path", "file_path", "filesystem_path", "local_path",
})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _utc_or_none(value: Any) -> bool:
    return value is None or (isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset().total_seconds() == 0)


def _forbidden_nested(value: Any, field: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            if (key_text in _FORBIDDEN_KEYS or any(marker in key_text for marker in
                    ("credential", "reason", "think", "score", "rank", "role", "safety", "safe"))
                    or key_text.endswith("_path")):
                issues.append(ValidationIssue(f"{field}.{key}", "contains a forbidden credential, hidden-reasoning, clinical, scoring, or path field"))
            _forbidden_nested(item, f"{field}.{key}", issues)
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _forbidden_nested(item, f"{field}[{index}]", issues)


def _value_matches_type(value: Any, value_type: str) -> bool:
    if value_type == "null": return value is None
    if value_type == "boolean": return isinstance(value, bool)
    if value_type == "string": return isinstance(value, str)
    if value_type == "number": return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if value_type == "object": return isinstance(value, Mapping)
    if value_type == "array": return isinstance(value, tuple)
    return False


def validate_request(request: models.TargetFeasibilityRequest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in ("request_schema_id", "request_schema_version", "target_identifier", "target_identifier_type", "source_name", "source_release", "requesting_actor_id"):
        if not _text(getattr(request, field)):
            issues.append(ValidationIssue(field, "must be a non-empty string"))
    if request.request_schema_id != models.REQUEST_SCHEMA_ID: issues.append(ValidationIssue("request_schema_id", "must equal the stable feasibility request schema ID"))
    if request.request_schema_version != models.REQUEST_SCHEMA_VERSION: issues.append(ValidationIssue("request_schema_version", "must equal the stable feasibility request schema version"))
    if request.target_identifier_type not in models.TARGET_IDENTIFIER_TYPES: issues.append(ValidationIssue("target_identifier_type", "is not an allowed controlled-vocabulary value"))
    if request.disease_context is not None and not _text(request.disease_context): issues.append(ValidationIssue("disease_context", "must be a non-empty string or null"))
    for field, allowed in (("requested_dimensions", models.FEASIBILITY_DIMENSIONS), ("requested_modalities", models.THERAPEUTIC_MODALITIES)):
        values = getattr(request, field)
        if not isinstance(values, tuple): issues.append(ValidationIssue(field, "must be immutable"))
        if len(values) != len(set(values)): issues.append(ValidationIssue(field, "must not contain duplicates"))
        if any(value not in allowed for value in values): issues.append(ValidationIssue(field, "contains an unknown controlled-vocabulary value"))
    if not _utc_or_none(request.operational_timestamp): issues.append(ValidationIssue("operational_timestamp", "must be a timezone-aware UTC datetime or null"))
    return issues


def validate_observation(observation: models.FeasibilityObservation, request: models.TargetFeasibilityRequest | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in ("observation_format_version", "target_identifier", "target_identifier_type", "dimension", "factor_identifier", "normalized_value_type", "availability_state", "source_name", "source_release", "source_field_or_path"):
        if not _text(getattr(observation, field)): issues.append(ValidationIssue(field, "must be a non-empty string"))
    if observation.observation_format_version != models.OBSERVATION_FORMAT_VERSION: issues.append(ValidationIssue("observation_format_version", "must equal the stable observation format version"))
    if observation.target_identifier_type not in models.TARGET_IDENTIFIER_TYPES: issues.append(ValidationIssue("target_identifier_type", "is not an allowed controlled-vocabulary value"))
    if observation.dimension not in models.FEASIBILITY_DIMENSIONS: issues.append(ValidationIssue("dimension", "is not an allowed controlled-vocabulary value"))
    if observation.modality is not None and observation.modality not in models.THERAPEUTIC_MODALITIES: issues.append(ValidationIssue("modality", "is not an allowed controlled-vocabulary value or null"))
    if observation.availability_state not in models.AVAILABILITY_STATES: issues.append(ValidationIssue("availability_state", "is not an allowed controlled-vocabulary value"))
    if observation.normalized_value_type not in models.NORMALIZED_VALUE_TYPES or not _value_matches_type(observation.normalized_value, observation.normalized_value_type): issues.append(ValidationIssue("normalized_value", "does not match normalized_value_type"))
    if observation.source_record_identifier is not None and not _text(observation.source_record_identifier): issues.append(ValidationIssue("source_record_identifier", "must be a non-empty string or null"))
    if not isinstance(observation.provenance, Mapping): issues.append(ValidationIssue("provenance", "must be an immutable mapping"))
    if not isinstance(observation.limitations, tuple) or not all(_text(item) for item in observation.limitations): issues.append(ValidationIssue("limitations", "must be an immutable sequence of non-empty strings"))
    if not _utc_or_none(observation.operational_retrieval_timestamp): issues.append(ValidationIssue("operational_retrieval_timestamp", "must be a timezone-aware UTC datetime or null"))
    _forbidden_nested(observation.provenance, "provenance", issues)
    _forbidden_nested(observation.normalized_value, "normalized_value", issues)
    if observation.source_field_or_path.startswith(("/", "file://", "~", "\\\\")) or ".." in observation.source_field_or_path:
        issues.append(ValidationIssue("source_field_or_path", "must not be an arbitrary filesystem path"))
    if request is not None:
        for field in ("target_identifier", "target_identifier_type", "source_name", "source_release"):
            if getattr(observation, field) != getattr(request, field): issues.append(ValidationIssue(field, "must match the request"))
        if observation.dimension not in request.requested_dimensions: issues.append(ValidationIssue("dimension", "was not requested"))
        if observation.modality is not None and observation.modality not in request.requested_modalities: issues.append(ValidationIssue("modality", "was not requested"))
    return issues


def validate_profile(profile: models.TargetFeasibilityProfile, request: models.TargetFeasibilityRequest | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in ("profile_format_version", "request_id", "target_identifier", "target_identifier_type", "source_name", "source_release"):
        if not _text(getattr(profile, field)): issues.append(ValidationIssue(field, "must be a non-empty string"))
    if profile.profile_format_version != models.PROFILE_FORMAT_VERSION: issues.append(ValidationIssue("profile_format_version", "must equal the stable profile format version"))
    if profile.target_identifier_type not in models.TARGET_IDENTIFIER_TYPES: issues.append(ValidationIssue("target_identifier_type", "is not an allowed controlled-vocabulary value"))
    if profile.disease_context is not None and not _text(profile.disease_context): issues.append(ValidationIssue("disease_context", "must be a non-empty string or null"))
    for field, allowed in (("requested_dimensions", models.FEASIBILITY_DIMENSIONS), ("requested_modalities", models.THERAPEUTIC_MODALITIES)):
        values = getattr(profile, field)
        if not isinstance(values, tuple): issues.append(ValidationIssue(field, "must be immutable"))
        if len(values) != len(set(values)): issues.append(ValidationIssue(field, "must not contain duplicates"))
        if any(value not in allowed for value in values): issues.append(ValidationIssue(field, "contains an unknown controlled-vocabulary value"))
    if not isinstance(profile.observations, tuple) or not all(isinstance(item, models.FeasibilityObservation) for item in profile.observations): issues.append(ValidationIssue("observations", "must be an immutable sequence of observations"))
    ids = [item.observation_id for item in profile.observations]
    if len(ids) != len(set(ids)): issues.append(ValidationIssue("observations", "must not contain duplicate observation identities"))
    if ids != sorted(ids): issues.append(ValidationIssue("observations", "must be in canonical observation identity order"))
    for index, item in enumerate(profile.observations):
        for issue in validate_observation(item): issues.append(ValidationIssue(f"observations[{index}].{issue.field}", issue.message))
        for field in ("target_identifier", "target_identifier_type", "source_name", "source_release"):
            if getattr(item, field) != getattr(profile, field): issues.append(ValidationIssue(f"observations[{index}].{field}", "must match the profile"))
    if request is not None:
        if profile.request_id != request.request_id: issues.append(ValidationIssue("request_id", "must match the request"))
        for field in ("target_identifier", "target_identifier_type", "disease_context", "source_name", "source_release", "requested_dimensions", "requested_modalities"):
            if getattr(profile, field) != getattr(request, field): issues.append(ValidationIssue(field, "must match the request"))
        for index, item in enumerate(profile.observations):
            for issue in validate_observation(item, request): issues.append(ValidationIssue(f"observations[{index}].{issue.field}", issue.message))
    return issues


def require_valid_request(request: models.TargetFeasibilityRequest) -> None:
    issues = validate_request(request)
    if issues: raise ValidationError(issues)


def require_valid_observation(observation: models.FeasibilityObservation, request: models.TargetFeasibilityRequest | None = None) -> None:
    issues = validate_observation(observation, request)
    if issues: raise ValidationError(issues)


def require_valid_profile(profile: models.TargetFeasibilityProfile, request: models.TargetFeasibilityRequest | None = None) -> None:
    issues = validate_profile(profile, request)
    if issues: raise ValidationError(issues)
