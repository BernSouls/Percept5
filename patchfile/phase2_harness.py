"""Pytest plugin: exclude shadow copies without deleting them.

`Percept4-main/` and `diagnostics/_tmp/` contain duplicate packages that
shadow the live tree.  Remove them from sys.path at configure time.
"""
from __future__ import annotations

import sys

_BAD = ("Percept4-main", "diagnostics/_tmp", "diagnostics\\_tmp")


def pytest_configure(config):
    # `src/pipeline.py` is a shim that re-exports orchestration.pipeline and
    # shadows tests/figground/pipeline.py.  Pre-import the real fixture module
    # while figground is first on sys.path, then leave the import cached.
    from pathlib import Path
    fg = Path(__file__).resolve().parent / "build" / "tests" / "figground"
    if fg.is_dir():
        sys.path.insert(0, str(fg))
        try:
            import pipeline  # noqa: F401
        except Exception:
            pass
    keep = []
    for p in sys.path:
        q = (p or "").replace("\\", "/")
        if any(b.replace("\\", "/") in q for b in _BAD):
            continue
        keep.append(p)
    sys.path[:] = keep
