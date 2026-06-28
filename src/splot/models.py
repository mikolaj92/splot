from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any
from uuid import uuid4

from .versioning import STATE_SCHEMA_VERSION


JsonDict = dict[str, Any]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


@dataclass
class JsonModel:
    def to_dict(self) -> JsonDict:
        return jsonable(self)


@dataclass
class Wave(JsonModel):
    id: str
    kind: str = "generic"
    domain: str | None = None
    reliability: float = 1.0
    latency_ms: int | None = None
    cost: float | None = None
    known_biases: list[str] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Wave":
        return cls(**data)


@dataclass
class Projection(JsonModel):
    wave_id: str
    observes: list[str] = field(default_factory=list)
    loses: list[str] = field(default_factory=list)
    biases: list[str] = field(default_factory=list)
    confidence_hint: float | None = None
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class Observation(JsonModel):
    id: str
    wave_id: str | None = None
    kind: str = "generic"
    observed_at: str | None = None
    window_start: str | None = None
    window_end: str | None = None
    values: JsonDict = field(default_factory=dict)
    confidence: float = 1.0
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Observation":
        return cls(**data)


@dataclass
class Evidence(JsonModel):
    id: str
    observation_id: str | None = None
    candidate_id: str | None = None
    supports: list[str] = field(default_factory=list)
    opposes: list[str] = field(default_factory=list)
    strength: float = 0.0
    confidence: float = 1.0
    reasons: list[str] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Evidence":
        return cls(**data)


@dataclass
class Belief(JsonModel):
    id: str
    objective_id: str
    candidate_beliefs: JsonDict = field(default_factory=dict)
    uncertainty: float = 1.0
    conflicts: list[JsonDict] = field(default_factory=list)
    stale_sources: list[str] = field(default_factory=list)
    source_reliability: dict[str, float] = field(default_factory=dict)
    previous_decision: JsonDict | None = None
    history: list[JsonDict] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class Candidate(JsonModel):
    id: str
    kind: str = "generic"
    source_ids: list[str] = field(default_factory=list)
    payload: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)
    proposed_action: str | None = None
    expected_gain: float | None = None
    switching_cost: float = 0.0
    risk: float | None = None
    dependencies: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Candidate":
        return cls(**data)


@dataclass
class Signal(JsonModel):
    id: str
    value: Any
    normalized: float
    weight: float
    prefer: str = "higher"
    confidence: float = 1.0
    reason: str | None = None
    contribution: float = 0.0


@dataclass
class ConstraintResult(JsonModel):
    id: str
    severity: str
    passed: bool
    reason: str
    penalty: float = 0.0


@dataclass
class VerifierResult(JsonModel):
    id: str
    passed: bool
    reason: str


@dataclass
class CandidateEvaluation(JsonModel):
    candidate_id: str
    eligible: bool
    score: float
    raw_score: float
    signals: list[Signal] = field(default_factory=list)
    constraints: list[ConstraintResult] = field(default_factory=list)
    verifiers: list[VerifierResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected_reasons: list[str] = field(default_factory=list)
    human_decisions: list[str] = field(default_factory=list)


@dataclass
class Decision(JsonModel):
    id: str
    status: str
    objective_id: str
    selected_candidate_id: str | None = None
    selected_candidate_ids: list[str] = field(default_factory=list)
    previous_decision_id: str | None = None
    action: JsonDict | None = None
    confidence: float = 0.0
    uncertainty: float = 1.0
    policy_reason: str = ""
    explanation: str = ""
    evaluations: list[JsonDict] = field(default_factory=list)
    rejected_candidates: list[JsonDict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_human_inputs: list[str] = field(default_factory=list)
    created_at: str | None = None
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class Feedback(JsonModel):
    decision_id: str
    outcome: str | None = None
    accepted: bool | None = None
    external_result: JsonDict = field(default_factory=dict)
    state_updates: JsonDict = field(default_factory=dict)
    reliability_updates: dict[str, float] = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class SplotState(JsonModel):
    state_schema_version: int = STATE_SCHEMA_VERSION
    session_id: str = field(default_factory=lambda: new_id("session"))
    objective_id: str | None = None
    previous_decision: JsonDict | None = None
    last_decision_at: str | None = None
    last_switch_at: str | None = None
    candidate_history: list[JsonDict] = field(default_factory=list)
    evidence_history: list[JsonDict] = field(default_factory=list)
    source_reliability: dict[str, float] = field(default_factory=dict)
    unresolved_conflicts: list[JsonDict] = field(default_factory=list)
    open_human_decisions: list[str] = field(default_factory=list)
    stability_memory: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonDict | None) -> "SplotState":
        if not data:
            return cls()
        return cls(
            state_schema_version=int(data.get("state_schema_version", STATE_SCHEMA_VERSION)),
            session_id=data.get("session_id") or new_id("session"),
            objective_id=data.get("objective_id"),
            previous_decision=data.get("previous_decision"),
            last_decision_at=data.get("last_decision_at"),
            last_switch_at=data.get("last_switch_at"),
            candidate_history=list(data.get("candidate_history") or []),
            evidence_history=list(data.get("evidence_history") or []),
            source_reliability=dict(data.get("source_reliability") or {}),
            unresolved_conflicts=list(data.get("unresolved_conflicts") or []),
            open_human_decisions=list(data.get("open_human_decisions") or []),
            stability_memory=dict(data.get("stability_memory") or {}),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class DecisionReport(JsonModel):
    splot_version: str
    profile_version: int
    profile_digest: str
    profile_schema_version: int
    report_schema_version: int
    input_digest: str
    round_id: str
    profile_id: str
    mode: str
    objective_id: str
    created_at: str
    previous_decision: JsonDict | None
    observations: list[JsonDict]
    candidates: list[JsonDict]
    evidence: list[JsonDict]
    belief: JsonDict
    evaluations: list[JsonDict]
    stability: JsonDict
    decision: JsonDict
    uncertainty: JsonDict
    policy_reasons: list[str]
    previous_state: JsonDict
    updated_state: JsonDict
    warnings: list[str] = field(default_factory=list)
    human_decisions: list[str] = field(default_factory=list)
    state_updates: JsonDict = field(default_factory=dict)
