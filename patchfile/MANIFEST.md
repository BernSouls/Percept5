# PHASE 2 — THE MANIFEST

**The deliverable is a patch series. It applies to the ORIGINAL tree; the
overlay (`phase2/build/`) is only the working copy the series was generated
from and verified against.**

```
cd E:\Take25\work                 # the repository root
git apply -p1 phase2/patches/0000_harness_figground_pipeline.patch
git apply -p1 phase2/patches/0001_matcher_flags.patch
git apply -p1 phase2/patches/0002_edge_mass_containment_and_incomparable.patch
git apply -p1 phase2/patches/0003_keep_hierarchy_members.patch
git apply -p1 phase2/patches/0004_median_exemplar_template.patch
git apply -p1 phase2/patches/0005_count_absent_consensus_voters.patch
git apply -p1 phase2/patches/0006_frame_partition_registration.patch
git apply -p1 phase2/patches/0007_pins.patch
```

**The series changes NO behaviour until a flag is set.** Every mechanism is
behind a new flag whose default is the historical behaviour; the only
behaviour-free-by-construction changes are the HARNESS fix (0000) and the
REGISTRATION (0006), which close gaps rather than alter a decision.

## THE SERIES

| # | the patch | the claim | the mechanism | the flag (default) | the pin |
|---|---|---|---|---|---|
| 0000 | `0000_harness_figground_pipeline` | H1 | the figground fixture stops shadowing `orchestration.pipeline`'s names | — | the collection: 0 errors |
| 0001 | `0001_matcher_flags` | — | the five new flags are declared | — | `test_every_new_flag_defaults_to_the_historical_behaviour` |
| 0002 | `0002_edge_mass_containment_and_incomparable` | **B3, B7** | the matched edge mass is capped at its own total (the RAW mass stays in the trace); an incomparable relation is skipped from the numerator AND the denominator | `MATCH_EDGE_MASS_CONTAINMENT`, `MATCH_SKIP_INCOMPARABLE_RELATIONS` (both **False**) | `test_b3_the_containment_caps_the_matched_edge_mass`, `test_b7_an_incomparable_relation_is_skipped_not_scored`, `test_the_edge_mass_of_a_flag_loses_its_facilitation` |
| 0003 | `0003_keep_hierarchy_members` | **P0** | the hierarchy step keeps the member (additive) | `MATCH_KEEP_HIERARCHY_MEMBERS` (**False**) | `test_p0_the_member_is_kept_only_when_the_flag_is_on` |
| 0004 | `0004_median_exemplar_template` | **D5** | the template is built in the MEDIAN exemplar's space | `MATCH_TEMPLATE_MEDIAN_EXEMPLAR` (**False**) | `test_d5_the_median_exemplar_only_when_the_flag_is_on` |
| 0005 | `0005_count_absent_consensus_voters` | **D7** | an exemplar that did not fill a slot is an abstention: it stays in the denominator, and the weights stay aligned to the exemplar index | `MATCH_CONSENSUS_COUNT_ABSTENTIONS` (**False**) | `test_d7_the_abstentions_are_counted_only_when_the_flag_is_on` |
| 0006 | `0006_frame_partition_registration` | the partition gap | the four DECLARED but unregistered lens types are registered as attributes; `Action` becomes an explicit NON_LENS type | — | `test_relation_frame_emitted.py`, `test_the_partition_is_the_pinned_list` |
| 0007 | `0007_pins` | — | the pins themselves | — | the four pin files |

## THE VERIFY COMMAND PER PIN

```
python -m pytest tests/matcher/test_phase2_flagged_mechanisms.py \
                 tests/matcher/test_relation_frame_emitted.py \
                 tests/matcher/test_p4b_count_apart.py \
                 tests/matcher/test_relation_frame_partition.py -q
```

**The series is verified mechanically** (`python phase2/verify_patches.py`):
it is applied to a scratch copy of the tree and the result must be
**byte-identical** to the overlay. There is no `git` binary on this machine,
so the applier implements `git apply -p1` semantics (the prefixes are
stripped, the hunks are applied at their stated line numbers, and a context
mismatch is an ERROR, never a fuzzy match).

## THE OVERLAY (the working copy)

```
phase2/apply_all.bat      # rebuild the overlay from src/ and run the checks
phase2/verify_overlay.py  # the mechanism checks (each prints the loaded path)
phase2/gen_patches.py     # regenerate the series from the overlay
phase2/verify_patches.py  # apply the series to a scratch tree and compare
```

`apply_all.bat` **never writes to `src/`**: it copies the tree into
`phase2/build/src`, applies the mechanisms, and runs the pins against the
copy. The mechanism checks assert that the loaded modules live under
`phase2/build` — the harness trap (the original `src/` at the front of
`sys.path`) is checked, not assumed.

## THE MEASUREMENTS (precision first; the truth's row carried)

**The nine registered pairs, the M3-6 role metric**
(`diagnostics/phase2_nine_pair_arms.py`):

| the arm | P | R | F1 | mapped | rel/match |
|---|---|---|---|---|---|
| **the renderer truth's own mapping** | **0.967** | **0.696** | **0.802** | 92.4 | — |
| the baseline (every flag OFF) | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B3 the containment | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B7 the incomparable skip | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B7b identity-only is presence | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B3 + B7 + B7b | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| P0 keep the member | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |

**EVERY ARM IS IDENTICAL TO THE BASELINE.** These are CONTRACT corrections:
the overflow never binds on this corpus, there is no cross-ontology edge pair
in it, and the hierarchy step is inert on it. **They are correct, pinned and
inconsequential** — and the report says so rather than claiming a gain.

**The P0 target is elsewhere** (`diagnostics/phase2_spine_census.py`): the
physical pattern-pattern edges 3 017 over four ETH-80 frames → the situation
graph 740; **the hierarchy step deletes 0 of them**; the loss is upstream, in
the situation graph's own construction. Per family: the structural spine
survives (CONTOUR_CONTINUITY 93.5 %, JUNCTION_CONTOUR 92.2 %,
CURVATURE_SIGN_CONTINUITY 95.6 %, RADIALITY 95.3 %) while the ORIENTATION
family is nearly absent (ORIENTATION_CONTINUITY 178 → 1, ORIENTATION_BEND
66 → 0, ORIENTATION_JUNCTION 54 → 0). **180 Orientation nodes are produced by
the front end and NONE reach the matcher.** That is the P1 target.
