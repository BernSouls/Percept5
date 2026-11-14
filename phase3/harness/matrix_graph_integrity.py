"""Check inputs for reverse-duplicate undirected edges and hash provenance."""
from phase3.runtime.bootstrap import ROOT,activate,write_json,imported_product_paths
activate()
from collections import Counter
import hashlib,json
from core.types import EdgeType,UNDIRECTED_EDGE_TYPES
from core.frontend_contract import frontend_contract,assert_live_contract

def main():
    rs=json.loads((ROOT/'.cache/joint-matrix/index.json').read_text())['records']
    rows=[]
    with frontend_contract():
        assert_live_contract();imported_product_paths()
        for r in rs:
            if r['error']:
                rows.append({'name':r['name'],'error':r['error']});continue
            v=json.loads((ROOT/r['path']).read_text())
            h=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            c=Counter((min(e['a'],e['b']),max(e['a'],e['b']),e['type']) for e in v['selected_graph']['edges'] if EdgeType[e['type']] in UNDIRECTED_EDGE_TYPES)
            rows.append({'name':r['name'],'same_hash':h==r['sha256'],'prior_equal':r['prior_equal'],'duplicate_undirected':sum(n-1 for n in c.values() if n>1)})
    out={'frames':len(rows),'frame_errors':sum('error' in r for r in rows),'hashes_match':sum(bool(r.get('same_hash')) for r in rows),'prior_equal':sum(bool(r.get('prior_equal')) for r in rows),'reverse_duplicates':sum(r.get('duplicate_undirected',0) for r in rows),'rows':rows}
    write_json(ROOT/'phase3/results/joint-matrix-input-integrity.json',out)
    print({k:v for k,v in out.items() if k!='rows'})
if __name__=='__main__':main()
