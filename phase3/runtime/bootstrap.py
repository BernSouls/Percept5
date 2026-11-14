"""Independent Phase-0 runtime guard. Import BEFORE any project module.

The checkout root is the sole product source. Public dependencies may come
from the active virtualenv; the sibling reference checkout is never put on
sys.path. Legacy export shims live inside this tree and only re-export local
packages (the action decoder is an explicitly unavailable import stub).
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SHIMS = ROOT / "phase3" / "runtime" / "shims"
PROJECT_PACKAGES = frozenset({
    "core", "dynamics", "input", "learning", "lenses", "matching", "memory",
    "orchestration", "parameters", "perception", "action", "phase3",
})
PROJECT_MODULES = frozenset({
    "concept_graph", "consolidator", "activation_engine", "sensory_floor",
    "derived_lenses", "pipeline", "structural_similarity", "calibration",
    "consensus", "alignment", "_text", "eth80_frontend", "_bootstrap",
    "eth80_split", "_stats", "_cache_carry", "_graphs", "_oracle",
})
_ACTIVE = False


def assert_under_tree(module: ModuleType) -> Path:
    """Mandatory measured-module provenance assertion, not a path-name guess."""
    file = getattr(module, "__file__", None)
    if file is None:
        # Several supplied product packages are PEP-420 namespaces. They have
        # no __file__ by definition; assert EVERY namespace search location is
        # local. Every actual implementation module below still requires a
        # local __file__, and explicit load() rejects a namespace as a target.
        locations = getattr(module, "__path__", None)
        if locations is not None:
            paths = [Path(p).resolve() for p in locations]
            if paths and all(p.is_relative_to(ROOT) for p in paths):
                return paths[0]
        raise RuntimeError(f"{module.__name__} has no local __file__ or local namespace path")
    path = Path(file).resolve()
    if not path.is_relative_to(ROOT):
        raise RuntimeError(f"WRONG TREE: {module.__name__} loaded from {path}; expected under {ROOT}")
    return path


def activate() -> Path:
    global _ACTIVE
    if not (ROOT / "core" / "types.py").is_file():
        raise RuntimeError(f"not the expected checkout: {ROOT}")
    for name, module in tuple(sys.modules.items()):
        if module is not None and name.split(".")[0] in PROJECT_PACKAGES | PROJECT_MODULES:
            assert_under_tree(module)
    # Preserve stdlib and site dependencies, but remove ALL other source roots.
    paths = [str(ROOT)]
    for entry in sys.path:
        p = Path(entry or os.getcwd()).resolve()
        if p == ROOT or p == SHIMS:
            continue
        if "site-packages" in p.parts or "dist-packages" in p.parts:
            paths.append(entry)
            continue
        if p.is_relative_to(ROOT) and any(
            x in p.parts for x in (".cache", ".arena", "Percept4-main", "_tmp")
        ):
            continue
        if any(x in p.parts for x in ("python3.11", "lib-dynload")) and not p.is_relative_to(ROOT):
            paths.append(entry)
        elif p.is_relative_to(ROOT):
            # Local test support (tests/matcher, diagnostics) is allowed only
            # AFTER the checkout root; it can never shadow a product package.
            paths.append(entry)
    paths.append(str(SHIMS))
    sys.path[:] = list(dict.fromkeys(paths))
    _ACTIVE = True
    return ROOT


def load(name: str) -> ModuleType:
    if not _ACTIVE:
        activate()
    module = importlib.import_module(name)
    if getattr(module, "__file__", None) is None:
        raise RuntimeError(f"measured target {name} is a namespace, not an implementation module")
    assert_under_tree(module)
    return module


def imported_product_paths() -> dict[str, str]:
    if not _ACTIVE:
        activate()
    out = {}
    for name, module in sorted(sys.modules.items()):
        if module is not None and name.split(".")[0] in PROJECT_PACKAGES | PROJECT_MODULES:
            out[name] = str(assert_under_tree(module))
    return out


def provenance(entry_script: str, modules: list[str]) -> dict:
    """Call after importing measurement dependencies, before reading data."""
    loaded = [load(name) for name in modules]
    paths = {m.__name__: str(assert_under_tree(m)) for m in loaded}
    return {
        "root": str(ROOT),
        "entry_script": str(Path(entry_script).resolve()),
        "python": sys.version,
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "modules": paths,
        "sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                   for name, path in paths.items()},
        "all_imported_product_paths": imported_product_paths(),
    }


def write_json(path: Path, value: object) -> None:
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise RuntimeError(f"refusing to write outside checkout: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
