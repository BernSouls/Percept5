# PHASE 2 — THE VERIFICATION OF THE INHERITED WORK, AND THE FIXES

**What the previous agent did correctly, what I fixed in it, and the
measurements that decide where the work goes next.** Written against the
overlay in `phase2/`; the original `src/` is never written to.

---

## 1. WHAT WAS DONE CORRECTLY (and is kept)

| the work | the verdict | the evidence |
|---|---|---|
| **D7 — the consensus's absent voters** | **CORRECT, and it is exactly the fix I had worked out but not landed** | 2 of 5 matching voters now report the support **0.400 over 5 voters** (the historical 1.000 over 2). The weights are aligned to the exemplar index (the old code zipped the surviving values with the FIRST weights — the second half of the defect). |
| **B7 — the third state for an incomparable relation** | **CORRECT** | `polymorphic_edge_similarity(..., return_none=True)` returns `None` for a pair with no common ontology (the three stage-6 relations have no U30 equivalent), and the live path skips it. |
| **P0 — "the hierarchy step is inert"** | **CORRECT, and I CONFIRMED IT INDEPENDENTLY** | My own census (`diagnostics/phase2_spine_census.py`, four ETH-80 frames, the shipped pipeline): the hierarchy step deletes **0 of 740** situation-graph edges and **0** nodes. The edge loss (3 017 → 740) is UPSTREAM, in the situation graph's own construction. |
| **H1/H2 — the harness** | **CORRECT** | the collection errors are gone; the walker's `mp_context` import is real. |
| **the discipline** | **CORRECT and worth keeping** | no accuracy was claimed from a mechanism change; the P0 census was reported as "inert" rather than as a gain; the log names what was NOT landed. |

## 2. WHAT I FIXED IN IT (seven issues; each with its evidence)

### 2.1 NO FLAG-GATING — the largest defect

Six mechanisms changed the shipped behaviour the moment the overlay was
loaded. The project's rule is explicit: **"every new default OFF until a
pre-registered rule selects it; the series must apply without changing
behaviour until a flag is set."** The P0 specification says the same thing
("Flag-gated, default = current until measured").

**FIXED:** every mechanism is now behind a new flag whose default is the
**historical** behaviour, so the overlay loads without changing a single
number and each fix is a measurement arm:

`MATCH_EDGE_MASS_CONTAINMENT` · `MATCH_SKIP_INCOMPARABLE_RELATIONS` ·
`MATCH_KEEP_HIERARCHY_MEMBERS` · `MATCH_TEMPLATE_MEDIAN_EXEMPLAR` ·
`MATCH_CONSENSUS_COUNT_ABSTENTIONS` — all `False`.

### 2.2 THE B3 PIN RE-BASELINE DESTROYED THE PIN

The inherited pin asserted `c_matched_em == 2.0` with the flag counted as a
measured axis and `== 1.0` without it. **The pin's name says "the edge mass
of a flag LOSES ITS FACILITATION" — the two branches ARE the test.** The
cap made BOTH branches 1.0: the pin became vacuous, and the facilitation's
signal was silently discarded.

**FIXED:** the RAW (uncapped) mass is kept in the trace
(`q_matched_em_raw` / `c_matched_em_raw`), so the pin keeps its
discriminating power (2.0 against 1.0) **and** the containment is asserted
separately (`c_matched_em <= c_edge_total`).

### 2.3 B7b WAS A DEFAULT FLIP

`EVIDENCE_RELATION_COUNT_APART` was flipped `False → True` and the
declared-defaults pin was re-baselined to match. A default is not a bug
fix: it changes every score in the tree, and the flip was made with **no
measurement** of what it does.

**FIXED:** the default is **not** flipped. The mechanism already exists in
the tree and is read with `getattr` at every use, so it is measured as an
**arm** (the flag set at run time) rather than shipped as a default. The
declared-defaults pin is untouched.

### 2.4 THE FRAME PIN WAS TOO WEAK — AND IT HIDED A REAL GAP

The inherited pin compared two HARDCODED literals (`V1_TIER`,
`HIGHER_TIER`) against the partition. Those literals did not even enumerate
the higher structural lenses the front end emits (CONTOUR_PEAK, PEAK_CHAIN,
ContourFragment, Corner, EndStopped, CurveComplex), so a new front-end lens
did **not** redden it.

**FIXED:** the pin reads the source of truth — the V1 names, the higher
names, and the `produces` field of every derived lens declaration. **And it
found a real gap:** four lens types are **DECLARED by the front end but in
NEITHER partition** — `Size`, `Motion`, `EffectPresent`, `OrientationPol` —
so each was "not frame" by the tree's own rule *and* unclassified by the
attribute set. A fifth, `Action` (a motor concept that leaks into the
pattern-node space), was in neither either.

**FIXED:** the four are registered as attributes (the choice and its reason
are recorded in the code and in the report below), and `Action` becomes an
explicit `NON_LENS_TYPES` member, so it can never enter a correspondence by
accident.

### 2.5 THE DELIVERABLE WAS NOT A PATCH SERIES

**FIXED:** an eight-patch series (`phase2/patches/`), each with the required
header (the claim IDs, the mechanism, the pre-registered constants, the
gating flag, the pin), and **mechanically verified**: the series is applied
to a scratch copy of the tree and the result must be **byte-identical** to
the overlay (`phase2/verify_patches.py`; there is no `git` binary on this
machine, so the applier implements `git apply -p1` semantics and a context
mismatch is an error, never a fuzzy match).

### 2.6 THE NINE-PAIR WALKER NEVER RAN

The inherited log was **25 MB of tracebacks**: `mp_context` was only
*Mentioned* in a `# noqa` comment and never imported, and the worker called
an undefined `_scene` (under the Windows `spawn` start method the child
re-imports the module, so the parent's `SCENES` dict is empty).

**FIXED in the source:** the import is real and the worker resolves the
scene itself. **The walker now runs and reproduces the baseline exactly:**
the walker P 0.633 / R 0.375, the incumbent P 0.641 / R 0.690 — the same
numbers the earlier sessions recorded. The primary measurement instrument of
the whole project was dead, and it is alive.

### 2.7 TWO SMALLER DEFECTS

* the inherited P0 check called `_apply_hierarchy_exclusions(None, sg)` —
  `None` has no `_part_exclusions`, so the check raised an
  `AttributeError` instead of testing anything (fixed with a stand-in
  object, in the check and in the pin);
* **a determinism bug in my own B7 code**, caught before it shipped: it
  `sorted()` a set of edge keys, and a key carries an `EdgeType`, whose
  order is hash-dependent — the tree's rule forbids exactly this. The sum
  is now `math.fsum` over an unsorted list (exactly rounded, therefore
  order-independent).

---

## 3. THE MEASUREMENTS (precision first; the truth's row carried)

### 3.1 THE NINE REGISTERED PAIRS — EVERY ARM IS THE BASELINE

`diagnostics/phase2_nine_pair_arms.py` (the overlay is asserted to be the
loaded tree):

| the arm | P | R | F1 | mapped | rel/match |
|---|---|---|---|---|---|
| **the renderer truth's own mapping** | **0.967** | **0.696** | **0.802** | 92.4 | — |
| the baseline (every flag OFF) | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B3 the containment | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B7 the incomparable skip | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B7b identity-only is presence | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| B3 + B7 + B7b | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |
| P0 keep the member | 0.640 | 0.688 | 0.662 | 159.2 | 1.27 |

**THE HEADLINE: NONE of the inherited fixes changes a single number on the
registered corpus.** The cap never binds there (the edges carry flags, so
f(0) = 1 and there is no facilitation to overflow); there is no
cross-ontology edge pair in it; the hierarchy step is inert on it.

**They are contract corrections — correct, pinned, and inconsequential.**
Reporting them as gains would be false.

### 3.2 THE REAL P0 TARGET: THE FRONT END, NOT THE HIERARCHY

`diagnostics/phase2_spine_census.py` — four ETH-80 frames, the shipped
pipeline:

* the physical pattern-pattern edges: **3 017** → the situation graph:
  **740** (24.5 %);
* **the hierarchy step deletes 0 of them** (and 0 nodes);
* per family, the STRUCTURAL spine survives
  (CONTOUR_CONTINUITY 93.5 %, JUNCTION_CONTOUR 92.2 %,
  CURVATURE_SIGN_CONTINUITY 95.6 %, RADIALITY 95.3 %, COCIRCULAR 97.9 %),
  while the **ORIENTATION family is nearly absent**
  (ORIENTATION_CONTINUITY 178 → **1**, ORIENTATION_BEND 66 → **0**,
  ORIENTATION_JUNCTION 54 → **0**) and the proximity/attribute families are
  decimated (CO_LOCATED 737 → 42, REGION_CONTENT 469 → 39).

**THE FRONT END PRODUCES 180 ORIENTATION NODES AND NONE REACH THE MATCHER**
(`diagnostics/phase2_emission_census.py`: Orientation 180 in the graph, **0**
in the situation graph). **That is the P1 target** — not the hierarchy step,
and not the matcher.

### 3.3 THE POSITION RULING — THE CONFIRMATION NUMBERS

`diagnostics/phase2_position_confirmation.py` (the nine registered pairs):

* **the depth slot:** 1 653 POSITION nodes over 17 scenes; the distinct
  emitted z-bin values: **[8.0]**; the entropy **0.0000 bits**. A constant
  slot emitted as if measured is a **fabricated measurement**: the ruling
  (depth on 2D input is ABSENT, never 0) applies and is not optional.
* **the duplication:** the Pearson correlation between the Position
  *signature* similarity and the *anchor* factor over 85 075 candidate pairs
  is **0.8403**; the two factors pick the same best partner for **824 of
  875** nodes (94.2 %).
* **the ablation:** removing the Position signature from the correspondence
  changes **0 of 4 089** mapped pairs and moves nothing (P 0.640 / R 0.688 /
  F1 0.662, unchanged); removing the **anchor** changes **828 of 4 089** and
  costs P 0.043 / R 0.048 / F1 0.045.

**THE VERDICT: the Position signature is a pure DOUBLE COUNT of the anchor's
information.** The ruling is confirmed by measurement: retinotopic position
stays in the anchor, and the Position signature is demoted.

---

## 4. THE RANKED LIST OF WHAT IS GENUINELY MISSING

1. **The ORIENTATION spine never reaches the matcher** (180 nodes produced,
   0 in the situation graph; ORIENTATION_CONTINUITY 178 → 1). The front end
   builds the orientation and the situation graph drops it. **P1's
   Orientation mandate is therefore a FRONT-END problem, and it is the
   largest single gap measured.**
2. **The depth slot is fabricated** (a constant bin, 0.0000 bits of
   entropy). The Position ruling (ABSENT, never 0) is confirmed and cheap.
3. **The Position signature double-counts the anchor** (r = 0.8403; 0 of
   4 089 mapped pairs change when it is removed). Demoting it is a
   simplification, not a gain — and it is now measurable.
4. **Four declared lens types are unclassified** (now registered) and the
   attribute families are decimated upstream (CO_LOCATED 5.7 %,
   REGION_CONTENT 8.3 %, CONTOUR_ORIENTATION 5.6 %).
5. **The matcher still reads the attribute nodes as identity votes** (the
   frame restriction exists only in the walker and in the dark graded
   solver; the live `evidence_score` path never calls `is_frame`).
6. **No explicit junction primitive at the floor** (P2): the V2 topology
   descriptor exists (arity 19) but there is no T/Y/Arrow/L node class, and
   the T and Y aliases in the frame partition have no emitter here.
7. **The additive relational objective is INVERTED** (the stage-10
   measurement: the objective's own proven optimum is a worse
   correspondence than the renderer truth's). The alphabet work does not
   touch that, and it does not have to: a richer alphabet changes the
   objective's numbers, and the inversion test must be re-run with it.

## 5. THE SENTENCE

**After the inherited fixes (corrected, flag-gated and pinned) the matcher
reads the alphabet exactly as before — the nine-pair arms are identical to
the baseline (P 0.640 / R 0.688 / F1 0.662 against the truth's 0.967 / 0.696
/ 0.802) — because the alphabet's orientation spine never reaches it (180
Orientation nodes produced, 0 matched) and its depth slot is a constant
(0.0000 bits).**
