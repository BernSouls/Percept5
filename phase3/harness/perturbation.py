"""Registered translation/occlusion/isotropy probes. No product edits."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import json, math, time
from collections import Counter, defaultdict
import numpy as np
from PIL import Image, ImageDraw
from phase3.harness.frontend import run_frame, read_rgb
from phase3.harness.metrics import quantiles, connected_components, correlation, edge_sort

P = load("parameters")
SC = load("core.schema")
H = load("core.hashing")
CT = load("core.types")


def anchor_key(a):
    return H.serialize_value(a).hex()


def fragments(result):
    out = {}
    for d in result.all_detections:
        if d.k != "ContourFragment":
            continue
        frag = next((r[1] for r in d.rho if r[0] == "fragment"), None)
        key = (anchor_key(d.alpha), frag)
        out[key] = {"mid": list(getattr(d, "_frag_mid", (float("nan"), float("nan")))),
                    "tangent": getattr(d, "_frag_tangent", None),
                    "bins": list(d.sigma.quantized), "parent_anchor": anchor_key(d.alpha)}
    return out


def edge_records(result):
    amap = result.graph.pattern_node_anchor_map()
    out = {}
    for e in edge_sort(result.window.edges):
        a, b, et = e
        ka, kb = anchor_key(amap.get(a)), anchor_key(amap.get(b))
        if et in CT.UNDIRECTED_EDGE_TYPES:
            ka, kb = sorted((ka, kb))
        key = (et.name, ka, kb)
        ep = result.window.edge_params.get(e) or result.window.edge_params.get((min(a,b),max(a,b),et))
        if ep is None or not hasattr(ep, "quantized"):
            out[key] = {"class": None, "identity": None, "graded": None}
            continue
        ids = set(ep.identity_slots if ep.identity_slots is not None else SC.EDGE_IDENTITY_SLOTS.get(ep.class_, ()))
        specs = SC.U30_EDGE_UNIT_TABLE.get(ep.class_, ()) if SC._is_u30_edge_params(ep) else SC.EDGE_UNIT_TABLE.get(ep.class_, ())
        if len(specs) == len(ep.quantized):
            ids.update(i for i,s in enumerate(specs) if s.quantiser == "lookup_key")
        ident = tuple(ep.quantized[i] for i in sorted(ids) if i < len(ep.quantized))
        graded = tuple(v for i,v in enumerate(ep.quantized) if i not in ids and v != SC.UNKNOWN)
        out[key] = {"class": ep.class_, "identity": ident, "graded": graded}
    return out


def translate(img, dx, dy):
    out = np.empty_like(img)
    out[:] = img[0,0]
    h,w = img.shape[:2]
    ys0, ys1 = max(0,dy), min(h,h+dy)
    xs0, xs1 = max(0,dx), min(w,w+dx)
    out[ys0:ys1, xs0:xs1] = img[ys0-dy:ys1-dy, xs0-dx:xs1-dx]
    return out


def compare_translation(base, pert, dx, dy):
    fb, fp = fragments(base), fragments(pert)
    common = sorted(set(fb) & set(fp))
    drift = []
    sig_changed = 0
    for k in common:
        mb, mp = fb[k]["mid"], fp[k]["mid"]
        if all(math.isfinite(x) for x in mb+mp):
            drift.append(math.hypot(mp[0]-dx-mb[0], mp[1]-dy-mb[1]))
        sig_changed += fb[k]["bins"] != fp[k]["bins"]
    eb, ep = edge_records(base), edge_records(pert)
    ek = sorted(set(eb) & set(ep))
    topo_same = sum(eb[k]["class"] == ep[k]["class"] and eb[k]["identity"] == ep[k]["identity"] for k in ek)
    geom_same = sum(eb[k]["graded"] == ep[k]["graded"] for k in ek)
    both_known = [k for k in ek if eb[k]["graded"] is not None and ep[k]["graded"] is not None]
    geom_known = sum(eb[k]["graded"] == ep[k]["graded"] for k in both_known)
    return {"dx": dx, "dy": dy,
            "fragments_base": len(fb), "fragments_pert": len(fp), "fragment_matches": len(common),
            "fragment_unmatched_base": len(set(fb)-set(fp)), "fragment_unmatched_pert": len(set(fp)-set(fb)),
            "fragment_drift_px": quantiles(drift), "fragment_signature_changed": sig_changed,
            "edge_matches": len(ek), "edges_base": len(eb), "edges_pert": len(ep),
            "topological_identity_same": topo_same,
            "topological_identity_share": topo_same/len(ek) if ek else None,
            "graded_bins_same_all_matched": geom_same,
            "graded_bins_same_share_all_matched": geom_same/len(ek) if ek else None,
            "graded_both_known": len(both_known), "graded_bins_same_known": geom_known,
            "graded_bins_same_share_known": geom_known/len(both_known) if both_known else None}


def polygon_fixture():
    bg = 60
    img = Image.new("RGB", (96,96), (bg,bg,bg))
    draw = ImageDraw.Draw(img)
    poly = [(18,20),(70,16),(82,40),(64,48),(78,78),(30,82),(14,58),(34,46)]
    draw.polygon(poly, fill=(210,210,210))
    base = np.asarray(img).copy()
    occ = base.copy()
    x0 = int(96*0.40); x1 = int(96*0.60)
    occ[:, x0:x1] = bg
    return base, occ


def run():
    protocol = json.loads((ROOT/"phase3/audit/protocol.json").read_text())
    split = json.loads((ROOT/"phase3/inputs/eth80_split.json").read_text())
    rows = []
    for cls, paths in sorted(split["eval"].items()):
        for rel in sorted(paths)[:2]:
            name = rel.rsplit("/",1)[-1]
            cached = ROOT/".cache/phase0/perturbation"/(cls+"__"+name+".json")
            if cached.is_file():
                row = json.loads(cached.read_text())
                if len(row.get("translations", [])) == len(protocol["sampling"]["translation_offsets"]):
                    rows.append(row)
                    print(cls, name, "resumed cached measurement", flush=True)
                    continue
            img = read_rgb(ROOT/"data/ETH-80"/cls/name, 96)
            t = time.monotonic()
            base = run_frame(img, name)
            comps = []
            for dx,dy in protocol["sampling"]["translation_offsets"]:
                pert = run_frame(translate(img,dx,dy), f"{name}_t{dx}_{dy}")
                comps.append(compare_translation(base,pert,dx,dy))
            row = {"label": cls, "name": name, "corpus": "ETH80_EVAL75_96",
                   "baseline_nodes": len(base.window.nodes), "baseline_edges": len(base.window.edges),
                   "translations": comps, "seconds": time.monotonic()-t}
            rows.append(row)
            write_json(ROOT/".cache/phase0/perturbation"/(cls+"__"+name+".json"), row)
            print(cls,name,"done",row["seconds"],flush=True)
    base_img, occ_img = polygon_fixture()
    b = run_frame(base_img, "polygon_base")
    o = run_frame(occ_img, "polygon_occluded")
    fb, fo = fragments(b), fragments(o)
    common = sorted(set(fb)&set(fo))
    drift = [math.hypot(fo[k]["mid"][0]-fb[k]["mid"][0], fo[k]["mid"][1]-fb[k]["mid"][1]) for k in common]
    occ_row = {"corpus":"SYNTHETIC_CONTROLS","fixture":"nonconvex_polygon_central_20pct_width_removed",
               "removed_fraction_of_width":0.20,
               "contours_base": len(b.observation.get_contours()), "contours_occluded": len(o.observation.get_contours()),
               "fragments_base":len(fb),"fragments_occluded":len(fo),"matches":len(common),
               "unmatched_base":len(set(fb)-set(fo)),"unmatched_occluded":len(set(fo)-set(fb)),
               "fragment_drift_px":quantiles(drift),
               "signature_changed":sum(fb[k]["bins"]!=fo[k]["bins"] for k in common),
               "nodes_base":len(b.window.nodes),"nodes_occluded":len(o.window.nodes),
               "edges_base":len(b.window.edges),"edges_occluded":len(o.window.edges)}
    controls = []
    rng = np.random.default_rng(20261113)
    images = {"flat_grey_96": np.full((96,96,3),128,np.uint8),
              "flat_white_96": np.full((96,96,3),255,np.uint8),
              "noise_96": rng.integers(0,256,(96,96,3),dtype=np.uint8),
              "flat_grey_256": np.full((256,256,3),128,np.uint8)}
    for name,img in images.items():
        r = run_frame(img,name)
        iso = [r.observation.get_isotropy(u) for u in range(len(r.observation._regions))]
        elong = [r.observation.get_elongation(u) for u in range(len(r.observation._regions))]
        rough = [r.observation.get_roughness(u) for u in range(len(r.observation._regions))]
        gate_below = sum(x < P.ORIENTATION_GRADIENT_MIN for x in rough)
        controls.append({"name":name,"orientation_raw":sum(d.k=="Orientation" for d in r.raw),
                         "orientation_bound":sum(d.k=="Orientation" for d in r.bound_v1),
                         "orientation_window":sum(r.signatures[n][0]=="Orientation" for n in r.window.nodes),
                         "largest_component":max(connected_components(r.window.nodes,r.window.edges),default=0),
                         "nodes":len(r.window.nodes),"edges":len(r.window.edges),
                         "regions":len(iso),"roughness_below_gate":gate_below,
                         "isotropy_elongation_pearson":correlation(iso,elong),
                         "isotropy_values":quantiles(iso),"roughness_values":quantiles(rough)})
    write_json(ROOT/"phase3/results/perturbation-summary.json",{"translations":rows,"occlusion":occ_row,"controls":controls})
    write_json(ROOT/"phase3/audit/perturbation-provenance.json",provenance("phase3/harness/perturbation.py",["phase3.harness.frontend","lenses.base","orchestration.binder"]))
    print("DONE",flush=True)

if __name__=="__main__":
    run()
