"""Registered finished-build frame census. One fresh process per hash seed.

Raw per-frame records are under the ignored workspace cache, not Phase 0.
No frames are resumed from a different pass. Errors are recorded, not omitted.
"""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, provenance, write_json
activate()
import argparse, gc, json, os, time, traceback, hashlib
from collections import Counter
from dataclasses import asdict
from phase3.harness.frontend import run_frame, read_rgb
from phase3.harness.metrics import edge_sort
from core.frontend_contract import assert_live_contract, frontend_contract


def signature(sig):
    return {"kind":sig.kind,"class":sig.class_,"relation":sig.relation,
            "type_tag":sig.type_tag,"hash_value":sig.hash_value,
            "quantized":list(sig.quantized),"population":[list(a) for a in sig.population],
            "features":[{"name":f.name,"source_lens":f.source_lens,"attachment":list(f.attachment),
                         "signature":signature(f.signature)} for f in getattr(sig,"_named_features",())]}


def entries():
    eth=json.loads((ROOT/'phase3/inputs/eth80_all8.json').read_text())
    for cls in sorted(eth['references']):
        yield 'ETH80_ALL8','reference',cls,eth['references'][cls]
    for cls in sorted(eth['eval']):
        for rec in eth['eval'][cls]:
            yield 'ETH80_ALL8','eval',cls,rec
    r=json.loads((ROOT/'phase3/inputs/renderer_truth_v1.json').read_text())
    for rec in sorted(r['scenes'],key=lambda v:v['name']):
        yield 'RENDERER_TRUTH_V1',rec['split'],'',rec


def capture(result, corpus, arm, label, rec):
    window, selected = result.window, result.spatial
    fam_all=Counter(e[2].name for e in window.edges)
    fam_sel=Counter(e[2].name for e in selected.edges)
    from matching.perceptual_selection import is_structural
    from matching.relation_frame import is_frame
    from phase3.harness.metrics import connected_components
    frame={n for n in window.nodes if n in result.signatures and is_frame(result.signatures[n][0])}
    all_frame=[e for e in window.edges if e[0] in frame and e[1] in frame]
    structural=[e for e in all_frame if is_structural(e[2])]
    selected_sigs={n:selected.signature_overrides.get(n) or result.signatures.get(n) for n in selected.nodes}
    nodes=[]
    for n,info in sorted(selected_sigs.items()):
        if not info: continue
        pos=selected.anchor_of_node.get(n)
        nodes.append({'id':n,'lens':info[0],'sig':signature(info[1]),'position':list(pos) if pos is not None else None})
    edges=[]
    for e in edge_sort(selected.edges):
        ep=selected.edge_params.get(e)
        try: params=asdict(ep) if ep else None
        except TypeError: params=None
        edges.append({'a':e[0],'b':e[1],'type':e[2].name,'weight':selected.weights.get(e,1.),'params':params})
    return {'corpus':corpus,'arm':arm,'label':label,'name':rec.get('name',rec['path'].split('/')[-1]),
            'path':rec['path'],'source_sha256':rec['sha256'],
            'window_nodes':len(window.nodes),'window_edges':len(window.edges),
            'selected_nodes':len(selected.nodes),'selected_edges':len(selected.edges),
            'family_window':dict(sorted(fam_all.items())),'family_selected':dict(sorted(fam_sel.items())),
            'selection_diagnostics':result.mapper.diagnostics.get('perceptual_selection',{}),
            'frame_component_all':max(connected_components(frame,all_frame),default=0),
            'frame_component_structural':max(connected_components(frame,structural),default=0),
            'selected_graph':{'nodes':nodes,'edges':edges}}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pass-name',required=True);args=ap.parse_args()
    out=ROOT/'.cache'/'build-measure'/args.pass_name
    out.mkdir(parents=True,exist_ok=True)
    es=list(entries()); records=[]
    for i,(corpus,arm,label,rec) in enumerate(es):
        name=rec.get('name',rec['path'].split('/')[-1]);path=out/(corpus+'__'+name+'.json')
        t=time.monotonic()
        try:
            with frontend_contract():
                assert_live_contract()
                r=run_frame(read_rgb(ROOT/rec['path']),name)
                row=capture(r,corpus,arm,label,rec)
            elapsed=time.monotonic()-t
            write_json(path,row)
            digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            records.append({'corpus':corpus,'arm':arm,'label':label,'name':name,'path':str(path.relative_to(ROOT)),'seconds':elapsed,'canonical_sha256':digest,'error':None})
            print(f'{i+1}/{len(es)} {corpus} {name} {elapsed:.2f}s {row["window_edges"]}->{row["selected_edges"]}',flush=True)
            del r,row
        except Exception as exc:
            elapsed=time.monotonic()-t
            records.append({'corpus':corpus,'arm':arm,'label':label,'name':name,'seconds':elapsed,'error':str(exc),'traceback':traceback.format_exc()})
            print(f'{i+1}/{len(es)} ERROR {corpus} {name}: {exc}',flush=True)
        write_json(out/'index.json',{'pass':args.pass_name,'seed':os.getenv('PYTHONHASHSEED'),'records':records})
        gc.collect()
    write_json(out/'provenance.json',provenance('phase3/harness/build_measure.py',['phase3.harness.frontend','matching.fuzzy','matching.perceptual_selection','matching.feature_attachment','memory.mapper','orchestration.binder']))
    print('DONE',len(records),'failures',sum(bool(x['error']) for x in records),flush=True)

if __name__=='__main__': main()
