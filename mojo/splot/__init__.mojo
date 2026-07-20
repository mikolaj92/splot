"""Splot — standalone arbitration runtime (Mojo exclusive)."""

from .models import (
    Candidate,
    Observation,
    Signal,
    ConstraintResult,
    CandidateEvaluation,
    Decision,
    SplotState,
    RoundResult,
)
from .pipeline import run_round, evaluate_all, decide_from_evaluations
from .json_util import parse_json
from .adapters_fala import arbitration_step, run_stdio_line
