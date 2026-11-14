"""Render the finished-build result tables from completed measurements."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT
import json


def main():
    census=json.loads((ROOT/'phase3/results/build-census-seed0.json').read_text())
    pairs=json.loads((ROOT/'phase3/results/build-pairs-seed0.json').read_text())
    det=json.loads((ROOT/'phase3/results/build-determinism.json').read_text())
    before=json.loads((ROOT/'phase3/results/native-flow.json').read_text())
    oldmi={(x['lens'],x['class']):x['joint_MI'] for x in json.loads((ROOT/'phase3/results/mi-class.json').read_text())}
    lines=['# Finished-build evaluation','',
      'Build: `percept5-frontend-build-v1`; protocol amendment in `audit/build-protocol.json`. First measurement seed 0; fresh-process repeat seed 1729. No tuning after measurement.',
      '', '## Scope and comparability','',
      'ETH80_ALL8 is 136 independent 256×256 frames (8 references, 128 object-disjoint evaluation frames; all eight classes). The historical Phase 0 baseline is ETH80_REF4_plus_EVAL75_native256 (79 frames, four classes), so before/after rates below are descriptive, **not paired causal comparisons**. RENDERER_TRUTH_V1 contains 15 independent 192×192 scenes and nine registered pairs; there is no comparable Phase 0 role-oracle result.',
      'The original wording “first two objects” conflicted with object-disjoint evaluation against reference object 1. Before measurement the manifest was corrected to objects 2 and 3; the amendment records this.',
      '', '## Frame and edge budgets','',
      '| Corpus | Before | After | Registered criterion |', '|---|---|---|---|']
    for name in ('ETH80_ALL8','RENDERER_TRUTH_V1'):
        c=census[name];q=c['frame_seconds'];e=c['edge_budget'];old='10.4 s/frame mean; 50-node historical cap' if name=='ETH80_ALL8' else 'not measured'
        lines.append(f'| {name} | {old} | {c["n_success"]}/{c["n_registered"]} frames; frame median {q["median"]:.3f} s, p95 {q["p95"]:.3f} s, max {q["max"]:.3f} s; selected edges/frame max {int(e["max"])} | frame p95 ≤30 s and max ≤60 s: **{"PASS" if c["runtime_pass"] else "FAIL"}**; edges ≤512: **{"PASS" if c["edge_budget_pass"] else "FAIL"}** |')
    lines += ['', 'The first 8 reference frames ran while a preliminary repeat/regression was briefly active; timings are wall-clock and include that contention. Match timing below was measured without the repeat running.', '', '## Edge-family survival','',
      'Selected counts divided by complete-window counts, aggregated per corpus. A zero caused by non-frame endpoints is reported explicitly; CO_LOCATED, CONTACT, PROXIMITY and SURFACE_GROUPING are excluded by design, with attributes carried as named features instead. The Phase 0 before arm is its capped spatial situation, not the new selected graph.', '',
      '| Edge family | Before: Phase 0 % | ETH80_ALL8 selected/window (%) | RENDERER_TRUTH_V1 selected/window (%) | Missing structural family reasons (ETH / renderer, frame counts) |', '|---|---:|---:|---:|---|']
    a=census['ETH80_ALL8']['family_survival'];b=census['RENDERER_TRUTH_V1']['family_survival'];old=before['family_spatial_survival']
    for name in sorted(set(a)|set(b)|set(old)):
        def cell(d):
            if name not in d:return '—'
            x=d[name];return f'{x["selected"]}/{x["window"]} ({100*x["fraction"]:.2f}%)' if x['fraction'] is not None else '—'
        bf=f'{old[name]*100:.2f}%' if name in old and old[name] is not None else '—'
        ra=a.get(name,{}).get('missing_reason_counts',{});rb=b.get(name,{}).get('missing_reason_counts',{})
        reason=', '.join(f'{k}: {ra.get(k,0)}/{rb.get(k,0)}' for k in sorted(set(ra)|set(rb))) or '—'
        lines.append(f'| {name} | {bf} | {cell(a)} | {cell(b)} | {reason} |')
    lines += ['', 'Criterion: every present structural family absent from the selected graph needs an explicit reason. **PASS for reason disclosure**, not a claim of preservation: the table shows families with zero selected edges. Excluded attribute relations are outside the structural-family coverage criterion.', '', '### Largest FRAME component', '']
    for name in ('ETH80_ALL8','RENDERER_TRUTH_V1'):
        c=census[name];allc=c['largest_frame_component_all'];struct=c['largest_frame_component_structural'];ratio=c['largest_component_structural_to_all']
        lines.append(f'- {name}: median largest component, all edges {allc["median"]:.1f}, structural edges {struct["median"]:.1f}; median per-frame structural/all ratio {ratio["median"]:.3f}. Before: not measured on this corpus/scope. Registered requirement is disclosure, not a numeric threshold: **PASS**.')
    lines += ['', '## Renderer nine pairs: role oracle versus bounded fuzzy solver','',
      'Before: no independently measured comparable role-oracle baseline. The truth denominator for each pair is Σ min(role counts) over roles `(object_id, lens_type, signature_class)`. The truth row uses that same denominator; when it is zero, recall and F1 are undefined. Coordinates missing from the pattern-node registry and background nodes have no object role. Predictions involving them remain in the precision denominator, so precision below is a conservative lower bound, not a measured exact precision. See per-pair role availability in `results/build-pairs-seed0.json`.', '',
      '| Pair | Truth TP / denominator; P / R / F1 | Returned solver TP / predicted / denominator; P / R / F1 | Objective truth / returned | Match seconds |', '|---|---|---|---:|---:|']
    def v(x): return '—' if x is None else f'{x:.3f}'
    for row in pairs['pairs']:
        if row['error']:
            lines.append(f'| {" / ".join(row["pair"])} | — | ERROR: {row["error"]} | — | — |');continue
        t=row['truth'];s=row['solver'];lines.append(f'| {" / ".join(row["pair"])} | {t["tp"]}/{t["truth_denominator"]}; {v(t["precision"])} / {v(t["recall"])} / {v(t["f1"])} | {s["tp"]}/{s["predicted"]}/{s["truth_denominator"]}; {v(s["precision"])} / {v(s["recall"])} / {v(s["f1"])} | {row["truth_objective"]["score"]:.6f} / {row["returned_solver_objective"]:.6f} | {row["match_seconds"]:.3f} |')
    m=pairs['micro'];q=pairs['match_seconds'];lines += ['',
      f'Micro: {m["tp"]}/{m["predicted"]}/{m["truth_denominator"]}; conservative P {m["precision"]:.3f}, R {m["recall"]:.3f}, F1 {m["f1"]:.3f}. Pair objective uses a deterministic canonical member of each role equivalence class; it is not a uniquely specified geometric ground-truth correspondence.',
      'The product fuzzy alignment is bounded and heuristic, so the returned objective is **not a certified global optimum**. A global-optimum criterion is therefore **not evaluated**; the truth-versus-returned measurements are shown without claiming proof.',
      f'Match timing before: unavailable. After: median {q["median"]:.3f} s, p95 {q["p95"]:.3f} s, max {q["max"]:.3f} s over {q["n"]} matches. Criterion p95 ≤1 s and max ≤3 s: **{"PASS" if pairs["runtime_pass"] else "FAIL"}**. No registered P/R/F1 threshold was specified; do not infer a pass from these low-precision results.', '',
      '## ETH80_ALL8 class information', '',
      'Joint symbol is `(quantized tuple, population-axis presence pattern)` on selected nodes, grouped by lens/class. Primary null permutes whole-image labels 999 times, seed 1729; 128 evaluation images, eight classes. Before values below come from the Phase 0 complete window, 79 frames/four classes and 1000 permutations, so they are not a matched comparison. No numeric MI pass threshold was registered.', '',
      '| Lens / class | Before MI bits (different corpus/scope) | After n | After MI bits | Image-level permutation p |', '|---|---:|---:|---:|---:|']
    for x in census['ETH80_ALL8']['class_mi']['groups']:
        z=x['joint_MI'];old=oldmi.get((x['lens'],x['class']));ov=v(old['observed_bits']) if old else '—'
        lines.append(f'| {x["lens"]} / {x["class"]} | {ov} | {z["n"]} | {z["observed_bits"]:.4f} | {z["p_one_sided"]:.3f} |')
    margin=json.loads((ROOT/'phase3/results/build-renderer-margin.json').read_text())
    failure=json.loads((ROOT/'phase3/results/build-filter-seed0.json').read_text())
    closure=json.loads((ROOT/'phase3/results/build-closure-seed0.json').read_text())['counts']
    lines += ['', '## Closure flags (partial scope)', '',
      'Before: Phase 0 PEAK_CHAIN closure was constantly zero on the historical four-class complete-window corpus. After: counts below are selected matcher-input pattern nodes, not the complete detection stream. Observation-contour flags were not recorded, so the full registered three-source closure criterion remains **NOT EVALUATED**.', '']
    for corp in sorted(closure):
        for cls in sorted(closure[corp]):
            item=closure[corp][cls]
            lines.append(f'- {corp} {cls}: {item.get("closed",0)}/{item["total"]} closed; {item.get("open",0)} open, {item.get("absent",0)} absent.')
    lines += ['', '## Renderer margin', '',
      'Before: unavailable on RENDERER_TRUTH_V1. After: using 4-neighbour visible-foreground perimeter sides, classified by their foreground pixel centre, the 192-pixel controls have a 42-pixel largest-kernel margin. Single box 0/360, single cylinder 0/324, single disk 0/416 sides outside; each has zero wholly discarded components. Centered-control criterion ≤10%: **PASS**. The fresh-process repeat JSON has the same SHA-256.', '',
      '## Eight-class filter and named pooling audit', '',
      f'Before: Phase 0 had zero post-filter edges in all eight arm/class rows, on a different four-class corpus. After: **FAIL / NOT EVALUABLE**: content pooling aborted at evaluation frame {failure["processed_frames"]+1}, `{failure["failed_frame"]}`, with `{failure["error"]}`. No class templates or positive/negative scores were produced; do not interpret this as a successful filter criterion. The fresh-process seed-1729 attempt failed at the same frame with the same error.',
      'Post-measurement diagnosis: the two feature bundles were unequal in full precision but identical after `serialize_value` rounded their floats to 1e-6; the feature-aware content-ID collision guard then rejected them. This is a product-path defect, not evidence that the filter passes. It is not patched or tuned after seeing the corpus results.', '',
      '## Determinism', '', f'Fresh process, hash seeds 0 and 1729: {det["frame_equal"]}/{det["frames_compared"]} canonical frame SHA-256s equal; census equal: {det.get("census_equal")}; pairs equal: {det.get("pairs_equal")}. Runtime and provenance timestamps excluded. **{"PASS" if det["passed"] else "FAIL"}** for these completed measurements. The filter failed identically in both processes. See `results/build-determinism.json` for each frame.', '',
       '## Singleton and explicit limits', '',
       'Off-correspondence null was registered before this measurement. Identical edgeless singleton: before chance 1.0 / score 0.0; after chance 0.0 / score 0.5. The 0.5 factor is the registered no-alternative finite-sample rule. The singleton and off-correspondence pins pass.',
       'The named ABSENT/pooling follow-up remains separate and does not gate these measurements. Other registered diagnostics not fully captured by this run (including observation-contour closure, leak-channel interventions, translation drift and retrieval-recall probes) are **not evaluated** here; do not treat the listed results as a complete pass of those criteria.']
    (ROOT/'phase3/BUILD_REPORT.md').write_text('\n'.join(lines)+'\n')
    print('wrote phase3/BUILD_REPORT.md')
if __name__=='__main__':main()
