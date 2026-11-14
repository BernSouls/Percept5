"""Pytest plugin asserting product-module __file__ before every test.

Load explicitly with -p phase3.runtime.pytest_guard. Unlike the inherited
phase2 plugin this never inserts a sibling checkout or an overlay source.
"""
from __future__ import annotations
import sys
from pathlib import Path
from phase3.runtime.bootstrap import ROOT, SHIMS, activate, imported_product_paths, write_json


def pytest_configure(config):
    activate()
    # The export's fixtures use absolute _graphs/_oracle imports.
    sys.path.insert(1, str(ROOT / "tests" / "matcher"))
    # Restored export tests were authored in tests_matcher/, not tests/matcher/.
    # Their relative diagnostics lookup points at tests/diagnostics. Supply the
    # actual LOCAL support directory without editing any recovered test body.
    sys.path.insert(2, str(ROOT / "diagnostics"))
    import parameters
    import core.types
    import core.schema
    import memory.cores
    import matching.relation_frame
    imported_product_paths()


def pytest_collection_modifyitems(config, items):
    # Reassert after conftest collection (which can manipulate sys.path).
    paths = imported_product_paths()
    if not any(p == str(ROOT / "memory" / "cores.py") for p in paths.values()):
        raise RuntimeError("matcher implementation was not loaded from this tree")


def pytest_runtest_setup(item):
    activate()
    imported_product_paths()


def pytest_sessionfinish(session, exitstatus):
    write_json(ROOT / "phase3" / "audit" / "pytest-loaded-paths.json", {
        "exitstatus": int(exitstatus), "modules": imported_product_paths(),
        "shims": str(SHIMS), "root": str(ROOT),
    })
