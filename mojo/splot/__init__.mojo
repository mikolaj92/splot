"""Splot — standalone arbitration runtime (Mojo exclusive)."""

comptime SPLOT_VERSION = "0.3.1"

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
from .profile import load_profile_toml, load_profile_text
from .toml import parse_toml_value, parse_toml_json
from .adapters_fala import arbitration_step, run_stdio_line
