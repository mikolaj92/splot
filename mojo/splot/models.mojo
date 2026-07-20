"""Core Splot records (JSON-friendly)."""

from std.collections import List, Dict
from splot.json_util import quote


struct Candidate(Copyable, Movable):
    var id: String
    var payload_json: String  # object
    var metadata_json: String
    var source_ids_json: String  # array
    var switching_cost: Float64

    def __init__(
        out self,
        id: String,
        payload_json: String = "{}",
        metadata_json: String = "{}",
        source_ids_json: String = "[]",
        switching_cost: Float64 = 0.0,
    ):
        self.id = id
        self.payload_json = payload_json
        self.metadata_json = metadata_json
        self.source_ids_json = source_ids_json
        self.switching_cost = switching_cost

    def __init__(out self, *, copy: Self):
        self.id = copy.id
        self.payload_json = copy.payload_json
        self.metadata_json = copy.metadata_json
        self.source_ids_json = copy.source_ids_json
        self.switching_cost = copy.switching_cost


struct Observation(Copyable, Movable):
    var id: String
    var wave_id: String
    var values_json: String
    var confidence: Float64

    def __init__(
        out self,
        id: String,
        wave_id: String = "",
        values_json: String = "{}",
        confidence: Float64 = 1.0,
    ):
        self.id = id
        self.wave_id = wave_id
        self.values_json = values_json
        self.confidence = confidence

    def __init__(out self, *, copy: Self):
        self.id = copy.id
        self.wave_id = copy.wave_id
        self.values_json = copy.values_json
        self.confidence = copy.confidence


struct Signal(Copyable, Movable):
    var id: String
    var value_json: String
    var normalized: Float64
    var weight: Float64
    var prefer: String
    var confidence: Float64
    var contribution: Float64

    def __init__(
        out self,
        id: String,
        value_json: String,
        normalized: Float64,
        weight: Float64,
        prefer: String = "higher",
        confidence: Float64 = 1.0,
    ):
        self.id = id
        self.value_json = value_json
        self.normalized = normalized
        self.weight = weight
        self.prefer = prefer
        self.confidence = confidence
        self.contribution = normalized * weight

    def __init__(out self, *, copy: Self):
        self.id = copy.id
        self.value_json = copy.value_json
        self.normalized = copy.normalized
        self.weight = copy.weight
        self.prefer = copy.prefer
        self.confidence = copy.confidence
        self.contribution = copy.contribution


struct ConstraintResult(Copyable, Movable):
    var id: String
    var severity: String
    var passed: Bool
    var reason: String
    var penalty: Float64

    def __init__(
        out self,
        id: String,
        severity: String,
        passed: Bool,
        reason: String,
        penalty: Float64 = 0.0,
    ):
        self.id = id
        self.severity = severity
        self.passed = passed
        self.reason = reason
        self.penalty = penalty

    def __init__(out self, *, copy: Self):
        self.id = copy.id
        self.severity = copy.severity
        self.passed = copy.passed
        self.reason = copy.reason
        self.penalty = copy.penalty


struct CandidateEvaluation(Copyable, Movable):
    var candidate_id: String
    var eligible: Bool
    var score: Float64
    var raw_score: Float64
    var signals: List[Signal]
    var constraints: List[ConstraintResult]
    var warnings: List[String]
    var rejected_reasons: List[String]
    var human_decisions: List[String]

    def __init__(out self, candidate_id: String):
        self.candidate_id = candidate_id
        self.eligible = True
        self.score = 0.0
        self.raw_score = 0.0
        self.signals = List[Signal]()
        self.constraints = List[ConstraintResult]()
        self.warnings = List[String]()
        self.rejected_reasons = List[String]()
        self.human_decisions = List[String]()

    def __init__(out self, *, copy: Self):
        self.candidate_id = copy.candidate_id
        self.eligible = copy.eligible
        self.score = copy.score
        self.raw_score = copy.raw_score
        self.signals = copy.signals.copy()
        self.constraints = copy.constraints.copy()
        self.warnings = copy.warnings.copy()
        self.rejected_reasons = copy.rejected_reasons.copy()
        self.human_decisions = copy.human_decisions.copy()


struct Decision(Copyable, Movable):
    var id: String
    var status: String
    var objective_id: String
    var selected_candidate_id: String
    var confidence: Float64
    var uncertainty: Float64
    var policy_reason: String
    var explanation: String
    var warnings_json: String

    def __init__(
        out self,
        id: String,
        status: String,
        objective_id: String,
        selected_candidate_id: String = "",
        confidence: Float64 = 0.0,
        uncertainty: Float64 = 1.0,
        policy_reason: String = "",
        explanation: String = "",
        warnings_json: String = "[]",
    ):
        self.id = id
        self.status = status
        self.objective_id = objective_id
        self.selected_candidate_id = selected_candidate_id
        self.confidence = confidence
        self.uncertainty = uncertainty
        self.policy_reason = policy_reason
        self.explanation = explanation
        self.warnings_json = warnings_json

    def __init__(out self, *, copy: Self):
        self.id = copy.id
        self.status = copy.status
        self.objective_id = copy.objective_id
        self.selected_candidate_id = copy.selected_candidate_id
        self.confidence = copy.confidence
        self.uncertainty = copy.uncertainty
        self.policy_reason = copy.policy_reason
        self.explanation = copy.explanation
        self.warnings_json = copy.warnings_json

    def to_json(self) -> String:
        var sel = "null"
        if self.selected_candidate_id != "":
            sel = quote(self.selected_candidate_id)
        return (
            "{\"id\":"
            + quote(self.id)
            + ",\"status\":"
            + quote(self.status)
            + ",\"objective_id\":"
            + quote(self.objective_id)
            + ",\"selected_candidate_id\":"
            + sel
            + ",\"confidence\":"
            + String(self.confidence)
            + ",\"uncertainty\":"
            + String(self.uncertainty)
            + ",\"policy_reason\":"
            + quote(self.policy_reason)
            + ",\"explanation\":"
            + quote(self.explanation)
            + ",\"warnings\":"
            + self.warnings_json
            + "}"
        )


struct SplotState(Copyable, Movable):
    var previous_decision_json: String
    var last_decision_at: String
    var last_switch_at: String
    var stability_memory_json: String

    def __init__(
        out self,
        previous_decision_json: String = "{}",
        last_decision_at: String = "",
        last_switch_at: String = "",
        stability_memory_json: String = "{}",
    ):
        self.previous_decision_json = previous_decision_json
        self.last_decision_at = last_decision_at
        self.last_switch_at = last_switch_at
        self.stability_memory_json = stability_memory_json

    def __init__(out self, *, copy: Self):
        self.previous_decision_json = copy.previous_decision_json
        self.last_decision_at = copy.last_decision_at
        self.last_switch_at = copy.last_switch_at
        self.stability_memory_json = copy.stability_memory_json

    def to_json(self) -> String:
        return (
            "{\"previous_decision\":"
            + self.previous_decision_json
            + ",\"last_decision_at\":"
            + quote(self.last_decision_at)
            + ",\"last_switch_at\":"
            + quote(self.last_switch_at)
            + ",\"stability_memory\":"
            + self.stability_memory_json
            + "}"
        )


struct RoundResult(Copyable, Movable):
    var decision: Decision
    var state: SplotState
    var report_json: String

    def __init__(out self, decision: Decision, state: SplotState, report_json: String):
        self.decision = decision.copy()
        self.state = state.copy()
        self.report_json = report_json

    def __init__(out self, *, copy: Self):
        self.decision = copy.decision.copy()
        self.state = copy.state.copy()
        self.report_json = copy.report_json
