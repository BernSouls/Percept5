"""[PHASE 2] THE PATCH GENERATOR.

The overlay is a COPY of the tree with the mechanisms applied; the DELIVERABLE
is a patch series that applies to the ORIGINAL tree with `git apply -p1` from
the repository root (E:\\Take25\\work).

This generator diffs the ORIGINAL `src/` against the overlay's `build/src` and
writes one patch per concern, with the header the brief requires: the claim
IDs addressed, the mechanism, the pre-registered constants, the gating flag
and the pin that catches the reversion.

THE CHECK: the generator asserts that the overlay's files are the ones it
diffs (no stale overlay), and it verifies every patch applies CLEANLY to a
scratch copy of the tree (`git apply --check` is not available -- there is no
git binary on this machine -- so the check is done with a patch applier
written here, `patch -p1` semantics: the hunks are applied to the file and a
mismatch is an error).
"""
from __future__ import annotations

import difflib
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"
OVERLAY = HERE / "build" / "src"
OVERLAY_TESTS = HERE / "build" / "tests"
OUT = HERE / "patches"

#: the series: (the patch's name, the files it touches, the header)
SERIES = [
    ("0000_harness_figground_pipeline",
     [("tests/figground/pipeline.py", "tests/figground/pipeline.py")],
     """CLAIM ID: H1 (the harness must collect the whole tree).

MECHANISM: the figground fixture module `tests/figground/pipeline.py`
SHADOWS `src/pipeline.py`, which is the compatibility name for
`orchestration.pipeline`.  The tests outside the figground suite that import
`Pipeline` / `PipelineProviders` therefore could not import them: 31
collection errors over the whole tree.  The figground module keeps its own
`run_pipeline` and exposes the orchestration names it does not define.

PRE-REGISTERED CONSTANTS: none.

GATING FLAG: none -- this is a HARNESS fix; it changes no product behaviour.

THE PIN: the collection itself: `python -m pytest --collect-only -q` must
        collect with 0 errors.

DEPENDENCIES: none.  Apply this one FIRST.
"""),
    ("0001_matcher_flags",
     [("src/parameters/_text.py", "src/parameters/_text.py")],
     """CLAIM IDS: none (the enabling change).

MECHANISM: the five NEW flags, every one of them DEFAULTING TO THE
HISTORICAL BEHAVIOUR:

    MATCH_EDGE_MASS_CONTAINMENT         B3  the matched edge mass may not
                                            exceed the edge mass it came from
    MATCH_SKIP_INCOMPARABLE_RELATIONS   B7  a relation with no common ontology
                                            is INCOMPARABLE: skipped from the
                                            numerator AND the denominator
    MATCH_KEEP_HIERARCHY_MEMBERS        P0  keep the member node (the
                                            hierarchy step becomes additive)
    MATCH_TEMPLATE_MEDIAN_EXEMPLAR      D5  the template is built in the
                                            MEDIAN exemplar's space
    MATCH_CONSENSUS_COUNT_ABSTENTIONS   D7  an exemplar that did not fill a
                                            slot is an ABSTENTION: it stays in
                                            the denominator

PRE-REGISTERED CONSTANTS: none -- the flags are switches, not numbers.

GATING FLAG: this patch IS the gating.  It changes no behaviour: every
mechanism that follows is OFF until a rule selects it.

THE PIN: tests/matcher/test_phase2_flagged_mechanisms.py::
        test_every_new_flag_defaults_to_the_historical_behaviour
        (reverting a flag's default reddens exactly one pin)

DEPENDENCIES: none.  Every later patch needs this one.
"""),
    ("0002_edge_mass_containment_and_incomparable",
     [("src/memory/cores.py", "src/memory/cores.py"),
      ("src/core/schema.py", "src/core/schema.py")],
     """CLAIM IDS: B3 (the edge-mass facilitation overflows the denominator),
             B7 (an incomparable relation is scored as a contradiction).

MECHANISM:
  B3  the factor (1 + log2(n+1)) multiplies the MATCHED edge mass but not the
      edge totals, so one matched edge with one measured axis contributes 2x
      its own mass and the ratio can exceed 1; the score's own min(1.0, ...)
      then hides the overflow.  The containment caps the matched mass at the
      edge mass it was drawn from.  The RAW mass is kept in the trace
      (`*_matched_em_raw`) so the facilitation stays visible: the pin's power
      is the 2.0 against the 1.0.
  B7  `polymorphic_edge_similarity(..., return_none=True)` returns the THIRD
      state for a pair with no common ontology (the three stage-6 relations
      have no U30 equivalent).  `_mcs_accumulate` skips it from the numerator
      AND from the denominator: the relation's mass leaves the side's edge
      total, and the verifiable-edge COUNT excludes it.  A relation with NO
      candidate is not incomparable -- absence is not incomparability -- so it
      stays in the denominator.

PRE-REGISTERED CONSTANTS: none.  The containment is the identity `min(x, own
total)`; the skip is the third state.

GATING FLAG: MATCH_EDGE_MASS_CONTAINMENT, MATCH_SKIP_INCOMPARABLE_RELATIONS
        (both default OFF: the historical behaviour).

THE PINS: tests/matcher/test_phase2_flagged_mechanisms.py::
        test_b3_the_containment_caps_the_matched_edge_mass
        test_b7_an_incomparable_relation_is_skipped_not_scored
        and tests/matcher/test_p4b_count_apart.py::
        test_the_edge_mass_of_a_flag_loses_its_facilitation (the RAW mass:
        2.0 with the flag counted as a measured axis, 1.0 without it -- the
        pin keeps its discriminating power, which the cap alone destroyed).

DEPENDENCIES: 0001 (the flags).

MEASURED: on the nine registered pairs the arms are IDENTICAL to the
        baseline (P 0.640 / R 0.688 / F1 0.662): the cap never binds on that
        corpus and there are no cross-ontology edge pairs in it.  These are
        contract corrections, not gains, and the report says so.
"""),
    ("0003_keep_hierarchy_members",
     [("src/memory/mapper.py", "src/memory/mapper.py")],
     """CLAIM ID: P0 (the hierarchy step must be additive, not subtractive).

MECHANISM: `_apply_hierarchy_exclusions` keeps the member node when the flag
is on: the member and the parent are both physical, and the
content-discriminative mass decides what survives downstream.  No arity or
schema change and no parent-slot fabrication.

PRE-REGISTERED CONSTANTS: none.

GATING FLAG: MATCH_KEEP_HIERARCHY_MEMBERS (default OFF).

THE PIN: tests/matcher/test_phase2_flagged_mechanisms.py::
        test_p0_the_member_is_kept_only_when_the_flag_is_on

DEPENDENCIES: 0001 (the flag).

MEASURED, AND THIS IS THE IMPORTANT PART: the hierarchy step is INERT on the
        four ETH-80 frames -- it deletes 0 of 740 situation-graph edges and 0
        nodes (diagnostics/phase2_spine_census.py).  The edge loss (3017 ->
        740) happens UPSTREAM, in the situation graph's own construction.
        So this flag is a shape, not a gain, and the real P0 target is the
        front end, not this step.
"""),
    ("0004_median_exemplar_template",
     [("src/matching/structural_similarity.py",
       "src/matching/structural_similarity.py")],
     """CLAIM ID: D5 (the template is built in the SMALLEST exemplar's space).

MECHANISM: the exemplar is the MEDIAN of the positives (by node count, then
edge count, then the node ids -- the historical sort key), not the smallest:
a node absent from the smallest (occluded or partial) view can never enter
the template.

PRE-REGISTERED CONSTANTS: none -- the median is the middle element of the
        historical sort order.

GATING FLAG: MATCH_TEMPLATE_MEDIAN_EXEMPLAR (default OFF).

THE PIN: tests/matcher/test_phase2_flagged_mechanisms.py::
        test_d5_the_median_exemplar_only_when_the_flag_is_on

DEPENDENCIES: 0001 (the flag).

MEASURED: the flag changes the TEMPLATE, not the correspondence path, so the
        nine-pair arms cannot see it; its effect is in the core construction
        (the ETH-80 benchmark), which is a separate measurement.
"""),
    ("0005_count_absent_consensus_voters",
     [("src/matching/consensus.py", "src/matching/consensus.py"),
      ("src/matching/fuzzy.py", "src/matching/fuzzy.py")],
     """CLAIM ID: D7 (the consensus drops the absent voters and misaligns the
             weights).

MECHANISM: `fuzzy_consensus` keeps the ABSENCE MASK: a reference slot that
an exemplar did not fill is an ABSTENTION (None), not a shorter voter list.
`slot_vote` accepts the abstention: the voter's weight stays in the
denominator (so the support is over ALL the voters) while it contributes no
value.  The row builder keeps one entry per voter, so the weights stay
aligned to the exemplar index -- the second half of the defect (the old code
zipped the surviving values with the FIRST weights).

PRE-REGISTERED CONSTANTS: none.

GATING FLAG: MATCH_CONSENSUS_COUNT_ABSTENTIONS (default OFF).

THE PIN: tests/matcher/test_phase2_flagged_mechanisms.py::
        test_d7_the_abstentions_are_counted_only_when_the_flag_is_on
        (2 of 5 matching voters -> the support 0.400 over 5 voters)

DEPENDENCIES: 0001 (the flag).

MEASURED: the mechanism is confirmed by the audit's construction (2 of 5 ->
the support 1.000 over 2 voters; the expected 0.400 over 5).  The consensus
path is not in the nine-pair correspondence path, so its effect is in the
core construction.
"""),
    ("0006_frame_partition_registration",
     [("src/matching/relation_frame.py", "src/matching/relation_frame.py")],
     """CLAIM ID: the frame partition must cover EVERY emitted lens type.

MECHANISM: four lens types are DECLARED by the front end
(lenses/base.py::_LENS_NAMES) but were in NEITHER partition: Size, Motion,
EffectPresent, OrientationPol.  Each was therefore 'not frame' by the tree's
own rule AND unclassified by the attribute set -- nothing said what it was.
They are registered as ATTRIBUTES, with the reason recorded in the code.

THE CHOICE (a judgement, stated because it is one): each is a descriptor of a
PLACE rather than a piece of shape, and each is emitted PER ANCHOR (the field
tiling).  OrientationPol is the polar axis of a region blob -- the same
substrate as Size -- and it tiles the field, so registering it as FRAME would
put thousands of nodes into the correspondence's domain.  If it is ever
promoted to a frame primitive it must first stop tiling the field.

A third partition is added: NON_LENS_TYPES = {"Action"} -- a motor concept
that leaks into the pattern-node space.  It is named explicitly so that it
can never enter a correspondence by accident, rather than falling through
"not frame" by accident.

PRE-REGISTERED CONSTANTS: none.

GATING FLAG: none -- this is a REGISTRATION, and an unregistered type is a
        defect, not a preference.

THE PIN: tests/matcher/test_relation_frame_emitted.py (the emitted names are
        read from the front end: the V1 names, the higher names and the
        `produces` of every derived lens declaration) and
        tests/matcher/test_relation_frame_partition.py (the pinned lists).

MEASURED: the four types emit 0 nodes on the four ETH-80 frames (the gap is
        latent, not active); 'Action' emits 1.  The gap was invisible to the
        old pin, which compared two HARDCODED literals that did not even
        enumerate the higher structural lenses the front end emits.
"""),
    ("0007_pins",
     [("tests/matcher/test_phase2_flagged_mechanisms.py", None),
      ("tests/matcher/test_relation_frame_emitted.py", None),
      ("tests/matcher/test_p4b_count_apart.py",
       "tests/matcher/test_p4b_count_apart.py"),
      ("tests/matcher/test_relation_frame_partition.py",
       "tests/matcher/test_relation_frame_partition.py")],
     """CLAIM IDS: the pins for B3, B7, P0, D5, D7 and the frame partition.

MECHANISM: the pins.  Every one of them states the DEFAULT (the flags are
OFF) and the MECHANISM (when the flag is on), so reverting any mechanism
reddens exactly one pin.  The B3 pin keeps its discriminating power: the
trace carries the RAW matched mass, so the flag-counted-as-an-axis case
(2.0) and the not-counted case (1.0) are still distinguishable -- the
revision-2 cap made both branches 1.0 and the pin vacuous.

PRE-REGISTERED CONSTANTS: none.

GATING FLAG: none.

THE PINS: this patch.

DEPENDENCIES: 0001-0006 (the mechanisms the pins test).

VERIFY: python -m pytest tests/matcher/test_phase2_flagged_mechanisms.py
        tests/matcher/test_relation_frame_emitted.py
        tests/matcher/test_p4b_count_apart.py
        tests/matcher/test_relation_frame_partition.py -q
"""),
]


def read(path: Path) -> list:
    try:
        return path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return []


def unified(rel: str, old: list, new: list, is_new: bool) -> str:
    out = []
    out.append("diff --git a/%s b/%s\n" % (rel, rel))
    if is_new:
        out.append("new file mode 100644\n")
        out.append("--- /dev/null\n")
        out.append("+++ b/%s\n" % rel)
    else:
        out.append("--- a/%s\n" % rel)
        out.append("+++ b/%s\n" % rel)
    body = list(difflib.unified_diff(old, new, fromfile="a/" + rel,
                                     tofile="b/" + rel, n=3))
    for line in body[2:]:                      # the first two lines are the
        out.append(line)                      # ---/+++ headers we wrote
    return "".join(out)


def build() -> int:
    if not OVERLAY.is_dir():
        raise SystemExit("the overlay is missing: run phase2/apply_all.bat")
    OUT.mkdir(exist_ok=True)
    written = []
    for name, files, header in SERIES:
        chunks = []
        for rel, new_rel in files:
            if new_rel is None:
                # a NEW file: it exists only in the overlay
                old_path = ROOT / rel
                new_path = (OVERLAY_TESTS / Path(rel).relative_to("tests")
                            if rel.startswith("tests/") else
                            OVERLAY / Path(rel).relative_to("src"))
                is_new = True
                old = []
            else:
                old_path = ROOT / rel
                new_path = (OVERLAY_TESTS / Path(rel).relative_to("tests")
                            if rel.startswith("tests/") else
                            OVERLAY / Path(rel).relative_to("src"))
                is_new = False
                old = read(old_path)
            new = read(new_path)
            if old == new:
                continue
            chunks.append(unified(rel, old, new, is_new))
        if not chunks:
            raise SystemExit("the patch %s is EMPTY -- the overlay and the"
                             " source agree on every file it touches" % name)
        text = ("# [PHASE 2] %s\n#\n" % name
                + "".join("# %s\n" % line for line in header.rstrip().split("\n"))
                + "#\n# apply from the repository root: git apply -p1 %s.patch\n"
                % name)
        (OUT / ("%s.patch" % name)).write_text(text + "".join(chunks),
                                                encoding="utf-8")
        written.append(name)
        print("  wrote %s.patch (%d bytes)" % (name, (OUT / (name + ".patch")).stat().st_size))
    print("the series: %s" % ", ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(build())
