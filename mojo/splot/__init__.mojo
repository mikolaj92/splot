"""Splot — generic fusion organ (Mojo exclusive).

Many high-entropy streams (candidate payloads) in → one lower-entropy
commitment out. Domain- and evaluator-agnostic: the host supplies signal
values; Splot only fuses under a TOML profile.
"""

comptime SPLOT_VERSION = "0.3.2"

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
from .pipeline import (
    run_round,
    evaluate_all,
    decide_from_evaluations,
    decide_select_one,
    decide_compose_one,
    evaluations_to_json,
    build_envelope_json,
)
from .registry import ReaderRegistry
from .json_util import parse_json
from .profile import load_profile_toml, load_profile_text
from .toml import parse_toml_value, parse_toml_json
from .adapters_fala import fusion_step, arbitration_step, run_stdio_line
