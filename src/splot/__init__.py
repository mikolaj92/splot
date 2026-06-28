"""Splot's generic information arbitration runtime."""

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
from .profile import SplotProfile, ProfileError, load_profile, validate_profile
from .registry import FunctionContext, FunctionRegistry, builtin_registry
from .runtime import RoundResult, run_round

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
    "Observation",
    "ProfileError",
    "RoundResult",
    "Signal",
    "Wave",
    "builtin_registry",
    "load_profile",
    "run_round",
    "validate_profile",
]

