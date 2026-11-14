"""Aggregate finished-build measurement only; never reads Phase-0 frame cache."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, write_json
activate()
import argparse, json, math
from collections import Counter,defaultdict
from phase3.harness.metrics import quantiles
from phase3.harness.analyze_census import mi_image_level


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pass-name',required=True);a=ap.parse_args()
    root=ROOT/'.cache/build-measure'/a.pass_name
    idx=json.loads((root/'index.json').read_text())['records']
    summary={}
    groups=defaultdict(lambda:{'values':[],'frames':[]})
    frame_labels=[]
    for corpus in ('ETH80_ALL8','RENDERER_TRUTH_V1'):
        records=[x for x in idx if x['corpus']==corpus]; ok=[x for x in records if not x['error']]
        fam0,fam1=Counter(),Counter();missing=Counter();nodes=edges=0;allnodes=alledges=0
        budgets=[]; components_all=[]; components_structural=[]; component_ratios=[]
        for record in ok:
            r=json.loads((ROOT/record['path']).read_text())
            fam0.update(r['family_window']);fam1.update(r['family_selected'])
            missing.update((name,reason) for name,reason in r['selection_diagnostics'].get('structural_families_missing',{}).items())
            nodes+=r['selected_nodes'];edges+=r['selected_edges'];allnodes+=r['window_nodes'];alledges+=r['window_edges']
            budgets.append(r['selected_edges'])
            components_all.append(r['frame_component_all'])
            components_structural.append(r['frame_component_structural'])
            if r['frame_component_all']:
                component_ratios.append(r['frame_component_structural']/r['frame_component_all'])
            if corpus=='ETH80_ALL8' and record['arm']=='eval':
                fi=len(frame_labels);frame_labels.append(record['label'])
                for node in r['selected_graph']['nodes']:
                    sig=node['sig'];g=groups[(node['lens'],sig['class'])]
                    g['values'].append((tuple(sig['quantized']),tuple(bool(v) for v in sig['population'])))
                    g['frames'].append(fi)
        fq=quantiles([x['seconds'] for x in ok])
        summary[corpus]={'n_registered':len(records),'n_success':len(ok),'failures':[x for x in records if x['error']],
          'frame_seconds':fq,'runtime_pass':bool(ok) and fq['p95']<=30 and fq['max']<=60,
          'window_nodes':allnodes,'window_edges':alledges,'selected_nodes':nodes,'selected_edges':edges,
          'edge_budget':quantiles(budgets),'edge_budget_pass':bool(ok) and max(budgets)<=512,
          'largest_frame_component_all':quantiles(components_all),
          'largest_frame_component_structural':quantiles(components_structural),
          'largest_component_structural_to_all':quantiles(component_ratios),
          'family_survival':{k:{'window':fam0[k],'selected':fam1[k],'fraction':fam1[k]/fam0[k] if fam0[k] else None,'missing_reason_counts':dict(sorted((why,cnt) for (name,why),cnt in missing.items() if name==k))} for k in sorted(fam0|fam1)}}
    mi=[]
    for (lens,cls),g in sorted(groups.items()):
        result=mi_image_level(g['values'],g['frames'],frame_labels,seed=1729,perms=999)
        mi.append({'lens':lens,'class':cls,'joint_MI':result})
        print('MI',lens,cls,result['n'],result['observed_bits'],result['p_one_sided'],flush=True)
    summary['ETH80_ALL8']['class_mi']={'scope':'128 object-disjoint evaluation frames; image-level label permutation',
       'classes':sorted(set(frame_labels)),'n_frames':len(frame_labels),'permutations':999,'groups':mi}
    write_json(ROOT/'phase3/results'/('build-census-'+a.pass_name+'.json'),summary)
    print('DONE',a.pass_name,flush=True)

if __name__=='__main__': main()
