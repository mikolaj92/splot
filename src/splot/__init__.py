"""Splot's generic information arbitration runtime."""

from .audit import ReportAuditFinding, audit_report, compare_replay
from .models import (
    SplotState,
    Candidate,
    CandidateEvaluation,
    ConstraintResult,
    Decision,
    DecisionReport,
    Evidence,
    Observation,
    Signal,
    Wave,
)
from .belief import build_belief
from .evidence import build_evidence
from .profile import (
    SplotProfile,
    ProfileDiagnostic,
    ProfileError,
    diagnose_profile,
    load_profile,
    validate_profile,
)
from .registry import FunctionContext, FunctionRegistry, builtin_registry
from .runtime import RoundResult, run_round
from .storage import JsonFileStateStore, MemoryStateStore, StateStore

__all__ = [
    "SplotProfile",
    "SplotState",
    "Candidate",
    "CandidateEvaluation",
    "ConstraintResult",
    "Decision",
    "DecisionReport",
    "Evidence",
    "FunctionContext",
    "FunctionRegistry",
    "JsonFileStateStore",
    "MemoryStateStore",
    "Observation",
    "ProfileDiagnostic",
    "ProfileError",
    "ReportAuditFinding",
    "RoundResult",
    "Signal",
    "StateStore",
    "Wave",
    "builtin_registry",
    "build_belief",
    "build_evidence",
    "audit_report",
    "compare_replay",
    "diagnose_profile",
    "load_profile",
    "run_round",
    "validate_profile",
]
