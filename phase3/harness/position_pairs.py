"""Position signature/anchor duplication probe on the nine registered synthetic pairs."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import json, math, time
from dataclasses import replace
from collections import defaultdict
import numpy as np
from phase3.harness.frontend import run_frame
from phase3.harness.metrics import correlation, jaccard

P = load("parameters")
MC = load("memory.cores")
GT = load("core.graph_types")
CO = load("consolidator")
H = load("core.hashing")

PAIRS = (("box_over_box", "box_over_box_test"), ("box_over_box", "box_over_box_haze"),
         ("cylinder_over_box", "cylinder_over_box_shift"), ("f_box_a", "f_box_b"),
         ("f_haze_a", "f_haze_b"), ("f_disk_a", "f_disk_b"), ("f_cyl_a", "f_cyl_b"),
         ("single_disk", "f_ctrl_disk"), ("single_box", "f_ctrl_box"))


def scenes():
    import sys
    sys.path.insert(0, str(ROOT/"tests/figground"))
    from scenes import build_all
    from fresh_scenes import build_fresh_all
    out = dict(build_all())
    out.update(build_fresh_all())
    return out


def remove_lens(sg, sigs, lens):
    nodes = frozenset(n for n in sg.nodes if sigs.get(n, ("", None))[0] != lens)
    edges = frozenset(e for e in sg.edges if e[0] in nodes and e[1] in nodes)
    return GT.Subgraph(nodes=nodes, edges=edges,
                       edge_params={e: p for e, p in sg.edge_params.items() if e in edges},
                       anchor_of_node={n: p for n, p in sg.anchor_of_node.items() if n in nodes},
                       node_weights={n: w for n, w in sg.node_weights.items() if n in nodes},
                       weights={e: w for e, w in sg.weights.items() if e in edges})


def score(q, c, qs, cs):
    tr = {}
    s, corr = MC.mcs_score(q, c, qs, cs, trace=tr)
    return {"score": float(s), "mapped": len(corr),
            "pairs": sorted((int(a), int(b)) for a, b in corr.items())}


def main():
    sc = scenes()
    needed = sorted({n for p in PAIRS for n in p})
    built = {}
    for name in needed:
        t = time.monotonic()
        rgb = np.asarray(sc[name].rgb, dtype=np.float32)
        r = run_frame(rgb, name)
        # Keep only the matcher input and signatures; discard the observation,
        # concept graph and lens objects so 18 scenes do not accumulate in RAM.
        built[name] = (r.hierarchy_off, r.signatures)
        print("built", name, len(r.window.nodes), len(r.window.edges), time.monotonic()-t, flush=True)
        del r
        import gc
        gc.collect()
    rows = []
    all_sims, all_anchors = [], []
    for a, b in PAIRS:
        qa, sa = built[a]
        cb, sb = built[b]
        pos_a = [n for n in sorted(qa.nodes) if sa.get(n, ("",))[0] == "Position"]
        pos_b = [n for n in sorted(cb.nodes) if sb.get(n, ("",))[0] == "Position"]
        na, nb = MC._normalised_anchors(qa), MC._normalised_anchors(cb)
        sims, anch = [], []
        for u in pos_a:
            for v in pos_b:
                s = MC._sig_similarity(sa[u][1], sb[v][1])
                if na is None or nb is None or u not in na or v not in nb:
                    f = 1.0
                else:
                    f = math.exp(-2.5 * math.hypot(na[u][0]-nb[v][0], na[u][1]-nb[v][1]))
                sims.append(s)
                anch.append(f)
        all_sims.extend(sims)
        all_anchors.extend(anch)
        base = score(qa, cb, sa, sb)
        no_pos = score(remove_lens(qa, sa, "Position"), remove_lens(cb, sb, "Position"), sa, sb)
        no_anchor = score(replace(qa, anchor_of_node={}), replace(cb, anchor_of_node={}), sa, sb)
        no_both = score(remove_lens(replace(qa, anchor_of_node={}), sa, "Position"),
                        remove_lens(replace(cb, anchor_of_node={}), sb, "Position"), sa, sb)
        def cmp(arm):
            bp = set(map(tuple, base["pairs"]))
            ap = set(map(tuple, arm["pairs"]))
            # no-position arms live in same node ids; anchor arms too.
            return {"mapped": arm["mapped"], "score": arm["score"],
                    "score_delta": arm["score"] - base["score"],
                    "pair_jaccard": jaccard(bp, ap),
                    "pairs_removed": len(bp - ap), "pairs_added": len(ap - bp)}
        bp = {tuple(x) for x in base["pairs"]}
        np_ = {tuple(x) for x in no_pos["pairs"]}
        pa, pb = set(pos_a), set(pos_b)
        nonpos_base = {x for x in bp if x[0] not in pa and x[1] not in pb}
        pos_base = bp - nonpos_base
        na_pairs = {tuple(x) for x in no_anchor["pairs"]}
        rows.append({"pair": [a, b], "position_nodes_q": len(pos_a), "position_nodes_c": len(pos_b),
                     "candidate_position_pairs": len(sims),
                     "pearson_sig_vs_anchor": correlation(sims, anch),
                     "baseline": base, "no_position_signature": cmp(no_pos),
                     "no_anchor": cmp(no_anchor), "no_both": cmp(no_both),
                     "baseline_position_mapped": len(pos_base),
                     "baseline_nonposition_mapped": len(nonpos_base),
                     "nonposition_pairs_changed_by_position_removal": len(nonpos_base ^ np_),
                     "position_pairs_removed_by_position_removal": len(pos_base - np_),
                     "nonposition_pairs_changed_by_anchor_removal": len(nonpos_base ^ {x for x in na_pairs if x[0] not in pa and x[1] not in pb}),
                     "position_pairs_changed_by_anchor_removal": len(pos_base ^ (na_pairs - {x for x in na_pairs if x[0] not in pa and x[1] not in pb}))})
        print("pair", a, b, rows[-1]["pearson_sig_vs_anchor"], flush=True)
    summary = {"corpus": "SYNTHETIC_NINE", "scope": "hierarchy_exclusions_off (MATCH_KEEP_HIERARCHY_MEMBERS=False arm; not the capped Mapper spatial_situation)",
               "pairs": rows, "pooled_candidate_pairs": len(all_sims),
               "pooled_pearson_sig_vs_anchor": correlation(all_sims, all_anchors),
               "total_baseline_mapped": sum(r["baseline"]["mapped"] for r in rows),
               "total_no_position_mapped": sum(r["no_position_signature"]["mapped"] for r in rows),
               "total_no_anchor_mapped": sum(r["no_anchor"]["mapped"] for r in rows),
               "total_baseline_position_mapped": sum(r["baseline_position_mapped"] for r in rows),
               "total_baseline_nonposition_mapped": sum(r["baseline_nonposition_mapped"] for r in rows),
               "total_nonposition_pairs_changed_by_position_removal": sum(r["nonposition_pairs_changed_by_position_removal"] for r in rows),
               "total_position_pairs_removed_by_position_removal": sum(r["position_pairs_removed_by_position_removal"] for r in rows),
               "total_nonposition_pairs_changed_by_anchor_removal": sum(r["nonposition_pairs_changed_by_anchor_removal"] for r in rows),
               "total_position_pairs_changed_by_anchor_removal": sum(r["position_pairs_changed_by_anchor_removal"] for r in rows)}
    write_json(ROOT/"phase3/results/position-pairs.json", summary)
    write_json(ROOT/"phase3/audit/position-pairs-provenance.json", provenance("phase3/harness/position_pairs.py", ["memory.cores", "phase3.harness.frontend"]))
    print("DONE", summary["pooled_pearson_sig_vs_anchor"], flush=True)

if __name__ == "__main__":
    main()
