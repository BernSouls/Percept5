"""Compare completed, independent hash-seed passes; timings are excluded."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, write_json
import json,hashlib


def main():
    roots=[ROOT/'.cache/build-measure'/s for s in ('seed0','seed1729')]
    indexes=[json.loads((r/'index.json').read_text())['records'] for r in roots]
    keyed=[{(x['corpus'],x['name']):x for x in index} for index in indexes]
    rows=[]
    for key in sorted(keyed[0].keys()|keyed[1].keys()):
        a,b=(k.get(key) for k in keyed)
        rows.append({'corpus':key[0],'name':key[1],'seed0':a.get('canonical_sha256') if a else None,
                     'seed1729':b.get('canonical_sha256') if b else None,
                     'match':bool(a and b and not a['error'] and not b['error'] and a['canonical_sha256']==b['canonical_sha256'])})
    out={'scope':'canonical per-frame result excluding elapsed time and provenance',
         'frame_comparison':rows,'frames_compared':len(rows),'frame_equal':sum(r['match'] for r in rows)}
    paths=[ROOT/'phase3/results'/('build-pairs-'+s+'.json') for s in ('seed0','seed1729')]
    if all(p.exists() for p in paths):
        vals=[json.loads(p.read_text())['canonical_without_timing'] for p in paths]
        hashes=[hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest() for v in vals]
        out['pair_hashes']=hashes;out['pairs_equal']=hashes[0]==hashes[1]
    paths=[ROOT/'phase3/results'/('build-census-'+s+'.json') for s in ('seed0','seed1729')]
    if all(p.exists() for p in paths):
        vals=[json.loads(p.read_text()) for p in paths]
        for v in vals:
            for corpus in v.values():
                corpus.pop('frame_seconds',None)
                corpus.pop('runtime_pass',None)
        hashes=[hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest() for v in vals]
        out['census_hashes']=hashes;out['census_equal']=hashes[0]==hashes[1]
    filters=[ROOT/'phase3/results'/('build-filter-'+s+'.json') for s in ('seed0','seed1729')]
    if all(p.exists() for p in filters):
        vals=[json.loads(p.read_text()) for p in filters]
        out['filter_repeat_same_failure']=(all(v.get('status')=='FAILED during content pooling' for v in vals) and
             all(vals[0].get(k)==vals[1].get(k) for k in ('processed_frames','failed_class','failed_frame','error')))
    margins=[ROOT/'phase3/results'/name for name in ('build-renderer-margin.json','build-renderer-margin-repeat.json')]
    if all(p.exists() for p in margins):
        hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in margins]
        out['margin_hashes']=hashes;out['margin_equal']=hashes[0]==hashes[1]
    closure=[ROOT/'phase3/results'/('build-closure-'+s+'.json') for s in ('seed0','seed1729')]
    if all(p.exists() for p in closure):
        hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in closure]
        out['closure_hashes']=hashes;out['closure_equal']=hashes[0]==hashes[1]
    out['passed']=(len(rows)==151 and out['frame_equal']==151 and out.get('pairs_equal') is True and out.get('census_equal') is True and out.get('margin_equal') is True and out.get('closure_equal') is True and out.get('filter_repeat_same_failure') is True)
    write_json(ROOT/'phase3/results/build-determinism.json',out)
    print('determinism:',out['frame_equal'],'/',len(rows),'pairs_equal',out.get('pairs_equal'),flush=True)
if __name__=='__main__':main()
