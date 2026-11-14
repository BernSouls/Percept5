# PHASE 0 — INDEPENDENT CONFIRMATION REPORT

Branch: `arena/5afe7334-percept5`  
Base HEAD: `1c35a03f20c848cd898119d984c2165c1b410d2c`  
Protocol: `phase3/audit/protocol.json` (`percept5-phase0-independent-v1`, amendments A0/A1)  
Scope: measurement and report only. No front-end redesign, no new patch series, no default selected.

Corpus availability:

- **Current measured corpus:** reconstructed pinned ETH-80 split, 79 images = 4 references + 75 eval, native 256×256 unless explicitly labeled `_96`.
- **Historical 60-graph corpus:** artifact missing → historical numbers depending on it are **UNKNOWN / CORPUS MISSING**.
- **Historical four-frame 96² sample:** identity manifest missing → not asserted identical to the current four reference images.
- **Synthetic nine:** recovered scene builders from the pinned Percept4 export; used for Position correlation/ablation, not for the historical renderer-truth P/R/F1 arms.

## 0. Execution status

| run | result |
|---|---|
| `analyze_census.py` | EXIT=0; wrote entropy/presence, MI, filter (both median arms), distance spans, margins, native totals |
| `analyze_census.py` deterministic repeat | EXIT=0; **0 result JSON files changed** |
| `junction_views.py` | EXIT=0; exactly **41** unique apple object-1 view PNGs |
| `position_pairs.py` | EXIT=0; includes the six per-pair Position/anchor decomposition counters |
| `position_pairs.py` deterministic repeat | EXIT=0; SHA-256 match: `3b9d475ce0e629b76d4c84ad0f16a9e9e289cce310e46a4c34cd78f055770c0e` |
| phase2 pins | **38 passed in 1.12s** (`phase3/audit/pins-final.log`) |
| matcher suite | **510 passed in 41.19s** (`phase3/audit/matcher-final.log`) |
| result hashes | `phase3/audit/final-status.json` |

Product edit in the working tree is still only the syntax/indentation repair in `lenses/base.py` required to import the module. No measurement constant or mechanism was changed.

Verdict legend:

- **CONFIRMED AT HEAD** — independently measured or statically verified on the current tree.
- **REFUTED AT HEAD** — current tree contradicts the claim.
- **PARTIAL** — one component holds, another does not.
- **CONTRACT CONFIRMED** — flag/pin behavior verified; accuracy effect not claimed.
- **UNKNOWN / CORPUS MISSING** — historical number cannot be reproduced because the original corpus/artifact identity is unavailable. No substitute number is presented as the historical one.

## 1. Confirmation table — historical `patchfile/VERIFICATION.md` §4

The original patch bundle has since been removed after integration; its application and verification records remain in `phase3/audit/phase2_apply.log`, `phase3/audit/phase2-patch-verification.md` and `phase3/audit/build-patch-status.json`.

| # | claim | verdict | anchor `file:line` | measured number | corpus / scope |
|---:|---|---|---|---|---|
| 1 | Orientation spine never reaches the matcher; historical 180 Orientation nodes → 0, ORIENTATION_CONTINUITY 178 → 1 | **PARTIAL AT HEAD; historical counts UNKNOWN / CORPUS MISSING** | `memory/mapper.py:1614`, `memory/mapper.py:162`; `lenses/base.py:2203`, `lenses/base.py:2390` | Orientation nodes: **4,141 window → 79 spatial** (one per frame floor reserve). Orientation relation edges: **ORIENTATION_CONTINUITY 4,093 → 0**, **ORIENTATION_BEND 2,288 → 0**, **ORIENTATION_JUNCTION 1,536 → 0**. Historical 180/0/178/1 not reproduced. | `ETH80_REF4_plus_EVAL75_native256`, 79 frames; spatial = capped `Mapper._spatial_situation` |
| 2 | Depth slot is fabricated: constant bin 8.0, 0.0000 bits | **REFUTED AT HEAD for 2D input; historical constant UNKNOWN / CORPUS MISSING** | `lenses/base.py:1959`–`1970`; `core/schema.py:135` | Position `dz`: **UNKNOWN in 7,436/7,436 detections**, entropy **None / ABSENT**, not 0 bits and not bin 8.0. `dx` H=3.980041 bits, `dy` H=3.969553 bits. Historical 1,653 nodes / `[8.0]` not reproduced. | `ETH80_REF4_plus_EVAL75_native256`; HEAD source after syntax-only import repair |
| 3 | Position signature double-counts anchor: r=0.8403; 0/4,089 mapped pairs change on Position removal; 828 change on anchor removal | **DIRECTIONALLY CONFIRMED; historical numbers UNKNOWN / CORPUS MISSING** | `memory/cores.py:785`, `:813`, `:824`, `:1089`, `:1949`; `lenses/base.py:1802` | Pooled Pearson **r=0.930512** over **80,089** candidate Position pairs. Baseline mapped **3,775** = 2,929 non-Position + 846 Position. Position removal: **0/2,929 non-Position pairs changed**, **846 Position pairs removed**. Anchor removal: mapped count still 3,775, but **1,350 pair memberships changed** (675 removed + 675 added): 1,334 non-Position + 16 Position. Historical r=0.8403 / 0-of-4,089 / 828 not reproduced. | `SYNTHETIC_NINE`, 17 scenes / 9 pairs; scope `hierarchy_exclusions_off` (keep-members=False), **not** capped spatial situation; metric `mcs_score`, not renderer-truth P/R/F1 |
| 4 | Four declared lens types were unclassified, now registered; attribute families decimated: CO_LOCATED 5.7%, REGION_CONTENT 8.3%, CONTOUR_ORIENTATION 5.6% | **REGISTRATION CONFIRMED AT HEAD; decimation confirmed, historical rates UNKNOWN / CORPUS MISSING** | `matching/relation_frame.py:85`, `:110`–`113`, `:120`–`125`; `memory/mapper.py:1614` | Unregistered window nodes: **0**. `Size`, `Motion`, `EffectPresent`, `OrientationPol` are attributes; `Action` is NON_LENS. Current window→spatial survival: **CO_LOCATED 14/17,404 = 0.0804%**, **REGION_CONTENT 15/11,494 = 0.1305%**, **CONTOUR_ORIENTATION 12/10,305 = 0.1164%**. Historical 5.7/8.3/5.6% not reproduced. | `ETH80_REF4_plus_EVAL75_native256` |
| 5 | Live `evidence_score` path never calls `is_frame`; frame restriction exists only in walker/dark graded solver | **CONFIRMED AT HEAD** | `memory/cores.py:2027`, `:1089`; `matching/graded_mcs.py:541`–`545`; `matching/relation_walker.py:354` | `is_frame` occurrences in `memory/cores.py`: **0**. Spatial situation contains **3,108 attribute nodes / 3,950 total = 78.68%**; frame nodes **842**. | HEAD source + `ETH80_REF4_plus_EVAL75_native256` |
| 6 | No explicit junction primitive at floor; no T/Y/Arrow/L node class; T/Y aliases have no emitter | **REFUTED AT HEAD for Corner/T/Y; Arrow/L remain absent** | `lenses/v2.py:1057`–`1089`, `:1091`, `:1432`; `parameters/_text.py:1127`–`1133`; `matching/relation_frame.py:73`–`74` | Native junction kinds: **Corner 153, Junction 99, T 31, Y 3**. Topologies: `{0:44, 1:153, 2:31, 3:3, 4:2, 6:53}`. Apple-1 41-view probe: **55 junctions = Corner 39, Junction 13, T 3**; no Y in that object; no Arrow/L emitter found. | `ETH80_REF4_plus_EVAL75_native256` + `ETH80_OBJECT1_96` |
| 7 | Additive relational objective is INVERTED: stage-10 proven optimum is worse than renderer truth | **UNKNOWN / CORPUS MISSING** | `memory/cores.py:1949`, `:2027` | No Phase-0 stage-10 inversion measurement was run; historical stage-10 artifact/corpus is unavailable. **No number assigned.** | historical stage-10 corpus missing |

## 2. Confirmation table — task-summary work items

| item | verdict | anchor `file:line` | measured number | corpus / scope |
|---|---|---|---|---|
| F1 — filter/template collapse; median-exemplar arm | **CONFIRMED AT HEAD on class-level templates; median ON does not rescue edges** | `consolidator.py:303`; `memory/distributions.py:98`, `:243`, `:358`, `:398`; `matching/structural_similarity.py:1373`, `:1435`, `:1631`; `parameters/_text.py:2277` | Both median arms: **core_edges_after = 0 in all 8 rows**. OFF template edges 0/0/0/0; ON template edges 2/1/1/1 but materialized core edges after filter 0. Template degree-zero share: OFF **1.000** all classes; ON **0.769–0.857**. Attribute mass share **0.351–0.522**. | `ETH80_REF4_plus_EVAL75_native256`; four class-level templates (A0), not leave-one-out query accuracy |
| P1 — graded populations / class information | **PARTIAL: graded tuples carry class MI for some lenses; population-presence pattern is class-constant; several slots degenerate** | `phase3/harness/analyze_census.py:44`, `:87`, `:146`; `core/registries.py:860`–`861`; `lenses/base.py:1652` | Per-axis population-presence pattern: **1 distinct pattern, H=0.000000 bits in all 24 lens/class groups**. Joint MI significant under both image-level and node-level nulls for **9** groups; image-level only for **4**; neither for **11**. Constant/ABSENT slots listed in §4.2. | `ETH80_REF4_plus_EVAL75_native256`; MI seed 20261113, 1000 permutations |
| P2 — junction kinds | **CONFIRMED AT HEAD for Corner/T/Y/residual Junction; Arrow/L absent** | `lenses/v2.py:1057`; `phase3/harness/junction_views.py:16` | Exactly **41** unique views; **55** junctions; kind H=**1.072427 bits**, topology H=**1.256637 bits**; **8** views with zero junctions. | `ETH80_OBJECT1_96` apple object-1 |
| P3 — intrinsic frames / frame-vs-attribute partition | **REGISTRATION CONFIRMED; live frame restriction ABSENT** | `matching/relation_frame.py:68`, `:85`, `:125`; `memory/cores.py:2027` | Unregistered nodes **0**. Window frame/attribute nodes: **23,840 / 33,256**; spatial frame/attribute nodes: **842 / 3,108**. `evidence_score` does not call `is_frame`. | HEAD + `ETH80_REF4_plus_EVAL75_native256` |
| P4 — contour profile | **CONFIRMED present but with degenerate slots, span violations, and perturbation sensitivity** | `lenses/base.py:1233`; `core/registries.py:858`; `perception/contour_field.py:360`, `:410`, `:462` | Contour `corner_count` constant **0**; PEAK_CHAIN `closure` constant **0**. EDGE_CONTOUR_CONTINUITY `dist`: **94.2055%** outside [0,2]; EDGE_JUNCTION_CONTOUR `dist`: **88.3032%** outside [0,2.5]. ±2px fragment signatures changed **319/536**; ±3px **332/584**; occlusion **7/7** matched fragments changed. | native256 + `ETH80_EVAL75_96` + `SYNTHETIC_CONTROLS` |
| P5 — topological relations | **CONFIRMED: categorical identity more translation-stable than graded bins; orientation relation distances outside declared spans; most families absent from capped spatial graph** | `core/schema.py:1520`, `:2260`; `memory/mapper.py:1614` | ±2px topological identity same **4,314/4,587 = 94.0484%** vs graded bins **3,216/4,587 = 70.1112%**. ±3px: **3,531/3,744 = 94.3109%** vs **2,645/3,744 = 70.6464%**. EDGE_ORIENTATION_BEND/JUNCTION `spatial_dist`: **100%** outside [0,1]. 18 of 26 window edge families have **0** spatial survivors. | native256 + `ETH80_EVAL75_96` |
| P6 — degenerate channels | **CONFIRMED** | `lenses/base.py:1652`–`1686`, `:1970`, `:2616`; `parameters/_text.py:315` | Position `dz` ABSENT; Onset `recency` constant 0; CurveComplex `n_contours`=1, `n_junctions`=0; RegionShape `area`=0; Surface `grad_mag`/`grad_side`=0. Flat grey/white controls: Orientation **0**; all 256/256 regions below roughness gate. Noise control: Orientation **41**. Isotropy↔elongation Pearson **0.990685–1.000000** on all four controls. | native256 + `SYNTHETIC_CONTROLS` |
| Matcher-side flags B3/B7/B7b/P0/D5/D7/frame partition | **CONTRACT CONFIRMED by pins; nine-pair accuracy arms NOT RE-MEASURED** | `parameters/_text.py:2255`, `:2274`–`2278`; `memory/cores.py:1665`–`1677`, `:1576`, `:1612`; `matching/fuzzy.py:254`–`276`; `matching/relation_frame.py:110`–`121` | Pins **38 passed**; matcher suite **510 passed**. Defaults: B3/B7/B7b/P0/D5/D7 all **False**; `JUNCTION_FAMILY_SPLIT` **True**. Historical nine-pair P/R/F1 table is inherited, not independently re-run here. | HEAD pins; historical nine-pair role-metric corpus/harness missing |
| P0 hierarchy inertness | **HISTORICAL SITUATION-GRAPH CLAIM UNKNOWN / CORPUS MISSING; complete-window effect measured and large** | `memory/mapper.py:1746`–`1765`; `parameters/_text.py:2276` | On complete window, shipped keep-members=False deletes **4,393 nodes** (Contour 1,090 + Orientation 3,303) and **33,361 edges** relative to keep-members=True. Historical “0 of 740 situation-graph edges” refers to a different capped scope and is not reproduced. | `ETH80_REF4_plus_EVAL75_native256`; window scopes, not historical four-frame situation graph |
| Precision-first / nine pairs / corpus labels | **PROTOCOL FOLLOWED; historical renderer-truth P/R/F1 UNKNOWN / CORPUS MISSING** | `phase3/audit/protocol.json`; `phase3/harness/position_pairs.py:51` | Nine synthetic pairs measured for Position correlation/ablation only. Every cited number above carries a corpus label. Inherited truth P .967/R .696/F1 .802 and flag-arm P .640/R .688/F1 .662 are **not** claimed as Phase-0 measurements. | `SYNTHETIC_NINE`; historical role-metric harness missing |

## 3. Harness file list

| path | role |
|---|---|
| `phase3/runtime/bootstrap.py` | local-tree assertion, module loading, provenance, canonical JSON writer |
| `phase3/runtime/pytest_guard.py` | test-path guard / namespace handling |
| `phase3/runtime/shims/sensory_floor.py` | reference shim for missing sibling import |
| `phase3/run_pytest.sh` | guarded pytest entry point |
| `phase3/harness/frontend.py` | independent SensoryFloor→Pipeline→Binder→StateIndex→Mapper probe; returns window, capped spatial, and both hierarchy arms |
| `phase3/harness/metrics.py` | entropy, MI, canonical typed ordering keys, quantiles, correlation, connected components |
| `phase3/harness/native_census.py` | 79-frame native ETH-80 census; per-frame JSON cache; writer-argument capture |
| `phase3/harness/analyze_census.py` | entropy/presence, image-level + node-level MI, both filter arms, distance spans, margins, totals |
| `phase3/harness/perturbation.py` | ±2/±3 px translations, occlusion fixture, flat/noise controls |
| `phase3/harness/junction_views.py` | exactly 41 unique apple object-1 views; junction kind/topology distribution |
| `phase3/harness/position_pairs.py` | nine synthetic pairs; Position/anchor correlation and decomposed ablations |
| `phase3/harness/aggregate_results.py` | deterministic cache-only aggregation: native flow and perturbation stability |
| `phase3/inputs/eth80_split.json` | pinned 79-image split: 4 references + 75 eval |
| `phase3/audit/protocol.json` | pre-registered rules and amendments A0/A1 |
| `phase3/results/*.json` | machine-readable measurements |
| `phase3/audit/final-status.json` | exit codes, repeat determinism, result SHA-256 manifest |

Restored support files (not measurement harness): `tests/matcher/*`, `tests/figground/*`, `diagnostics/*` from the pinned Percept4 export. They are used only where stated (synthetic scene construction and existing pins).

## 4. Measured numbers

### 4.1 Native flow and totals

Corpus: `ETH80_REF4_plus_EVAL75_native256` — 79 frames, original 256×256 RGB, shipped defaults, independent fresh graph per frame.

| scope | nodes | edges |
|---|---:|---:|
| complete window / keep-members=True arm | 57,096 | 72,354 |
| hierarchy_exclusions_off / shipped keep-members=False arm | 52,703 | 38,993 |
| capped `Mapper._spatial_situation` | 3,950 | 194 |

- Degree-zero window nodes: **30,765 / 57,096 = 53.8829%**.
- Default hierarchy deletion from window: **4,393 nodes**, **33,361 edges**.
- Spatial nodes per frame: **50** by cap; spatial edges total **194**.
- Junction kinds: **Corner 153, Junction 99, T 31, Y 3**.
- Junction topologies: `{0:44, 1:153, 2:31, 3:3, 4:2, 6:53}`.

Selected lens window→spatial counts:

| lens | window | spatial | note |
|---|---:|---:|---|
| Orientation | 4,141 | 79 | one per frame floor reserve |
| Position | 7,433 | 79 | one per frame floor reserve |
| CONTOUR_PEAK | 8,169 | 79 | one per frame floor reserve |
| Color | 2,950 | 79 | one per frame floor reserve |
| BorderOwnership | 5,863 | 2,399 | densest remaining seats |
| Boundary | 5,787 | 156 | |
| Junction | 98 | 54 | residual kind |
| T | 31 | 24 | |
| Y | 3 | 3 | |
| IllusoryContour | 125 | 50 | |

Selected edge-family window→spatial survival:

| family | window | spatial | survival |
|---|---:|---:|---:|
| JUNCTION_CONTOUR | 5,508 | 86 | 1.5614% |
| BORDER_OWNERSHIP_EDGE | 391 | 52 | 13.2992% |
| REGION_CONTENT | 11,494 | 15 | 0.1305% |
| CO_LOCATED | 17,404 | 14 | 0.0804% |
| CONTOUR_ORIENTATION | 10,305 | 12 | 0.1164% |
| CURVE_CONTAINMENT | 1,090 | 6 | 0.5505% |
| JUNCTION_ORIENTATION | 736 | 6 | 0.8152% |
| LINE_TERMINATION | 208 | 3 | 1.4423% |
| ORIENTATION_CONTINUITY | 4,093 | 0 | 0% |
| ORIENTATION_BEND | 2,288 | 0 | 0% |
| ORIENTATION_JUNCTION | 1,536 | 0 | 0% |
| CONTOUR_CONTINUITY | 2,799 | 0 | 0% |
| CURVATURE_SIGN_CONTINUITY | 2,496 | 0 | 0% |
| RADIALITY | 1,691 | 0 | 0% |
| COCIRCULAR | 921 | 0 | 0% |

All other 18 window families also have **0** spatial survivors. Full table: `phase3/results/native-flow.json`.

### 4.2 Entropy, presence, degenerate slots

Corpus: `ETH80_REF4_plus_EVAL75_native256`. Full table: `phase3/results/entropy-presence.json`.

Population-presence pattern (per-axis boolean tuple) is constant within every lens/class group: **1 distinct pattern, H = 0.000000 bits** for all 24 groups. All-present groups include Contour, ContourFragment, Corner, Junction/T/Y, Polarity, RegionShape, BorderOwnership, CONTOUR_PEAK, TextureBoundary. All-absent groups include Boundary, Color, Texture, Onset, Orientation, Position.

Key ABSENT/CONSTANT slots:

| lens | class | slot | status | value / count |
|---|---|---|---|---|
| Position | POSITION | `dz` | **ABSENT** | UNKNOWN 7,436/7,436; H=None |
| Onset | ONSET | `recency` | CONSTANT | 0.0 over 2,210 detections |
| CurveComplex | CURVE_COMPLEX | `n_contours` | CONSTANT | 1.0 |
| CurveComplex | CURVE_COMPLEX | `n_junctions` | CONSTANT | 0.0 |
| Contour | CONTOUR | `corner_count` | CONSTANT | 0.0 |
| PEAK_CHAIN | PEAK_CHAIN | `closure` | CONSTANT | 0.0 |
| RegionShape | REGION_SHAPE | `area` | CONSTANT | 0.0 |
| Surface | SURFACE_PATCH | `grad_mag`, `grad_side`, `shape` | CONSTANT | 0.0 |
| Junction | JUNCTION | `arm_sharp_mean` | CONSTANT | 7.0 |
| Junction | JUNCTION | `arm_angle0/1/3/5` | CONSTANT | 0.0 |
| Corner | JUNCTION | `degree`, `topo` | CONSTANT | 2.0, 1.0 |
| T | JUNCTION | `degree`, `topo` | CONSTANT | 3.0, 2.0 |
| Y | JUNCTION | `degree`, `topo` | CONSTANT | 3.0, 3.0 |

Position `dx` entropy: **3.980041 bits**; `dy`: **3.969553 bits**; `dz`: **ABSENT**.

### 4.3 Joint MI with class label

Corpus: `ETH80_REF4_plus_EVAL75_native256`. Symbol = `(quantized tuple, per-axis population-presence pattern)`. Primary null: whole-image label permutation, seed 20261113, 1000 permutations. Secondary node-level null is anti-conservative and labeled as such. Full table: `phase3/results/mi-class.json`.

Significant under **both** nulls (p<0.05):

| lens | class | MI bits | image p | node p |
|---|---|---:|---:|---:|
| TextureBoundary | TEXTURE_BOUNDARY | 1.322794 | 0.000999 | 0.000999 |
| Surface | SURFACE_PATCH | 1.254376 | 0.000999 | 0.000999 |
| ContourFragment | CONTOUR_FRAGMENT | 1.222483 | 0.000999 | 0.000999 |
| Orientation | ORIENTATION | 0.952482 | 0.000999 | 0.000999 |
| CONTOUR_PEAK | CONTOUR_PEAK | 0.889027 | 0.000999 | 0.000999 |
| Color | COLOR_LEGACY | 0.600718 | 0.000999 | 0.000999 |
| BorderOwnership | BORDER_OWNERSHIP | 0.216391 | 0.000999 | 0.004995 |
| Boundary | BOUNDARY_ANCHORED | 0.211329 | 0.000999 | 0.000999 |
| Texture | TEXTURE | 0.143572 | 0.000999 | 0.000999 |

Significant under **image-level only**:

| lens | class | MI bits | image p | node p |
|---|---|---:|---:|---:|
| Contour | CONTOUR | 0.911912 | 0.002997 | 0.053946 |
| CurveComplex | CURVE_COMPLEX | 0.888784 | 0.038961 | 0.369630 |
| EndStopped | ENDSTOPPED | 0.183656 | 0.006993 | 0.940060 |
| Position | POSITION | 0.059136 | 0.000999 | 0.985015 |

Neither null significant: Corner/CORNER, Corner/JUNCTION, IllusoryContour, Junction/JUNCTION, Onset, Orientation_SEGMENT, PEAK_CHAIN, Polarity, RegionShape, T, Y. Onset and Polarity have MI=0 despite Polarity having 3 values, because the value is constant per image in this corpus.

### 4.4 Filter / template — both median arms

Corpus: `ETH80_REF4_plus_EVAL75_native256`; four class-level templates (A0). Full table: `phase3/results/filter-template.json`.

| class | median arm | pos/neg | Wilson min count | min freq | template nodes | template edges | template degree-zero share | attribute mass share | core nodes before→after | core edges before→after |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| apple | OFF | 17/62 | 3 | 0.176471 | 12 | 0 | 1.000000 | 0.432339 | 12→3 | 0→0 |
| car | OFF | 25/54 | 3 | 0.120000 | 10 | 0 | 1.000000 | 0.522265 | 10→0 | 0→0 |
| cup | OFF | 19/60 | 3 | 0.157895 | 12 | 0 | 1.000000 | 0.505753 | 11→2 | 0→0 |
| horse | OFF | 18/61 | 3 | 0.166667 | 13 | 0 | 1.000000 | 0.417280 | 13→1 | 0→0 |
| apple | ON | 17/62 | 3 | 0.176471 | 13 | 2 | 0.769231 | 0.374769 | 13→3 | 2→0 |
| car | ON | 25/54 | 3 | 0.120000 | 14 | 1 | 0.857143 | 0.350629 | 13→0 | 0→0 |
| cup | ON | 19/60 | 3 | 0.157895 | 13 | 1 | 0.846154 | 0.411264 | 10→2 | 0→0 |
| horse | ON | 18/61 | 3 | 0.166667 | 13 | 1 | 0.846154 | 0.409856 | 13→1 | 1→0 |

`core_edges_after = 0` in **all 8 rows**. Materialization uses the lowest-WL-hash exemplar regardless of the median flag; the median flag affects `structural_intersection`’s internal exemplar choice.

### 4.5 Distance spans outside declared schema range

Corpus: `ETH80_REF4_plus_EVAL75_native256`; continuous writer arguments intercepted without changing return values. Full table: `phase3/results/distance-spans.json`.

| edge class | slot | unit | n | declared span | outside | outside share | median | max |
|---|---|---|---:|---|---:|---:|---:|---:|
| EDGE_ORIENTATION_BEND | spatial_dist | wavelengths | 34,693 | [0,1] | 34,693 | 100% | 8.838835 | 22.114758 |
| EDGE_ORIENTATION_JUNCTION | spatial_dist | wavelengths | 39,227 | [0,1] | 39,227 | 100% | 9.013878 | 22.534695 |
| EDGE_CONTOUR_CONTINUITY | dist | wavelengths | 15,325 | [0,2] | 14,437 | 94.2055% | 8.273876 | 20.025765 |
| EDGE_CONTACT | dist | median_spacings | 592 | [0,1] | 549 | 92.7365% | 2.705494 | 6.674637 |
| EDGE_JUNCTION_CONTOUR | dist | wavelengths | 5,634 | [0,2.5] | 4,975 | 88.3032% | 7.267520 | 19.031452 |
| EDGE_CONCENTRICITY | offset | fraction | 545 | [0,1] | 325 | 59.6330% | 1.060660 | 1.494036 |

All other registered writer slots measured: **0% outside** their declared span.

### 4.6 Border margins

Rule: actual nonzero Gabor kernel support → half-support → shipped interior cap. Full table: `phase3/results/margins.json`.

| size | front-end scale | kernel full size | channel half-supports | capped channel margins | single margin | zones |
|---:|---:|---:|---|---|---:|---:|
| 256 | 1.000000 | 113 | [56,37,24,15,10] | [56,37,24,16,16] | 56 px | 4 |
| 96 | 0.375000 | 43 | [21,14,9,6,4] | [21,16,16,16,16] | 21 px | 2 |

### 4.7 Perturbation and controls

Translation corpus: `ETH80_EVAL75_96` — first two eval images per class, 8 images, 96×96. Full tables: `phase3/results/perturbation-summary.json`, `phase3/results/perturbation-stability.json`.

| arm | translations | fragment matches | signatures changed | drift median-of-medians | drift max | topological identity same | graded bins same |
|---|---:|---:|---:|---:|---:|---|---|
| ±2 px | 32 | 536 | 319 | 2.0 px | 96.462428 px | 4,314/4,587 = 94.0484% | 3,216/4,587 = 70.1112% |
| ±3 px | 32 | 584 | 332 | 1.0 px | 102.303470 px | 3,531/3,744 = 94.3109% | 2,645/3,744 = 70.6464% |

Occlusion fixture (`SYNTHETIC_CONTROLS`, nonconvex polygon, central 20% width removed):

- contours: **18 → 19**
- fragments: **16 → 22**
- matched fragments: **7**, all **7** signature-changed
- drift: median **34.205263 px**, max **58.137767 px**
- window nodes: **372 → 460**; edges: **563 → 733**

Controls (`SYNTHETIC_CONTROLS`):

| control | regions | below roughness gate | Orientation raw | bound | window | nodes | edges | largest component | isotropy↔elongation r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat_grey_96 | 256 | 256 | 0 | 0 | 0 | 117 | 35 | 21 | 1.000000 |
| flat_white_96 | 256 | 256 | 0 | 0 | 0 | 121 | 43 | 25 | 1.000000 |
| noise_96 | 309 | 23 | 41 | 41 | 41 | 894 | 679 | 174 | 0.990685 |
| flat_grey_256 | 256 | 256 | 0 | 0 | 0 | 139 | 36 | 27 | 1.000000 |

### 4.8 Junction views

Corpus: `ETH80_OBJECT1_96` — apple object-1, exactly 41 unique view PNGs, 96×96. Full table: `phase3/results/junction-views.json`.

- views: **41**
- total junctions: **55**
- kinds: **Corner 39, Junction 13, T 3**; kind entropy **1.072427 bits**
- topologies: `{0:3, 1:39, 2:3, 6:10}`; topology entropy **1.256637 bits**
- views with zero junctions: **8**
- Y, Arrow, L: **0** in this object probe.

### 4.9 Position / anchor ablation

Corpus: `SYNTHETIC_NINE` — 17 scenes, 9 registered pairs. Scope: `hierarchy_exclusions_off` (shipped keep-members=False arm), **not** the capped Mapper spatial situation. Metric: `mcs_score` correspondence/score, not renderer-truth P/R/F1. Full table: `phase3/results/position-pairs.json`.

| quantity | value |
|---|---:|
| unique scenes | 17 |
| unique Position nodes across scenes | 1,603 |
| candidate Position pairs | 80,089 |
| pooled Pearson r(signature similarity, anchor factor) | **0.930512** |
| per-pair r range | 0.929899 – 0.931802 |
| baseline mapped | 3,775 |
| baseline non-Position mapped | 2,929 |
| baseline Position mapped | 846 |
| no-Position mapped | 2,929 |
| non-Position pairs changed by Position removal | **0** |
| Position pairs removed by Position removal | **846** |
| no-anchor mapped | 3,775 |
| non-Position pairs changed by anchor removal | **1,334** |
| Position pairs changed by anchor removal | **16** |
| total anchor-removal pair memberships changed | **1,350** (675 removed + 675 added) |
| no-Position score delta range | −0.060126 … +0.002678 |
| no-anchor score delta range | −0.058886 … +0.082447 |

Interpretation: Position signature removal leaves every non-Position correspondence unchanged in this scope, but deletes the Position correspondences themselves. Anchor removal preserves the mapped count while swapping 675 partners. The historical r=0.8403 / 0-of-4,089 / 828 numbers are not reproduced and remain UNKNOWN / CORPUS MISSING.

## 5. Inherited phase2 claims — disposition

| inherited claim | disposition |
|---|---|
| D7 absent voters, B7 incomparable skip, B3 raw/capped pin, P0 flag shape, D5 median flag, frame partition registration | **CONTRACT CONFIRMED** by 38 pins and 510 matcher tests. No accuracy gain claimed. |
| Nine-pair truth P .967/R .696/F1 .802; all flag arms P .640/R .688/F1 .662, mapped 159.2 | **UNKNOWN / CORPUS MISSING** as a Phase-0 measurement. The synthetic scenes were recovered, but the historical renderer-truth role-metric arm harness was not re-run; these numbers are inherited only. |
| Four-frame spine census: 3,017→740, hierarchy deletes 0/740, Orientation 180→0, ORIENTATION_CONTINUITY 178→1 | **UNKNOWN / CORPUS MISSING**. Current 79-frame native census is a different corpus/scope and is reported separately. |
| Historical Position confirmation: 1,653 nodes, z=[8.0], r=0.8403, 0/4,089, 828 | **UNKNOWN / CORPUS MISSING**. Current synthetic-nine and native256 measurements are reported separately. |
| Handoff test counts 36/568, reference 576 | **LABEL ONLY, NOT RECONCILED**. Current guarded runs: 38 pins passed, 510 matcher passed. |

## 6. Stop condition

Phase 0 measurement and report are complete. The next action is the user’s decision. No front-end code, patch series, flag selection, or phase2 amendment beyond the recorded syntax-only import repair has been produced in this phase.
