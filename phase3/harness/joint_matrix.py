"""Execute the pre-registered ETH80 reference-by-held-out joint MCS matrix."""
from phase3.runtime.bootstrap import ROOT,activate,write_json,imported_product_paths,provenance
activate()
import argparse,hashlib,json,math,time,traceback
from phase3.harness.build_pairs import graph
from matching.joint_mcs import joint_mcs
from core.frontend_contract import frontend_contract,assert_live_contract


def index(root,stream):
    while True:
        try:return json.loads((root/'index.json').read_text())['records']
        except (FileNotFoundError,json.JSONDecodeError):
            if not stream:raise
            time.sleep(1)

def load(row,offset):
    v=json.loads((ROOT/row['path']).read_text());digest=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    if digest!=row['sha256']:raise RuntimeError('graph hash mismatch '+row['name'])
    return graph(v,offset)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed-name',required=True);ap.add_argument('--stream',action='store_true');arg=ap.parse_args()
    protocol=ROOT/'phase3/audit/joint-mcs-protocol.json';pbytes=protocol.read_bytes();p=json.loads(pbytes)
    if p['protocol_id']!='eth80-joint-mcs-v1':raise RuntimeError('wrong preregistration')
    root=ROOT/'.cache/joint-matrix';wanted=['apple','car','cow','cup','dog','horse','pear','tomato']
    while True:
        rs=index(root,arg.stream);refs={r['class']:r for r in rs if r['arm']=='reference' and not r['error']}
        if len(refs)==8:break
        if not arg.stream:raise RuntimeError('missing references')
        time.sleep(2)
    reference={c:load(refs[c],0) for c in wanted};rows=[];seen=set()
    while len(seen)<128:
        rs=index(root,arg.stream)
        errs=[r for r in rs if r['error']]
        if errs:raise RuntimeError('input frame errors '+str(errs))
        ready=[r for r in rs if r['arm']=='eval' and r['name'] not in seen]
        if not ready:
            if not arg.stream:raise RuntimeError('missing evaluation graphs')
            time.sleep(2);continue
        for rec in ready:
            b,sb=load(rec,1<<80)
            for cls in wanted:
                a,sa=reference[cls]
                try:
                    with frontend_contract():
                        assert_live_contract();imported_product_paths()
                        result=joint_mcs(a,b,sa,sb)
                    rows.append({'reference':cls,'heldout_class':rec['class'],'heldout_frame':rec['name'],'score':result.score,'matched_nodes':len(result.mapping),'matched_edges':result.matched_edges,'graded_edges':result.graded_edges,'graded_similarity_sum':result.graded_edge_similarity_sum,'presence_only_edges':result.presence_only_edges,'unmatched_reference_nodes':len(a.nodes)-len(result.mapping),'unmatched_heldout_nodes':len(b.nodes)-len(result.mapping),'budget_exhausted':result.budget_exhausted,'one_to_one':len(result.mapping)==len(set(result.mapping.values())),'mapping':sorted([u,v-(1<<80)] for u,v in result.mapping.items()),'error':None})
                except Exception as e:
                    rows.append({'reference':cls,'heldout_class':rec['class'],'heldout_frame':rec['name'],'error':str(e),'traceback':traceback.format_exc()})
                    print('ERROR',cls,rec['name'],e,flush=True)
            seen.add(rec['name']);print('heldout',len(seen),'/128',rec['class'],rec['name'],flush=True)
    cells={}
    for i in wanted:
        cells[i]={}
        for j in wanted:
            pairs=[r for r in rows if r['reference']==i and r['heldout_class']==j];good=[r for r in pairs if r['error'] is None]
            if len(pairs)!=16 or len(good)!=16:
                cells[i][j]={'comparisons':len(pairs),'successes':len(good),'error':'incomplete cell'};continue
            n=len(good);graded=sum(r['graded_edges'] for r in good)
            cells[i][j]={'comparisons':n,'similarity':math.fsum(r['score'] for r in good)/n,'matched_nodes_mean':math.fsum(r['matched_nodes'] for r in good)/n,'matched_edges_mean':math.fsum(r['matched_edges'] for r in good)/n,'graded_edges_total':graded,'mean_graded_edge_similarity':math.fsum(r['graded_similarity_sum'] for r in good)/graded if graded else None,'presence_only_edges_total':sum(r['presence_only_edges'] for r in good),'budget_exhausted':sum(r['budget_exhausted'] for r in good),'one_to_one_all':all(r['one_to_one'] for r in good)}
    complete=all('similarity' in cells[i][j] for i in wanted for j in wanted)
    summary={}
    if complete:
        summary={'diagonal_mean':math.fsum(cells[i][i]['similarity'] for i in wanted)/8,'off_diagonal_mean':math.fsum(cells[i][j]['similarity'] for i in wanted for j in wanted if i!=j)/56,'per_class_margin':{i:cells[i][i]['similarity']-max(cells[i][j]['similarity'] for j in wanted if j!=i) for i in wanted}}
    result={'protocol_sha256':hashlib.sha256(pbytes).hexdigest(),'classes':wanted,'cells':cells,'summary':summary,'comparisons':len(rows),'errors':sum(r['error'] is not None for r in rows),'complete':complete,'per_view':rows}
    out=ROOT/'phase3/results'/('joint-matrix-'+arg.seed_name+'.json');write_json(out,result)
    print('DONE',len(rows),'errors',result['errors'],'summary',summary,flush=True)
if __name__=='__main__':main()
