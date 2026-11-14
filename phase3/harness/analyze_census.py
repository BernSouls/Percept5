"""Aggregate the independent native census: entropy, MI, filter, spans, margins."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import json, math
from collections import Counter, defaultdict
import numpy as np
from phase3.harness.metrics import entropy, quantiles, edge_sort, canonical_key

P = load("parameters")
SC = load("core.schema")
SL = load("core.slots")
RF = load("matching.relation_frame")
CT = load("core.types")
GT = load("core.graph_types")
CO = load("consolidator")
SS = load("matching.structural_similarity")
MC = load("memory.cores")
CONTENT = load("memory.content")
DIST = load("memory.distributions")
CF = load("perception.contour_field")
FL = load("perception.filters")


def load_frames():
    rows = []
    for p in sorted((ROOT/".cache/phase0/native-census").glob("*.json")):
        s = json.loads(p.read_text())
        if s.get("protocol_id") == "percept5-phase0-independent-v1":
            rows.append(s)
    return rows


def slot_names(cls, arity):
    try:
        names = list(SL.slot_names(cls) or ())
    except Exception:
        names = []
    if len(names) < arity:
        names += [f"slot{i}" for i in range(len(names), arity)]
    return names[:arity]


def entropy_report(frames):
    groups = defaultdict(list)
    node_groups = defaultdict(list)
    frame_names = defaultdict(set)
    for f in frames:
        for d0 in f["detections"]:
            # frontend.detection_record names the quantized tuple "slots";
            # node_records name it "bins". Normalize here, never guess arity.
            d = dict(d0, bins=d0["slots"])
            k = (d["lens"], d["class"], d["relation"])
            groups[k].append(d)
            frame_names[k].add(f["name"])
        for n in f["node_records"]:
            node_groups[(n["lens"], n["class"], n["relation"])].append(n)
    out = []
    for key, ds in sorted(groups.items()):
        lens, cls, rel = key
        arity = max(len(d["bins"]) for d in ds)
        names = slot_names(cls, arity)
        slots = []
        for i in range(arity):
            vals = [d["bins"][i] if i < len(d["bins"]) else None for d in ds]
            known = [v for v in vals if v is not None and v != SC.UNKNOWN]
            slots.append({"index": i, "name": names[i], "n": len(vals),
                          "unknown_or_missing": len(vals)-len(known),
                          "distinct_known": len(set(known)),
                          "entropy_known_bits": entropy(known),
                          "constant_known": len(set(known)) <= 1,
                          "values": dict(sorted(Counter(known).items())) if len(set(known)) <= 12 else None})
        pops = [bool(d["population"]) for d in ds]
        nodes = node_groups.get(key, [])
        out.append({"lens": lens, "class": cls, "relation": rel,
                    "detections": len(ds), "frames_present": len(frame_names[key]),
                    "joint_tuple_entropy_bits": entropy(tuple(d["bins"]) for d in ds),
                    "population_present": sum(pops), "population_present_share": sum(pops)/len(ds),
                    "population_presence_entropy_bits": entropy(pops),
                    "graph_nodes": len(nodes),
                    "graph_node_joint_entropy_bits": entropy(tuple(n["bins"]) for n in nodes),
                    "graph_node_population_present_share": (sum(bool(n["population"]) for n in nodes)/len(nodes)) if nodes else None,
                    "slots": slots})
    return out


def mi_image_level(values, node_frame, frame_labels, seed=20261113, perms=1000):
    n = len(values)
    if n == 0:
        return {"n": 0, "observed_bits": None, "p_one_sided": None}
    # Canonical typed encoding of each joint symbol: no repr(), no hash-order.
    # MI is invariant to how symbols are indexed, so this changes nothing numeric
    # versus a repr index -- it only removes the hash-seed/repr dependence.
    uniq = sorted({canonical_key(v) for v in values})
    code = {v: i for i, v in enumerate(uniq)}
    x = np.fromiter((code[canonical_key(v)] for v in values), dtype=np.int64, count=n)
    labels = sorted(set(frame_labels))
    lab_code = {l: i for i, l in enumerate(labels)}
    y = np.fromiter((lab_code[frame_labels[i]] for i in node_frame), dtype=np.int64, count=n)
    k = len(labels)
    V = len(uniq)
    def mi_joint(j):
        total = int(j.sum())
        if total == 0:
            return 0.0
        px = j.sum(axis=1)
        py = j.sum(axis=0)
        nz = j > 0
        denom = (px[:, None] * py[None, :])[nz]
        return float(np.sum(j[nz] / total * np.log2((j[nz] * total) / denom)))
    joint = np.bincount(x * k + y, minlength=V * k).reshape(V, k)
    obs = mi_joint(joint)
    frame_y = np.fromiter((lab_code[l] for l in frame_labels), dtype=np.int64, count=len(frame_labels))
    nf = np.fromiter(node_frame, dtype=np.int64, count=n)
    # PRIMARY null (pre-registered unit): permute WHOLE-IMAGE class labels,
    # keeping every image's node signatures together. Exchangeable units = the
    # images, so within-image clustering is respected. This is the headline p.
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(perms):
        yp = frame_y[rng.permutation(len(frame_labels))][nf]
        jp = np.bincount(x * k + yp, minlength=V * k).reshape(V, k)
        null.append(mi_joint(jp))
    exc = sum(v >= obs for v in null)
    # SECONDARY diagnostic: node-level label permutation. A permutation of the
    # node-label vector preserves the class marginals (per-class node counts) --
    # this is the "class-stratified node-label shuffle" -- but treats nodes as
    # independent, so it is anti-conservative. Reported only as a conditional
    # diagnostic, never as the headline p-value.
    rng2 = np.random.default_rng(seed + 1)
    node_null = []
    for _ in range(perms):
        yp = y[rng2.permutation(n)]
        jp = np.bincount(x * k + yp, minlength=V * k).reshape(V, k)
        node_null.append(mi_joint(jp))
    node_exc = sum(v >= obs for v in node_null)
    return {"n": n, "distinct_values": V, "observed_bits": obs,
            "permutations": perms, "exceedances": exc,
            "p_one_sided": (1 + exc) / (perms + 1),
            "null_median_bits": float(np.median(null)), "null_p95_bits": float(np.quantile(null, .95)),
            "node_level_null_median_bits": float(np.median(node_null)),
            "node_level_null_p95_bits": float(np.quantile(node_null, .95)),
            "node_level_p_one_sided": (1 + node_exc) / (perms + 1)}


def mi_report(frames):
    frame_labels = [f["label"] for f in frames]
    groups = defaultdict(lambda: {"values": [], "frames": []})
    for fi, f in enumerate(frames):
        for n in f["node_records"]:
            g = groups[(n["lens"], n["class"])]
            # Joint symbol = the quantized bin tuple PLUS the population-presence
            # pattern (per axis: does this axis carry a graded activity vector).
            # This is the protocol's "joint quantized tuple plus population
            # presence pattern". An empty population is the empty pattern (),
            # never a fabricated zero; a class with no population axes carries ()
            # on every node, so the presence term adds no spurious distinctions.
            presence = tuple(bool(axis) for axis in n["population"])
            g["values"].append((tuple(n["bins"]), presence))
            g["frames"].append(fi)
    return [{"lens": lens, "class": cls,
             "joint_MI": mi_image_level(g["values"], g["frames"], frame_labels)}
            for (lens, cls), g in sorted(groups.items())]


def reconstruct(f, scope="spatial_situation"):
    sigs, anchors = {}, {}
    for n in f["node_records"]:
        sigs[n["id"]] = (n["lens"], CT.TypedSignature(
            kind=n.get("kind", "CANONICAL"), type_tag=n.get("type_tag", ""),
            hash_value=n.get("hash_value", 0), class_=n["class"], relation=n["relation"],
            quantized=tuple(n["bins"]), population=tuple(tuple(v) for v in n["population"])))
        if n["anchor"]:
            anchors[n["id"]] = tuple(n["anchor"])
    sc = f["scopes"][scope]
    nodes = frozenset(sc["nodes"])
    edges = frozenset((a, b, CT.EdgeType[c]) for a, b, c in sc["edges"])

    def _ep(p):
        return SC.EdgeParams(class_=p["class_"], quantized=tuple(p["quantized"]),
            sign=p["sign"], confidence=p["confidence"],
            identity_slots=tuple(p["identity_slots"]) if p["identity_slots"] is not None else None,
            population=tuple(tuple(v) for v in p["population"]),
            ontology=p["ontology"], provenance=p["provenance"], origin=p["origin"],
            ordinal=p["ordinal"])

    eps = {}
    for r in f["edge_parameters"]:
        et = CT.EdgeType[r["family"]]
        e = (r["src"], r["dst"], et)
        if e not in edges:
            e = (min(r["src"], r["dst"]), max(r["src"], r["dst"]), et)
        if e in edges:
            # asdict(EdgeParamsMixture) has no top-level class_/quantized; it
            # carries protos/mass/t_last. Rebuild the mixture through its own
            # constructor so the founder/dominant prototype semantics survive.
            if "protos" in r:
                eps[e] = SC.EdgeParamsMixture(protos=[_ep(p) for p in r["protos"]],
                                              mass=list(r["mass"]), t_last=int(r["t_last"]))
            else:
                eps[e] = _ep(r)
    return GT.Subgraph(nodes=nodes, edges=edges, edge_params=eps,
                       anchor_of_node={n: anchors[n] for n in nodes if n in anchors}), sigs


def _filter_one_arm(by_class, median_arm):
    """One template+filter arm. median_arm toggles MATCH_TEMPLATE_MEDIAN_EXEMPLAR
    (structural_intersection's internal exemplar choice); materialization always
    uses the lowest-WL-hash exemplar, exactly as the shipped consolidator does."""
    rows = []
    for cls, pos_frames in sorted(by_class.items()):
        neg_frames = [f for c, fs in sorted(by_class.items()) if c != cls for f in fs]
        store = CONTENT.ContentSignatureStore()
        diag = {}
        def content(f):
            sg, sigs = reconstruct(f)
            return CONTENT.build_content_subgraph(sg, lambda n: sigs.get(n), store, diag)
        positives = [content(f) for f in sorted(pos_frames, key=lambda x: x["name"])]
        negatives = [content(f) for f in sorted(neg_frames, key=lambda x: (x["label"], x["name"]))]
        provider = store.get
        min_count = DIST._wilson_min_recurrence(len(positives), len(negatives))
        min_freq = min_count / len(positives)
        tdiag = {}
        template = SS.structural_intersection(positives, provider, min_frequency=min_freq,
                                              n_neg=len(negatives), diag=tdiag)
        row = {"median_exemplar_arm": median_arm,
               "class": cls, "positives": len(positives), "negatives": len(negatives),
               "wilson_min_count": min_count, "wilson_min_freq": min_freq,
               "template_nodes": len(template.nodes) if template else 0,
               "template_edges": len(template.edges) if template else 0}
        if template is None:
            rows.append(row)
            continue
        attr = sum(lens in RF.ATTRIBUTE_LENS_TYPES for lens, _, _ in template.nodes)
        frame = sum(RF.is_frame(lens) for lens, _, _ in template.nodes)
        mass_attr = math.fsum(c for lens, _, c in template.nodes if lens in RF.ATTRIBUTE_LENS_TYPES)
        mass_all = math.fsum(c for _, _, c in template.nodes)
        deg = Counter()
        for et, a, b, *_ in template.edges:
            deg[a] += 1
            deg[b] += 1
        zero = sum(i not in deg for i in range(len(template.nodes)))
        row.update(template_attribute_nodes=attr, template_frame_nodes=frame,
                   template_attribute_node_share=attr/len(template.nodes),
                   template_attribute_mass_share=mass_attr/mass_all if mass_all else None,
                   template_degree_zero_nodes=zero,
                   template_degree_zero_share=zero/len(template.nodes))
        exemplar = min(positives, key=lambda sg: MC._subgraph_wl_hash(sg, provider))
        core = SS.materialize_template(template, exemplar, provider)
        before = Counter(e[2].name for e in core.edges)
        filtered, fdiag, _ = CO._content_discriminative_filter(
            core, positives, negatives, provider,
            theta_disc_norm=P.THETA_DISC_NORM, theta_pos_min=P.THETA_POS_MIN_CONTENT,
            pool_sigma_floor=P.POOL_SIGMA_FLOOR)
        after = Counter(e[2].name for e in filtered.edges)
        fams = [{"family": fam, "before": before[fam], "after": after[fam],
                 "survival": after[fam]/before[fam] if before[fam] else None}
                for fam in sorted(set(before) | set(after))]
        row.update(core_nodes_before=len(core.nodes), core_edges_before=len(core.edges),
                   core_nodes_after=len(filtered.nodes), core_edges_after=len(filtered.edges),
                   edge_survival_overall=len(filtered.edges)/len(core.edges) if core.edges else None,
                   families=fams,
                   filter_nodes_dropped_zero_mass=fdiag["nodes_dropped_zero_mass"],
                   filter_edges_dropped_zero_mass=fdiag["edges_dropped_zero_mass"],
                   filter_edges_dropped_topk=fdiag["edges_dropped_topk"],
                   filter_edges_dropped_by_endpoint=fdiag["edges_dropped_by_endpoint"])
        rows.append(row)
    return rows


def filter_report(frames):
    by_class = defaultdict(list)
    for f in frames:
        by_class[f["label"]].append(f)
    out = []
    old_median = getattr(P, "MATCH_TEMPLATE_MEDIAN_EXEMPLAR", False)
    try:
        for median_arm in (False, True):
            P.MATCH_TEMPLATE_MEDIAN_EXEMPLAR = median_arm
            out.extend(_filter_one_arm(by_class, median_arm))
    finally:
        P.MATCH_TEMPLATE_MEDIAN_EXEMPLAR = old_median
    return out


def distance_spans(frames):
    agg = defaultdict(list)
    for f in frames:
        for w in f["writer_values"]:
            cls = w["class"]
            specs = SC.U30_EDGE_UNIT_TABLE.get(cls) or SC.EDGE_UNIT_TABLE.get(cls)
            if not specs:
                continue
            for spec in specs:
                v = w["values"].get(spec.name)
                if v is not None:
                    agg[(cls, spec.name, spec.unit, spec.lo, spec.hi)].append(v)
    out = []
    for (cls, name, unit, lo, hi), vals in sorted(agg.items()):
        outside = sum(v < lo or v > hi for v in vals)
        q = quantiles(vals)
        q.update({"class": cls, "slot": name, "unit": unit, "lo": lo, "hi": hi,
                  "outside_span": outside, "outside_share": outside/len(vals)})
        out.append(q)
    return out


def margins():
    out = []
    for size in (256, 96):
        scale = CF.front_end_scale(size, size)
        bank = FL.GaborBank.build_default(scale)
        half = CF._channel_half_supports(bank)
        out.append({"size": size, "front_end_scale": scale,
                    "kernel_full_size": int(bank.kernels.shape[-1]),
                    "single_margin_px": CF._border_margin_px(bank),
                    "single_margin_capped_px": CF._interior_margin(CF._border_margin_px(bank), size, size),
                    "channel_half_supports": half,
                    "channel_margins_capped": CF._channel_margins(bank, size, size),
                    "zones": CF._channel_zones(CF._channel_margins(bank, size, size))})
    return out


def main():
    frames = load_frames()
    if len(frames) != 79:
        raise RuntimeError(f"expected 79 native frames, found {len(frames)}")
    write_json(ROOT/"phase3/results/entropy-presence.json", entropy_report(frames))
    print("entropy done", flush=True)
    write_json(ROOT/"phase3/results/mi-class.json", mi_report(frames))
    print("mi done", flush=True)
    write_json(ROOT/"phase3/results/filter-template.json", filter_report(frames))
    print("filter done", flush=True)
    write_json(ROOT/"phase3/results/distance-spans.json", distance_spans(frames))
    write_json(ROOT/"phase3/results/margins.json", margins())
    totals = {"frames": len(frames),
              "window_nodes": sum(f["window_nodes"] for f in frames),
              "window_edges": sum(f["window_edges"] for f in frames),
              "degree_zero_nodes": sum(f["degree_zero_nodes"] for f in frames),
              "degree_zero_share": sum(f["degree_zero_nodes"] for f in frames)/sum(f["window_nodes"] for f in frames),
              "spatial_nodes": sum(f["spatial_nodes"] for f in frames),
              "spatial_edges": sum(f["spatial_edges"] for f in frames),
              "junction_kinds": dict(sorted(Counter(k for f in frames for k, v in f["junction_kinds"].items() for _ in range(v)).items())),
              "junction_topologies": dict(sorted(Counter(k for f in frames for k, v in f["junction_topologies"].items() for _ in range(v)).items()))}
    write_json(ROOT/"phase3/results/native-totals.json", totals)
    write_json(ROOT/"phase3/audit/analysis-provenance.json", provenance("phase3/harness/analyze_census.py", ["consolidator", "matching.structural_similarity", "memory.content", "core.schema"]))
    print("DONE", totals, flush=True)

if __name__ == "__main__":
    main()
