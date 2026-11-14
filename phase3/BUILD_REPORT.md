# Finished-build evaluation

Build: `percept5-frontend-build-v1`; protocol amendment in `audit/build-protocol.json`. First measurement seed 0; fresh-process repeat seed 1729. No tuning after measurement.

## Scope and comparability

ETH80_ALL8 is 136 independent 256×256 frames (8 references, 128 object-disjoint evaluation frames; all eight classes). The historical Phase 0 baseline is ETH80_REF4_plus_EVAL75_native256 (79 frames, four classes), so before/after rates below are descriptive, **not paired causal comparisons**. RENDERER_TRUTH_V1 contains 15 independent 192×192 scenes and nine registered pairs; there is no comparable Phase 0 role-oracle result.
The original wording “first two objects” conflicted with object-disjoint evaluation against reference object 1. Before measurement the manifest was corrected to objects 2 and 3; the amendment records this.

## Frame and edge budgets

| Corpus | Before | After | Registered criterion |
|---|---|---|---|
| ETH80_ALL8 | 10.4 s/frame mean; 50-node historical cap | 136/136 frames; frame median 9.267 s, p95 9.987 s, max 12.983 s; selected edges/frame max 458 | frame p95 ≤30 s and max ≤60 s: **PASS**; edges ≤512: **PASS** |
| RENDERER_TRUTH_V1 | not measured | 15/15 frames; frame median 6.927 s, p95 7.367 s, max 7.616 s; selected edges/frame max 302 | frame p95 ≤30 s and max ≤60 s: **PASS**; edges ≤512: **PASS** |

The first 8 reference frames ran while a preliminary repeat/regression was briefly active; timings are wall-clock and include that contention. Match timing below was measured without the repeat running.

## Edge-family survival

Selected counts divided by complete-window counts, aggregated per corpus. A zero caused by non-frame endpoints is reported explicitly; CO_LOCATED, CONTACT, PROXIMITY and SURFACE_GROUPING are excluded by design, with attributes carried as named features instead. The Phase 0 before arm is its capped spatial situation, not the new selected graph.

| Edge family | Before: Phase 0 % | ETH80_ALL8 selected/window (%) | RENDERER_TRUTH_V1 selected/window (%) | Missing structural family reasons (ETH / renderer, frame counts) |
|---|---:|---:|---:|---|
| AMODAL_LINK | 0.00% | 195/195 (100.00%) | 39/39 (100.00%) | — |
| BORDER_OWNERSHIP_EDGE | 13.30% | 0/838 (0.00%) | 0/35 (0.00%) | no_frame_endpoints: 127/10 |
| COCIRCULAR | 0.00% | 449/449 (100.00%) | 59/59 (100.00%) | — |
| COLOR_OPPONENT_BORDER | 0.00% | 0/7385 (0.00%) | 0/214 (0.00%) | no_frame_endpoints: 136/15 |
| CONCENTRICITY | 0.00% | 130/130 (100.00%) | 36/36 (100.00%) | — |
| CONTACT | 0.00% | 0/849 (0.00%) | 0/14 (0.00%) | — |
| CONTOUR_CONTINUITY | 0.00% | 1245/1246 (99.92%) | 159/159 (100.00%) | — |
| CONTOUR_ORIENTATION | 0.12% | 5011/16501 (30.37%) | 529/1079 (49.03%) | — |
| CO_LOCATED | 0.08% | 0/26843 (0.00%) | 0/2825 (0.00%) | — |
| CURVATURE | 0.00% | 87/106 (82.08%) | — | — |
| CURVATURE_SIGN_CONTINUITY | 0.00% | 1002/1003 (99.90%) | 155/155 (100.00%) | — |
| CURVE_CONTAINMENT | 0.55% | 917/923 (99.35%) | 120/120 (100.00%) | — |
| DEGREE | 0.00% | 0/114 (0.00%) | 0/2 (0.00%) | no_frame_endpoints: 58/1 |
| JUNCTION_CONTOUR | 1.56% | 1022/1022 (100.00%) | 149/149 (100.00%) | — |
| JUNCTION_ORIENTATION | 0.82% | 475/475 (100.00%) | 65/65 (100.00%) | — |
| LINE_TERMINATION | 1.44% | 92/92 (100.00%) | 19/19 (100.00%) | — |
| OCCLUSION | 0.00% | 0/2 (0.00%) | 0/1 (0.00%) | no_frame_endpoints: 2/1 |
| ORIENTATION_BEND | 0.00% | 1751/1769 (98.98%) | 91/91 (100.00%) | — |
| ORIENTATION_CONTINUITY | 0.00% | 3515/3561 (98.71%) | 386/386 (100.00%) | — |
| ORIENTATION_JUNCTION | 0.00% | 1172/1179 (99.41%) | 207/207 (100.00%) | — |
| PARALLEL | 0.00% | 355/355 (100.00%) | 82/82 (100.00%) | — |
| RADIALITY | 0.00% | 674/674 (100.00%) | 102/102 (100.00%) | — |
| REGION_CONTENT | 0.13% | 263/23998 (1.10%) | 19/917 (2.07%) | no_frame_endpoints: 47/12 |
| SPIRALITY | 0.00% | 341/341 (100.00%) | 45/45 (100.00%) | — |
| SYMMETRY | 0.00% | 532/532 (100.00%) | 92/92 (100.00%) | — |
| TOPOLOGY | 0.00% | 0/2358 (0.00%) | 0/48 (0.00%) | no_frame_endpoints: 129/8 |

Criterion: every present structural family absent from the selected graph needs an explicit reason. **PASS for reason disclosure**, not a claim of preservation: the table shows families with zero selected edges. Excluded attribute relations are outside the structural-family coverage criterion.

### Largest FRAME component

- ETH80_ALL8: median largest component, all edges 42.5, structural edges 42.5; median per-frame structural/all ratio 1.000. Before: not measured on this corpus/scope. Registered requirement is disclosure, not a numeric threshold: **PASS**.
- RENDERER_TRUTH_V1: median largest component, all edges 47.0, structural edges 47.0; median per-frame structural/all ratio 1.000. Before: not measured on this corpus/scope. Registered requirement is disclosure, not a numeric threshold: **PASS**.

## Renderer nine pairs: role oracle versus bounded fuzzy solver

Before: no independently measured comparable role-oracle baseline. The truth denominator for each pair is Σ min(role counts) over roles `(object_id, lens_type, signature_class)`. The truth row uses that same denominator; when it is zero, recall and F1 are undefined. Coordinates missing from the pattern-node registry and background nodes have no object role. Predictions involving them remain in the precision denominator, so precision below is a conservative lower bound, not a measured exact precision. See per-pair role availability in `results/build-pairs-seed0.json`.

| Pair | Truth TP / denominator; P / R / F1 | Returned solver TP / predicted / denominator; P / R / F1 | Objective truth / returned | Match seconds |
|---|---|---|---:|---:|
| single_box / texture_box | 6/6; 1.000 / 1.000 / 1.000 | 4/110/6; 0.036 / 0.667 / 0.069 | 0.000000 / 0.174500 | 0.388 |
| single_disk / single_box | 0/0; — / — / — | 0/107/0; 0.000 / — / — | 0.000000 / 0.199812 | 0.100 |
| single_cylinder / single_disk | 0/0; — / — / — | 0/101/0; 0.000 / — / — | 0.000000 / 0.154170 | 0.092 |
| box_occlusion / box_occlusion_haze | 28/28; 1.000 / 1.000 / 1.000 | 25/173/28; 0.145 / 0.893 / 0.249 | 0.000000 / 0.569993 | 0.147 |
| cylinder_occlusion / cylinder_occlusion_haze | 58/58; 1.000 / 1.000 / 1.000 | 57/198/58; 0.288 / 0.983 / 0.445 | 0.022429 / 0.707614 | 0.200 |
| disk_occlusion / disk_occlusion_haze | 82/82; 1.000 / 1.000 / 1.000 | 80/190/82; 0.421 / 0.976 / 0.588 | 0.045185 / 0.630873 | 0.284 |
| view_cylinder_000 / view_cylinder_015 | 30/30; 1.000 / 1.000 / 1.000 | 30/128/30; 0.234 / 1.000 / 0.380 | 0.000000 / 0.505092 | 0.090 |
| view_cylinder_015 / view_cylinder_030 | 30/30; 1.000 / 1.000 / 1.000 | 26/142/30; 0.183 / 0.867 / 0.302 | 0.000000 / 0.484825 | 0.109 |
| view_cylinder_030 / view_cylinder_045 | 30/30; 1.000 / 1.000 / 1.000 | 27/150/30; 0.180 / 0.900 / 0.300 | 0.000000 / 0.430872 | 0.127 |

Micro: 249/1299/264; conservative P 0.192, R 0.943, F1 0.319. Pair objective uses a deterministic canonical member of each role equivalence class; it is not a uniquely specified geometric ground-truth correspondence.
The product fuzzy alignment is bounded and heuristic, so the returned objective is **not a certified global optimum**. A global-optimum criterion is therefore **not evaluated**; the truth-versus-returned measurements are shown without claiming proof.
Match timing before: unavailable. After: median 0.127 s, p95 0.347 s, max 0.388 s over 9 matches. Criterion p95 ≤1 s and max ≤3 s: **PASS**. No registered P/R/F1 threshold was specified; do not infer a pass from these low-precision results.

## ETH80_ALL8 class information

Joint symbol is `(quantized tuple, population-axis presence pattern)` on selected nodes, grouped by lens/class. Primary null permutes whole-image labels 999 times, seed 1729; 128 evaluation images, eight classes. Before values below come from the Phase 0 complete window, 79 frames/four classes and 1000 permutations, so they are not a matched comparison. No numeric MI pass threshold was registered.

| Lens / class | Before MI bits (different corpus/scope) | After n | After MI bits | Image-level permutation p |
|---|---:|---:|---:|---:|
| Arrow / JUNCTION | — | 16 | 2.3278 | 0.646 |
| CONTOUR_PEAK / CONTOUR_PEAK | 0.889 | 16693 | 1.1522 | 0.001 |
| Contour / CONTOUR | 0.912 | 1152 | 1.4004 | 0.999 |
| ContourFragment / CONTOUR_FRAGMENT | 1.222 | 8263 | 1.5773 | 0.001 |
| Corner / CORNER | 0.732 | 2003 | 0.8873 | 1.000 |
| CurveComplex / CURVE_COMPLEX | 0.889 | 872 | 1.3101 | 0.163 |
| EndStopped / ENDSTOPPED | 0.184 | 4997 | 0.2106 | 0.014 |
| IllusoryContour / ILLUSORY_CONTOUR | 1.174 | 290 | 1.6061 | 1.000 |
| Junction / JUNCTION | 1.633 | 10 | 2.1710 | 0.891 |
| L / JUNCTION | — | 139 | 1.7093 | 0.887 |
| Orientation / ORIENTATION | 0.952 | 4498 | 0.9641 | 0.001 |
| Orientation / ORIENTATION_SEGMENT | 1.580 | 182 | 2.6109 | 0.401 |
| PEAK_CHAIN / PEAK_CHAIN | 0.793 | 3036 | 1.1347 | 0.052 |
| RegionShape / REGION_SHAPE | 1.753 | 2124 | 2.7744 | 1.000 |
| T / JUNCTION | 1.550 | 21 | 2.4343 | 0.819 |
| Y / JUNCTION | 0.000 | 8 | 2.0000 | 0.641 |

## Closure flags (partial scope)

Before: Phase 0 PEAK_CHAIN closure was constantly zero on the historical four-class complete-window corpus. After: counts below are selected matcher-input pattern nodes, not the complete detection stream. Observation-contour flags were not recorded, so the full registered three-source closure criterion remains **NOT EVALUATED**.

- ETH80_ALL8 CONTOUR: 50/1207 closed; 1157 open, 0 absent.
- ETH80_ALL8 PEAK_CHAIN: 0/3229 closed; 3229 open, 0 absent.
- RENDERER_TRUTH_V1 CONTOUR: 18/150 closed; 132 open, 0 absent.
- RENDERER_TRUTH_V1 PEAK_CHAIN: 2/172 closed; 170 open, 0 absent.

## Renderer margin

Before: unavailable on RENDERER_TRUTH_V1. After: using 4-neighbour visible-foreground perimeter sides, classified by their foreground pixel centre, the 192-pixel controls have a 42-pixel largest-kernel margin. Single box 0/360, single cylinder 0/324, single disk 0/416 sides outside; each has zero wholly discarded components. Centered-control criterion ≤10%: **PASS**. The fresh-process repeat JSON has the same SHA-256.

## Eight-class filter and named pooling audit

Before: Phase 0 had zero post-filter edges in all eight arm/class rows, on a different four-class corpus. After: **FAIL / NOT EVALUABLE**: content pooling aborted at evaluation frame 3, `apple2-022-180.png`, with `[CONTENT HASH FAULT] feature-aware content ID collision`. No class templates or positive/negative scores were produced; do not interpret this as a successful filter criterion. The fresh-process seed-1729 attempt failed at the same frame with the same error.
Post-measurement diagnosis: the two feature bundles were unequal in full precision but identical after `serialize_value` rounded their floats to 1e-6; the feature-aware content-ID collision guard then rejected them. This is a product-path defect, not evidence that the filter passes. It is not patched or tuned after seeing the corpus results.

## Determinism

Fresh process, hash seeds 0 and 1729: 151/151 canonical frame SHA-256s equal; census equal: True; pairs equal: True. Runtime and provenance timestamps excluded. **PASS** for these completed measurements. The filter failed identically in both processes. See `results/build-determinism.json` for each frame.

## Singleton and explicit limits

Off-correspondence null was registered before this measurement. Identical edgeless singleton: before chance 1.0 / score 0.0; after chance 0.0 / score 0.5. The 0.5 factor is the registered no-alternative finite-sample rule. The singleton and off-correspondence pins pass.
The named ABSENT/pooling follow-up remains separate and does not gate these measurements. Other registered diagnostics not fully captured by this run (including observation-contour closure, leak-channel interventions, translation drift and retrieval-recall probes) are **not evaluated** here; do not treat the listed results as a complete pass of those criteria.
