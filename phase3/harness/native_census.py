"""Native ETH-80 baseline census. No imports from the inherited frontend."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()

from collections import Counter, defaultdict
from contextlib import contextmanager
import argparse
import gc
import json
import time

from phase3.harness.frontend import run_frame, read_rgb, frame_summary
from phase3.harness.metrics import entropy, mutual_information, permutation_mi, quantiles, connected_components, edge_sort

P = load("parameters")
SC = load("core.schema")
RG = load("core.registries")
RF = load("matching.relation_frame")
OB = load("orchestration.binder")
CO = load("consolidator")
SS = load("matching.structural_similarity")
MC = load("memory.cores")
CT = load("core.types")


def split_entries():
    split = json.loads((ROOT / "phase3/inputs/eth80_split.json").read_text())
    out = [("reference", cls, rel) for cls, rel in sorted(split["references"].items())]
    out += [("eval", cls, rel) for cls, paths in sorted(split["eval"].items())
            for rel in sorted(paths)]
    return out


@contextmanager
def capture_edge_values():
    """Read continuous writer arguments; return exactly the original result."""
    captured = []
    original = OB._edge_params
    def wrapped(class_name, values, *args, **kwargs):
        result = original(class_name, values, *args, **kwargs)
        captured.append((class_name, dict(values), tuple(result.quantized)))
        return result
    OB._edge_params = wrapped
    try:
        yield captured
    finally:
        OB._edge_params = original


def summarize(result, writer_values):
    summary = frame_summary(result)
    cg = result.graph
    nodes = sorted(result.window.nodes)
    degree = Counter()
    for a, b, _ in result.window.edges:
        degree[a] += 1
        degree[b] += 1
    summary["degree_zero_nodes"] = sum(degree[n] == 0 for n in nodes)
    summary["degree_zero_share"] = summary["degree_zero_nodes"] / len(nodes) if nodes else None
    summary["largest_component"] = max(connected_components(nodes, result.window.edges), default=0)
    summary["frame_nodes"] = sum(RF.is_frame(result.signatures[n][0]) for n in nodes if n in result.signatures)
    summary["attribute_nodes"] = sum(result.signatures[n][0] in RF.ATTRIBUTE_LENS_TYPES
                                     for n in nodes if n in result.signatures)
    summary["unregistered_nodes"] = sum(result.signatures[n][0] not in
        RF.FRAME_LENS_TYPES | RF.ATTRIBUTE_LENS_TYPES | RF.NON_LENS_TYPES
        for n in nodes if n in result.signatures)
    summary["junction_kinds"] = dict(sorted(Counter(d.k for d in result.all_detections
        if d.sigma.class_ == "JUNCTION").items()))
    summary["junction_topologies"] = dict(sorted(Counter(
        str(int(d.sigma.quantized[2])) for d in result.all_detections
        if d.sigma.class_ == "JUNCTION").items()))
    summary["writer_values"] = [
        {"class": cls, "values": {str(k): (float(v) if isinstance(v, (int,float)) else None)
                                  for k,v in sorted(values.items())},
         "bins": list(bins)} for cls, values, bins in writer_values]
    from dataclasses import asdict
    summary["edge_parameters"] = [
        dict({"src": e[0], "dst": e[1], "family": e[2].name}, **asdict(ep))
        for e in edge_sort(result.window.edges)
        for ep in [result.window.edge_params.get(e) or result.window.edge_params.get(
            (min(e[0],e[1]),max(e[0],e[1]),e[2]))]
        if ep is not None and hasattr(ep,"quantized")
    ]
    summary["node_records"] = [
        {"id": n, "lens": result.signatures[n][0], "class": result.signatures[n][1].class_,
         "relation": result.signatures[n][1].relation,
         "kind": result.signatures[n][1].kind,
         "type_tag": result.signatures[n][1].type_tag,
         "hash_value": result.signatures[n][1].hash_value,
         "bins": list(result.signatures[n][1].quantized),
         "population": list(result.signatures[n][1].population or ()),
         "anchor": list(result.window.anchor_of_node.get(n, ())),
         "degree": degree[n]}
        for n in nodes if n in result.signatures]
    summary["scopes"] = {}
    for scope_name, sg in (("spatial_situation", result.spatial),
                           ("hierarchy_exclusions_off", result.hierarchy_off),
                           ("hierarchy_exclusions_on", result.hierarchy_on)):
        summary["scopes"][scope_name] = {
            "nodes": sorted(sg.nodes),
            "edges": [[e[0], e[1], e[2].name] for e in edge_sort(sg.edges)],
        }
    return summary


def run(output_name="native-census", limit=None, only_class=None):
    entries = split_entries()
    if only_class:
        entries = [e for e in entries if e[1] == only_class]
    if limit is not None:
        entries = entries[:limit]
    records = []
    start = time.monotonic()
    for i, (arm, cls, rel) in enumerate(entries):
        name = rel.rsplit("/", 1)[-1]
        path = ROOT / "data/ETH-80" / cls / name
        out = ROOT / ".cache/phase0" / output_name / (cls + "__" + name + ".json")
        if out.is_file():
            s = json.loads(out.read_text())
            if s.get("protocol_id") == "percept5-phase0-independent-v1" and "scopes" in s:
                records.append({"name": s["name"], "label": s["label"], "arm": s["arm"],
                                "window_nodes": s["window_nodes"], "window_edges": s["window_edges"],
                                "seconds": s.get("seconds", 0.0)})
                print(f"{i+1}/{len(entries)} {cls}/{name}: resumed cached measurement", flush=True)
                continue
        t = time.monotonic()
        with capture_edge_values() as captured:
            result = run_frame(read_rgb(path), name)
        s = summarize(result, captured)
        s.update(arm=arm, label=cls, source_path=rel, seconds=time.monotonic()-t,
                 protocol_id="percept5-phase0-independent-v1")
        records.append({"name": s["name"], "label": s["label"], "arm": s["arm"],
                        "window_nodes": s["window_nodes"], "window_edges": s["window_edges"],
                        "seconds": s["seconds"]})
        # Full per-frame records are reproducible intermediate data, kept out
        # of the patchset (the repository has no external-data storage convention).
        write_json(out, s)
        print(f"{i+1}/{len(entries)} {cls}/{name}: nodes={s['window_nodes']} edges={s['window_edges']} spatial={s['spatial_nodes']}/{s['spatial_edges']} {s['seconds']:.2f}s", flush=True)
        del result, s, captured
        gc.collect()
    write_json(ROOT / "phase3/audit" / (output_name + "-provenance.json"),
               provenance("phase3/harness/native_census.py", [
                   "phase3.harness.frontend", "lenses.base", "lenses.v2", "lenses.v4",
                   "orchestration.binder", "consolidator", "memory.cores", "matching.relation_frame"]))
    # Save graph inputs for later leave-one-image-out filter measurements, as
    # JSON, never pickle from a sibling checkout. The product signatures are
    # reconstructed by their own constructors from the recorded tuples.
    return records


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="native-census")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--class", dest="only_class")
    args = ap.parse_args()
    records = run(args.output, args.limit, args.only_class)
    write_json(ROOT / "phase3/results" / (args.output + "-index.json"), {
        "n_frames": len(records), "seconds": sum(r["seconds"] for r in records),
        "frames": [{"name":r["name"],"label":r["label"],"arm":r["arm"],
                    "nodes":r["window_nodes"],"edges":r["window_edges"]} for r in records]})
