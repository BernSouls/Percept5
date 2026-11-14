"""Junction kind/topology distribution across 41 views of one ETH-80 object."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import json, tarfile, time
from collections import Counter
from pathlib import Path
import numpy as np
from phase3.harness.frontend import run_frame, read_rgb
from phase3.harness.metrics import entropy

P = load("parameters")
V2 = load("lenses.v2")


def ensure_images():
    split = json.loads((ROOT/"phase3/inputs/eth80_split.json").read_text())
    sha = split["dataset_commit"]
    archive = ROOT/".cache/eth80/source.tar.gz"
    outdir = ROOT/"data/ETH-80/apple_object1_all41"
    outdir.mkdir(parents=True, exist_ok=True)
    # The archive holds 41 object-1 VIEW pngs directly under 1/1/ plus 41
    # segmentation-mask pngs under 1/1/maps/. Restrict to files whose path
    # relative to the archive root is exactly "1/1/<name>.png" (no deeper
    # directory), and de-duplicate by basename, so exactly 41 unique views
    # remain. The maps are not object views and must never be counted.
    paths = {}
    with tarfile.open(archive) as t:
        prefix = t.getmembers()[0].name.split('/')[0]
        for m in t.getmembers():
            if not m.isfile():
                continue
            rel = m.name[len(prefix)+1:]
            parts = rel.split("/")
            if len(parts) != 3 or parts[0] != "1" or parts[1] != "1":
                continue
            name = parts[2]
            if not name.endswith(".png") or name.endswith("-map.png"):
                continue
            dst = outdir/name
            if not dst.exists():
                dst.write_bytes(t.extractfile(m).read())
            paths[name] = dst
    return sorted(paths.values())


def main():
    paths = ensure_images()
    if len(paths) != 41:
        raise RuntimeError(f"expected 41 apple object-1 views, found {len(paths)}")
    rows = []
    for p in paths:
        t = time.monotonic()
        r = run_frame(read_rgb(p, 96), p.stem)
        js = [d for d in r.all_detections if d.sigma.class_ == "JUNCTION"]
        kinds = Counter(d.k for d in js)
        topos = Counter(int(d.sigma.quantized[2]) for d in js)
        rows.append({"view": p.stem, "junctions": len(js),
                     "kinds": dict(sorted(kinds.items())),
                     "topologies": dict(sorted((str(k), v) for k, v in topos.items())),
                     "seconds": time.monotonic()-t})
        print(p.stem, len(js), dict(kinds), flush=True)
    all_kinds = Counter(k for r in rows for k, v in r["kinds"].items() for _ in range(v))
    all_topos = Counter(k for r in rows for k, v in r["topologies"].items() for _ in range(v))
    summary = {"corpus": "ETH80_OBJECT1_96", "object": "apple1", "views": len(rows),
               "total_junctions": sum(r["junctions"] for r in rows),
               "kind_counts": dict(sorted(all_kinds.items())),
               "topology_counts": dict(sorted(all_topos.items())),
               "kind_entropy_bits": entropy(k for r in rows for k, v in r["kinds"].items() for _ in range(v)),
               "topology_entropy_bits": entropy(k for r in rows for k, v in r["topologies"].items() for _ in range(v)),
               "views_with_zero_junctions": sum(r["junctions"] == 0 for r in rows),
               "rows": rows}
    write_json(ROOT/"phase3/results/junction-views.json", summary)
    write_json(ROOT/"phase3/audit/junction-views-provenance.json", provenance("phase3/harness/junction_views.py", ["lenses.v2", "phase3.harness.frontend"]))
    print("DONE", summary["kind_counts"], summary["topology_counts"], flush=True)

if __name__ == "__main__":
    main()
