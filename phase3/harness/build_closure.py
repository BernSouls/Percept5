"""Count recorded matcher-input closure slots; observation contours not cached."""
from phase3.runtime.bootstrap import ROOT,activate,write_json
activate()
import argparse,json
from collections import Counter,defaultdict
from core.registries import ABSENT
from core.slots import slot_names

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pass-name',required=True);a=ap.parse_args()
    root=ROOT/'.cache/build-measure'/a.pass_name
    records=json.loads((root/'index.json').read_text())['records'];totals=defaultdict(Counter)
    for r in records:
        if r['error']:continue
        row=json.loads((ROOT/r['path']).read_text())
        for n in row['selected_graph']['nodes']:
            cls=n['sig']['class']
            if cls not in ('PEAK_CHAIN','CONTOUR'):continue
            i=slot_names(cls).index('closure');q=n['sig']['quantized'];v=q[i] if i<len(q) else ABSENT
            totals[(r['corpus'],cls)]['total']+=1
            totals[(r['corpus'],cls)]['absent' if v==ABSENT else 'closed' if v==1 else 'open' if v==0 else 'other']+=1
    output={corp:{cls:dict(totals[(corp,cls)]) for c,cls in sorted(totals) if c==corp} for corp in sorted({c for c,_ in totals})}
    write_json(ROOT/'phase3/results'/('build-closure-'+a.pass_name+'.json'),{'scope':'selected graph pattern nodes; observation contours and pre-selection detections not retained','counts':output})
    print(json.dumps(output,sort_keys=True),flush=True)
if __name__=='__main__':main()
