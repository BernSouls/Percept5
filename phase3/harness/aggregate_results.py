"""Deterministic Phase-0 result aggregation. Reads cached measurements only."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import glob
import json
from collections import Counter

RF = load("matching.relation_frame")
SC = load("core.schema")


def native_flow():
    C = Counter()
    fam_w, fam_s = Counter(), Counter()
    lens_w, lens_s = Counter(), Counter()
    deleted_edges, deleted_nodes = Counter(), Counter()
    unregistered = 0
    for p in sorted(glob.glob(str(ROOT / ".cache/phase0/native-census/*.json"))):
        with open(p) as fh:
            f = json.load(fh)
        if f.get("protocol_id") != "percept5-phase0-independent-v1":
            continue
        for k in ("window_nodes", "window_edges", "spatial_nodes", "spatial_edges",
                  "hierarchy_off_nodes", "hierarchy_off_edges",
                  "hierarchy_on_nodes", "hierarchy_on_edges", "degree_zero_nodes"):
            C[k] += f[k]
        fam_w.update(f["edge_families"])
        fam_s.update(e[2] for e in f["scopes"]["spatial_situation"]["edges"])
        spatial_ids = set(f["scopes"]["spatial_situation"]["nodes"])
        # Cached scope names are flag arms: hierarchy_exclusions_off means
        # MATCH_KEEP_HIERARCHY_MEMBERS=False (the shipped default, exclusions
        # ACTIVE); hierarchy_exclusions_on means keep-members=True.
        off = {tuple(e) for e in f["scopes"]["hierarchy_exclusions_off"]["edges"]}
        on = {tuple(e) for e in f["scopes"]["hierarchy_exclusions_on"]["edges"]}
        deleted_edges.update(e[2] for e in on - off)
        offn = set(f["scopes"]["hierarchy_exclusions_off"]["nodes"])
        onn = set(f["scopes"]["hierarchy_exclusions_on"]["nodes"])
        deleted_nodes.update(n["lens"] for n in f["node_records"] if n["id"] in onn - offn)
        for n in f["node_records"]:
            lens_w[n["lens"]] += 1
            if n["id"] in spatial_ids:
                lens_s[n["lens"]] += 1
        unregistered += f["unregistered_nodes"]
    attr_w = sum(v for k, v in lens_w.items() if k in RF.ATTRIBUTE_LENS_TYPES)
    attr_s = sum(v for k, v in lens_s.items() if k in RF.ATTRIBUTE_LENS_TYPES)
    frame_w = sum(v for k, v in lens_w.items() if RF.is_frame(k))
    frame_s = sum(v for k, v in lens_s.items() if RF.is_frame(k))
    return {
        "corpus": "ETH80_REF4_plus_EVAL75_native256",
        "totals": dict(sorted(C.items())),
        "scope_note": ("window == keep-members=True arm; shipped default "
                       "MATCH_KEEP_HIERARCHY_MEMBERS=False is the cached "
                       "hierarchy_exclusions_off arm (exclusions active); "
                       "spatial_situation is the separate capped Mapper graph"),
        "default_hierarchy_deleted_nodes": C["window_nodes"] - C["hierarchy_off_nodes"],
        "default_hierarchy_deleted_edges": C["window_edges"] - C["hierarchy_off_edges"],
        "default_hierarchy_deleted_nodes_by_lens": dict(sorted(deleted_nodes.items())),
        "default_hierarchy_deleted_edges_by_family": dict(sorted(deleted_edges.items())),
        "keep_member_added_nodes": C["hierarchy_on_nodes"] - C["hierarchy_off_nodes"],
        "keep_member_added_edges": C["hierarchy_on_edges"] - C["hierarchy_off_edges"],
        "unregistered_nodes": unregistered,
        "attribute_nodes_window": attr_w,
        "attribute_nodes_spatial": attr_s,
        "frame_nodes_window": frame_w,
        "frame_nodes_spatial": frame_s,
        "lens_window": dict(sorted(lens_w.items())),
        "lens_spatial": dict(sorted(lens_s.items())),
        "family_window": dict(sorted(fam_w.items())),
        "family_spatial": dict(sorted(fam_s.items())),
        "family_spatial_survival": {k: (fam_s[k] / fam_w[k] if fam_w[k] else None)
                                    for k in sorted(fam_w)},
    }


def perturbation_stability():
    with open(ROOT / "phase3/results/perturbation-summary.json") as fh:
        s = json.load(fh)
    out = {}
    for label, offsets in (("pm2", {(-2, 0), (2, 0), (0, -2), (0, 2)}),
                           ("pm3", {(-3, 0), (3, 0), (0, -3), (0, 3)})):
        topo_same = topo_n = geom_same = geom_n = 0
        frag_matches = frag_changed = 0
        medians, p95s, maxima = [], [], []
        ntrans = 0
        for r in s["translations"]:
            for t in r["translations"]:
                if (t["dx"], t["dy"]) not in offsets:
                    continue
                ntrans += 1
                topo_same += t["topological_identity_same"]
                topo_n += t["edge_matches"]
                geom_same += t["graded_bins_same_all_matched"]
                geom_n += t["edge_matches"]
                frag_matches += t["fragment_matches"]
                frag_changed += t["fragment_signature_changed"]
                d = t["fragment_drift_px"]
                if d["n"]:
                    medians.append(d["median"])
                    p95s.append(d["p95"])
                    maxima.append(d["max"])
        medians.sort(); p95s.sort(); maxima.sort()
        out[label] = {
            "translations": ntrans,
            "fragment_matches_total": frag_matches,
            "fragment_signature_changed_total": frag_changed,
            "drift_median_of_per_translation_medians_px": medians[len(medians)//2] if medians else None,
            "drift_max_over_all_matched_fragments_px": max(maxima) if maxima else None,
            "drift_largest_per_translation_p95_px": max(p95s) if p95s else None,
            "topological_identity_same": topo_same,
            "matched_edges": topo_n,
            "topological_identity_share": topo_same / topo_n if topo_n else None,
            "graded_bins_same": geom_same,
            "graded_bins_share": geom_same / geom_n if geom_n else None,
        }
    out["occlusion"] = s["occlusion"]
    out["controls"] = s["controls"]
    return out


def main():
    flow = native_flow()
    write_json(ROOT / "phase3/results/native-flow.json", flow)
    write_json(ROOT / "phase3/results/perturbation-stability.json", perturbation_stability())
    write_json(ROOT / "phase3/audit/aggregate-results-provenance.json",
               provenance("phase3/harness/aggregate_results.py", ["matching.relation_frame", "core.schema"]))
    print("DONE", flow["totals"]["window_edges"], flow["totals"]["spatial_edges"])


if __name__ == "__main__":
    main()
