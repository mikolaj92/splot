"""Splot — generic fusion organ (Mojo engine + thin Python binding).

Mojo is the product truth (``mojo/splot``). This package is an optional in-process
host surface: ``fuse`` / ``fuse_json``. Subprocess step ``tools/splot_step.sh``
remains the official Fala / CI contract.

Requires a Mojo toolchain at import/call time (see README).
"""

from __future__ import annotations

from splot.api import fuse, fuse_json, load_profile

__all__ = ["fuse", "fuse_json", "load_profile", "__version__"]
__version__ = "0.4.1"
