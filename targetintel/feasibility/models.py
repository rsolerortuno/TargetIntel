"""Pure immutable contracts for source-linked target feasibility.

The values here are descriptive observations only.  This module intentionally
does not import or invoke TargetIntel's scoring, ranking, role, LLM, evidence,
or modality-evaluation layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Any, Mapping


REQUEST_SCHEMA_ID = "targetintel.target-feasibility-request"
REQUEST_SCHEMA_VERSION = "v0.4.0"
OBSERVATION_FORMAT_VERSION = "v0.4.0"
PROFILE_FORMAT_VERSION = "v0.4.0"

TARGET_IDENTIFIER_TYPES = frozenset({"ensembl_gene_id", "gene_symbol"})
FEASIBILITY_DIMENSIONS = frozenset({"clinical_precedence", "tractability", "doability", "safety"})
THERAPEUTIC_MODALITIES = frozenset({"antibody", "small_molecule", "protac", "other_clinical"})
AVAILABILITY_STATES = frozenset({
    "observed", "not_observed", "not_available", "not_applicable", "conflicting", "retrieval_failed",
})
NORMALIZED_VALUE_TYPES = frozenset({"string", "boolean", "number", "null", "object", "array"})


def _freeze(value: Any) -> Any:
    """Recursively make JSON-compatible nested values immutable."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, datetime):
        return _isoformat(value)
    return value


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Return deterministic JSON without operational environment details."""
    return json.dumps(_thaw(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _identity(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{sha256(canonical_json(payload).encode('utf-8')).hexdigest()}"


def _optional_timestamp(value: datetime | None) -> str | None:
    return None if value is None else _isoformat(value)


def _strict_from_dict(cls: type, data: Mapping[str, Any], fields: set[str]):
    unknown = set(data) - fields
    missing = fields - set(data)
    if unknown or missing:
        pieces = []
        if unknown:
            pieces.append("unknown fields: " + ", ".join(sorted(unknown)))
        if missing:
            pieces.append("missing fields: " + ", ".join(sorted(missing)))
        raise ValueError("; ".join(pieces))
    return cls(**dict(data))


@dataclass(frozen=True)
class TargetFeasibilityRequest:
    request_schema_id: str
    request_schema_version: str
    target_identifier: str
    target_identifier_type: str
    disease_context: str | None
    requested_dimensions: tuple[str, ...] | list[str]
    requested_modalities: tuple[str, ...] | list[str]
    source_name: str
    source_release: str
    requesting_actor_id: str
    operational_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_dimensions", tuple(sorted(self.requested_dimensions)))
        object.__setattr__(self, "requested_modalities", tuple(sorted(self.requested_modalities)))

    @property
    def request_id(self) -> str:
        return _identity("tfr", self.identity_payload())

    def identity_payload(self) -> dict[str, Any]:
        return {
            "request_schema_id": self.request_schema_id,
            "request_schema_version": self.request_schema_version,
            "target_identifier": self.target_identifier,
            "target_identifier_type": self.target_identifier_type,
            "disease_context": self.disease_context,
            "requested_dimensions": list(self.requested_dimensions),
            "requested_modalities": list(self.requested_modalities),
            "source_name": self.source_name,
            "source_release": self.source_release,
            "requesting_actor_id": self.requesting_actor_id,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self.identity_payload()
        result["request_id"] = self.request_id
        result["operational_timestamp"] = _optional_timestamp(self.operational_timestamp)
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TargetFeasibilityRequest":
        values = dict(data)
        supplied_id = values.pop("request_id", None)
        timestamp = values.get("operational_timestamp")
        if isinstance(timestamp, str):
            values["operational_timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        request = _strict_from_dict(cls, values, set(cls.__dataclass_fields__))
        if supplied_id is not None and supplied_id != request.request_id:
            raise ValueError("request_id does not match deterministic request content")
        from .validation import require_valid_request
        require_valid_request(request)
        return request


@dataclass(frozen=True)
class FeasibilityObservation:
    observation_format_version: str
    target_identifier: str
    target_identifier_type: str
    dimension: str
    modality: str | None
    factor_identifier: str
    normalized_value: Any
    normalized_value_type: str
    availability_state: str
    source_name: str
    source_release: str
    source_record_identifier: str | None
    source_field_or_path: str
    provenance: Mapping[str, Any]
    limitations: tuple[str, ...] | list[str]
    operational_retrieval_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "normalized_value", _freeze(self.normalized_value))
        object.__setattr__(self, "provenance", _freeze(self.provenance))
        object.__setattr__(self, "limitations", tuple(_freeze(item) for item in self.limitations))

    @property
    def observation_id(self) -> str:
        return _identity("tfo", self.identity_payload())

    def identity_payload(self) -> dict[str, Any]:
        return {
            "observation_format_version": self.observation_format_version,
            "target_identifier": self.target_identifier,
            "target_identifier_type": self.target_identifier_type,
            "dimension": self.dimension,
            "modality": self.modality,
            "factor_identifier": self.factor_identifier,
            "normalized_value": _thaw(self.normalized_value),
            "normalized_value_type": self.normalized_value_type,
            "availability_state": self.availability_state,
            "source_name": self.source_name,
            "source_release": self.source_release,
            "source_record_identifier": self.source_record_identifier,
            "source_field_or_path": self.source_field_or_path,
            "provenance": _thaw(self.provenance),
            "limitations": _thaw(self.limitations),
        }

    def to_dict(self) -> dict[str, Any]:
        result = self.identity_payload()
        result["observation_id"] = self.observation_id
        result["operational_retrieval_timestamp"] = _optional_timestamp(self.operational_retrieval_timestamp)
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FeasibilityObservation":
        values = dict(data)
        supplied_id = values.pop("observation_id", None)
        timestamp = values.get("operational_retrieval_timestamp")
        if isinstance(timestamp, str):
            values["operational_retrieval_timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        observation = _strict_from_dict(cls, values, set(cls.__dataclass_fields__))
        if supplied_id is not None and supplied_id != observation.observation_id:
            raise ValueError("observation_id does not match deterministic observation content")
        from .validation import require_valid_observation
        require_valid_observation(observation)
        return observation


def _availability_summary(observations: tuple[FeasibilityObservation, ...]) -> Mapping[str, int]:
    return MappingProxyType({state: sum(item.availability_state == state for item in observations) for state in sorted(AVAILABILITY_STATES)})


def _contradictions(observations: tuple[FeasibilityObservation, ...]) -> Mapping[str, Any]:
    groups: dict[tuple[Any, ...], list[FeasibilityObservation]] = {}
    for item in observations:
        key = (item.target_identifier, item.target_identifier_type, item.dimension, item.modality, item.factor_identifier, item.normalized_value_type)
        groups.setdefault(key, []).append(item)
    conflicting_ids = []
    for group in groups.values():
        values = {canonical_json(item.normalized_value) for item in group}
        if len(values) > 1 or any(item.availability_state == "conflicting" for item in group):
            conflicting_ids.extend(item.observation_id for item in group)
    return MappingProxyType({"has_contradictions": bool(conflicting_ids), "observation_ids": tuple(sorted(conflicting_ids))})


@dataclass(frozen=True)
class TargetFeasibilityProfile:
    profile_format_version: str
    request_id: str
    target_identifier: str
    target_identifier_type: str
    disease_context: str | None
    source_name: str
    source_release: str
    requested_dimensions: tuple[str, ...] | list[str]
    requested_modalities: tuple[str, ...] | list[str]
    observations: tuple[FeasibilityObservation, ...] | list[FeasibilityObservation]

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_dimensions", tuple(sorted(self.requested_dimensions)))
        object.__setattr__(self, "requested_modalities", tuple(sorted(self.requested_modalities)))
        object.__setattr__(self, "observations", tuple(sorted(self.observations, key=lambda item: item.observation_id)))

    @classmethod
    def from_request(
        cls, request: TargetFeasibilityRequest, observations: tuple[FeasibilityObservation, ...] | list[FeasibilityObservation]
    ) -> "TargetFeasibilityProfile":
        return cls(PROFILE_FORMAT_VERSION, request.request_id, request.target_identifier, request.target_identifier_type,
                   request.disease_context, request.source_name, request.source_release,
                   request.requested_dimensions, request.requested_modalities, observations)

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def availability_summary(self) -> Mapping[str, int]:
        return _availability_summary(self.observations)

    @property
    def contradiction_indicators(self) -> Mapping[str, Any]:
        return _contradictions(self.observations)

    @property
    def research_only(self) -> bool:
        return True

    @property
    def no_score_calculated(self) -> bool:
        return True

    @property
    def no_ranking_modified(self) -> bool:
        return True

    @property
    def no_role_modified(self) -> bool:
        return True

    @property
    def no_clinical_conclusion_generated(self) -> bool:
        return True

    @property
    def profile_id(self) -> str:
        return _identity("tfp", self.identity_payload())

    def identity_payload(self) -> dict[str, Any]:
        return {
            "profile_format_version": self.profile_format_version, "request_id": self.request_id,
            "target_identifier": self.target_identifier, "target_identifier_type": self.target_identifier_type,
            "disease_context": self.disease_context, "source_name": self.source_name,
            "source_release": self.source_release, "requested_dimensions": list(self.requested_dimensions),
            "requested_modalities": list(self.requested_modalities),
            "observation_ids": [item.observation_id for item in self.observations],
            "availability_summary": dict(self.availability_summary),
            "contradiction_indicators": _thaw(self.contradiction_indicators), "research_only": True,
            "no_score_calculated": True, "no_ranking_modified": True, "no_role_modified": True,
            "no_clinical_conclusion_generated": True,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self.identity_payload()
        result["profile_id"] = self.profile_id
        result["observations"] = [item.to_dict() for item in self.observations]
        result["observation_count"] = self.observation_count
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TargetFeasibilityProfile":
        values = dict(data)
        supplied_id = values.pop("profile_id", None)
        supplied_count = values.pop("observation_count", None)
        supplied_observation_ids = values.pop("observation_ids", None)
        supplied_summary = values.pop("availability_summary", None)
        supplied_contradictions = values.pop("contradiction_indicators", None)
        boundaries = {
            key: values.pop(key, None)
            for key in ("research_only", "no_score_calculated", "no_ranking_modified", "no_role_modified", "no_clinical_conclusion_generated")
        }
        observations = values.get("observations")
        if isinstance(observations, (list, tuple)):
            values["observations"] = [
                item if isinstance(item, FeasibilityObservation) else FeasibilityObservation.from_dict(item)
                for item in observations
            ]
        profile = _strict_from_dict(cls, values, set(cls.__dataclass_fields__))
        if supplied_id is not None and supplied_id != profile.profile_id:
            raise ValueError("profile_id does not match deterministic profile content")
        if supplied_count is not None and supplied_count != profile.observation_count:
            raise ValueError("observation_count does not match observations")
        if supplied_observation_ids is not None and supplied_observation_ids != [item.observation_id for item in profile.observations]:
            raise ValueError("observation_ids do not match observations")
        if supplied_summary is not None and supplied_summary != dict(profile.availability_summary):
            raise ValueError("availability_summary does not match observations")
        if supplied_contradictions is not None and supplied_contradictions != _thaw(profile.contradiction_indicators):
            raise ValueError("contradiction_indicators do not match observations")
        if any(value is not None and value is not True for value in boundaries.values()):
            raise ValueError("profile boundary statements must remain true")
        from .validation import require_valid_profile
        require_valid_profile(profile)
        return profile
