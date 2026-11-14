"""Reconstruct the 136 pinned ETH reference/evaluation graphs for the matrix."""
from phase3.runtime.bootstrap import ROOT,activate,write_json,imported_product_paths
activate()
import gc,hashlib,json,traceback
from phase3.harness.frontend import run_frame,read_rgb
from phase3.harness.build_measure import capture
from core.frontend_contract import frontend_contract,assert_live_contract

def main():
    m=json.loads((ROOT/'phase3/inputs/eth80_all8.json').read_text())
    es=[('reference',c,r) for c,r in sorted(m['references'].items())]
    es += [('eval',c,r) for c,rs in sorted(m['eval'].items()) for r in rs]
    old=json.loads((ROOT/'phase3/results/build-determinism.json').read_text())['frame_comparison']
    old={(r['corpus'],r['name']):r['seed0'] for r in old}
    out=ROOT/'.cache/joint-matrix';out.mkdir(parents=True,exist_ok=True);rows=[]
    for arm,cls,r in es:
        name=r['path'].split('/')[-1]
        try:
            image=ROOT/r['path'];assert hashlib.sha256(image.read_bytes()).hexdigest()==r['sha256']
            with frontend_contract():
                assert_live_contract();imported_product_paths();f=run_frame(read_rgb(image),name);v=capture(f,'ETH80_ALL8',arm,cls,r)
            path=out/(name+'.json');write_json(path,v)
            digest=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            rows.append({'arm':arm,'class':cls,'name':name,'path':str(path.relative_to(ROOT)),'sha256':digest,'prior_equal':digest==old.get(('ETH80_ALL8',name)),'error':None})
            del f,v;gc.collect()
        except Exception as e:
            rows.append({'arm':arm,'class':cls,'name':name,'error':str(e),'traceback':traceback.format_exc()})
        write_json(out/'index.json',{'records':rows})
        print(len(rows),'/136',cls,name,'prior_equal',rows[-1].get('prior_equal'),'error',rows[-1]['error'],flush=True)
    print('DONE errors',sum(bool(x['error']) for x in rows),'same_prior',sum(bool(x.get('prior_equal')) for x in rows),flush=True)
if __name__=='__main__':main()
