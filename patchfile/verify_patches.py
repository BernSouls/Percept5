"""[PHASE 2] THE PATCH VERIFIER.

There is no `git` binary on this machine, so the patches are verified with an
applier written here (`git apply -p1` semantics: the `a/` and `b/` prefixes
are stripped, the hunks are applied at their stated line numbers, and a
mismatch is an ERROR, not a fuzzy match).

THE CHECK IS STRONGER THAN "IT APPLIES": the series is applied to a scratch
copy of the tree and the result must be BYTE-IDENTICAL to the overlay the
series was generated from.  A patch that applied but produced a different
file would fail here.

    python phase2/verify_patches.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PATCHES = HERE / "patches"
OVERLAY = HERE / "build" / "src"
OVERLAY_TESTS = HERE / "build" / "tests"

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse(text):
    """(the file's path, the hunks) for one patch."""
    files = []
    cur = None
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            cur = {"path": None, "hunks": [], "new": False}
            files.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("new file mode"):
            cur["new"] = True
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            m = re.match(r"^\+\+\+ b/(.+?)\s*$", line)
            if m:
                cur["path"] = m.group(1)
            continue
        m = HUNK.match(line)
        if m:
            cur["hunks"].append({
                "old_start": int(m.group(1)),
                "old_len": int(m.group(2) or 1),
                "new_start": int(m.group(3)),
                "lines": [],
            })
            continue
        if cur["hunks"] and line[:1] in (" ", "-", "+", "\\"):
            cur["hunks"][-1]["lines"].append(line)
    return files


def apply_hunks(path: Path, hunks, is_new: bool) -> None:
    if is_new:
        lines = []
    else:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    cursor = 0
    for h in hunks:
        start = max(0, h["old_start"] - 1)      # a new file starts at 0
        if start < cursor:
            raise SystemExit("the hunks overlap at %s:%d" % (path, h["old_start"]))
        out.extend(lines[cursor:start])
        cursor = start
        for line in h["lines"]:
            tag = line[0]
            body = line[1:]
            if tag == " ":
                if cursor >= len(lines) or lines[cursor] != body:
                    raise SystemExit(
                        "the context does not match at %s:%d\n  expected: %r\n"
                        "  found:    %r"
                        % (path, cursor + 1, body,
                           lines[cursor] if cursor < len(lines) else "<EOF>"))
                out.append(body)
                cursor += 1
            elif tag == "-":
                if cursor >= len(lines) or lines[cursor] != body:
                    raise SystemExit(
                        "the removed line does not match at %s:%d\n  expected: %r\n"
                        "  found:    %r"
                        % (path, cursor + 1, body,
                           lines[cursor] if cursor < len(lines) else "<EOF>"))
                cursor += 1
            elif tag == "+":
                out.append(body)
            elif tag == "\\":
                continue
    out.extend(lines[cursor:])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(out), encoding="utf-8")


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="phase2_verify_"))
    print("the scratch tree: %s" % scratch)
    try:
        # the series is a diff AGAINST the original tree: copy it first
        shutil.copytree(ROOT / "src", scratch / "src",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT / "tests", scratch / "tests",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in sorted(p.name for p in PATCHES.glob("*.patch")):
            text = (PATCHES / name).read_text(encoding="utf-8")
            body = "".join(l for l in text.splitlines(keepends=True)
                           if not l.startswith("#"))
            files = parse(body)
            touched = []
            for f in files:
                if not f["path"]:
                    raise SystemExit("%s: a file has no path" % name)
                target = scratch / f["path"]
                apply_hunks(target, f["hunks"], f["new"])
                touched.append(f["path"])
            print("  %-52s applies: %s" % (name, ", ".join(touched)))
        # the result must be byte-identical to the overlay
        bad = []
        for rel, overlay in (("src", OVERLAY), ("tests", OVERLAY_TESTS)):
            base = scratch / rel
            if not base.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for f in filenames:
                    p = Path(dirpath) / f
                    q = overlay / p.relative_to(base)
                    if not q.exists():
                        bad.append("missing in the overlay: %s" % p)
                    elif p.read_bytes() != q.read_bytes():
                        bad.append("differs from the overlay: %s" % p)
        if bad:
            print("THE VERIFICATION FAILED:")
            for b in bad:
                print("   %s" % b)
            return 1
        print("THE VERIFICATION PASSED: the series applies cleanly and the"
              " result is byte-identical to the overlay.")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
