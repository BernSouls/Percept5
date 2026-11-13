# PHASE 2 — THE REVERT

**Every patch has an INDEPENDENT back-out.** Each revert is the reverse diff
of its patch, so the patches can be backed out one at a time, in any order,
without touching the others.

There is no `git` binary on this machine, so the reverse patches are written
by hand here (they are the same hunks with the sides swapped) and applied by
the same applier the forward series is verified with
(`phase2/verify_patches.py` implements `git apply -p1` semantics).

**The overlay's own back-out** (if the overlay is the thing being undone):
delete `phase2/build` — the original `src/` is never written to, so the
overlay has no back-out at all; it is a copy.

---

## 0000 — the harness fix

**Revert:** remove the appended block from `tests/figground/pipeline.py`:

```python
# [PHASE2 H1] merged compatibility names for non-figground tests
import sys as _sys
from orchestration import pipeline as _orch
for _n in ('Pipeline', 'PipelineProviders'):
    if not hasattr(_sys.modules[__name__], _n) and hasattr(_orch, _n):
        globals()[_n] = getattr(_orch, _n)
```

**The consequence:** the 31 collection errors come back (the tests outside
the figground suite that import `Pipeline` cannot import it). **This is the
ONLY patch whose revert is a regression of a fixed defect.**

## 0001 — the flags

**Revert:** delete the five flag declarations from `src/parameters/_text.py`
(the block under "THE NEW FLAGS"). **The consequence:** 0002–0005 read the
flags with `getattr(P, ..., False)`, so they fall back to the historical
behaviour — **the tree still runs and still behaves as it does today.**

## 0002 — B3 and B7

**Revert B3:** in `src/memory/cores.py`, delete the block

```python
    q_matched_em_raw = q_matched_em
    c_matched_em_raw = c_matched_em
    if bool(getattr(P, "MATCH_EDGE_MASS_CONTAINMENT", False)):
        q_matched_em = min(q_matched_em, q_edge_total)
        c_matched_em = min(c_matched_em, c_edge_total)
```

and the two trace lines (`q_matched_em_raw` / `c_matched_em_raw`).

**Revert B7:** in `src/core/schema.py`, remove the `return_none` parameter
and the `if return_none: return None` branch; in `src/memory/cores.py`,
remove the `_skip_incomparable` bookkeeping, the `return_none=` argument and
the `_any_comparable` skip, and restore
`trace["verifiable_core_edges_count"] = len(verifiable_core_edges)`.

**The consequence:** the historical behaviour exactly — the overflow returns
and an incomparable relation is scored 0.0 again.

## 0003 — P0

**Revert:** in `src/memory/mapper.py`, replace

```python
        if bool(getattr(P, "MATCH_KEEP_HIERARCHY_MEMBERS", False)):
            excluded = set()
        else:
            excluded = self._part_exclusions()
```

with `excluded = self._part_exclusions()`.

**The consequence:** the hierarchy step deletes the members again (it is
inert on the measured frames, so nothing changes there).

## 0004 — D5

**Revert:** in `src/matching/structural_similarity.py`, delete the
`if bool(getattr(P, "MATCH_TEMPLATE_MEDIAN_EXEMPLAR", False)):` block and
restore the single `exemplar = min(positives, key=...)` line.

**The consequence:** the template is built in the smallest exemplar's space
again.

## 0005 — D7

**Revert:** in `src/matching/consensus.py`, remove the `n_voters` parameter
from `slot_vote` and `vote_consensus`, restore
`support = counts[mode] / total_w` and `support = near / total_w`, and
restore the `pairs` list comprehension without the `v is not None` test; in
`src/matching/fuzzy.py`, restore the filtered row builder
(`[c[i] for c in cols if i < len(c)]`) and drop the `n_voters=` argument.

**The consequence:** 2 of 5 matching voters report the support 1.000 over 2
voters again.

## 0006 — the registration

**Revert:** in `src/matching/relation_frame.py`, remove the four attribute
types ("Size", "Motion", "EffectPresent", "OrientationPol") and the
`NON_LENS_TYPES` block; in `tests/matcher/test_relation_frame_partition.py`,
remove the four names from `V1_TIER` and from the expected attribute set.

**The consequence:** the four declared lens types are unclassified again —
and `test_relation_frame_emitted.py` (which is NOT reverted here) reddens,
which is the point: the gap is real.

## 0007 — the pins

**Revert:** delete the two new pin files and the two amended blocks. **The
consequence:** the mechanisms are no longer guarded; the tree still runs.

---

## THE ORDER-SAFE WAY TO BACK OUT EVERYTHING

Back out 0007 first, then 0006 … 0001 in reverse order. Each patch is
independent, so any subset works; the reverse order is simply the tidiest.
