"""Splot: a cybernetic information arbitration runtime.

Many partial, noisy, possibly conflicting signals in; one decision signal with
minimized entropy out, plus a trace of the remaining uncertainty and why the
decision won. The theoretical basis is Marian Mazur's cybernetics; see
docs/CONCEPTUAL_MODEL.md.
"""

from .audit import ReportAuditFinding, audit_report, compare_replay, compare_reports
from .errors import (
    SplotCompositionError,
    SplotError,
    SplotPolicyError,
    SplotProfileError,
    SplotProviderError,
    SplotRegistryError,
    SplotReportError,
    SplotStabilityError,
    SplotValidationError,
)
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
from .schemas import (
    SchemaValidationError,
    validate_decision_report_data,
    validate_profile_data,
    validate_state_data,
)
from .storage import JsonFileStateStore, MemoryStateStore, StateStore
from .versioning import SPLOT_VERSION

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
    "SPLOT_VERSION",
    "SchemaValidationError",
    "Signal",
    "SplotCompositionError",
    "SplotError",
    "SplotPolicyError",
    "SplotProfileError",
    "SplotProviderError",
    "SplotRegistryError",
    "SplotReportError",
    "SplotStabilityError",
    "SplotValidationError",
    "StateStore",
    "Wave",
    "builtin_registry",
    "build_belief",
    "build_evidence",
    "audit_report",
    "compare_replay",
    "compare_reports",
    "diagnose_profile",
    "load_profile",
    "run_round",
    "validate_decision_report_data",
    "validate_profile",
    "validate_profile_data",
    "validate_state_data",
]
