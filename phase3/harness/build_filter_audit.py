"""Registered eight-class filter audit from the already measured selected graphs.

Fits on 16 object-disjoint eval frames per class, contrasts against 112 other
class frames, and reports descriptive in-sample evidence; it is not an
independent generalization estimate. No frontend extraction is repeated.
"""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT,activate,write_json
activate()
import argparse,json,time,traceback,math
from collections import defaultdict
import parameters as P
from core.frontend_contract import frontend_contract
from phase3.harness.build_pairs import graph
from memory.content import ContentSignatureStore,build_content_subgraph
from memory.distributions import _wilson_min_recurrence
from matching.structural_similarity import structural_intersection,materialize_template,select_template_exemplar
from consolidator import _content_discriminative_filter
from memory.cores import evidence_score


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pass-name',required=True);a=ap.parse_args()
    root=ROOT/'.cache/build-measure'/a.pass_name;index=json.loads((root/'index.json').read_text())['records']
    recs=[r for r in index if r['corpus']=='ETH80_ALL8' and r['arm']=='eval' and not r['error']]
    if len(recs)!=128:raise RuntimeError('expected all 128 held-out input frames')
    with frontend_contract():
        store=ContentSignatureStore();graphs=[]
        for i,r in enumerate(recs):
            raw=json.loads((ROOT/r['path']).read_text());sg,sigs=graph(raw,i<<80)
            try:
                cg=build_content_subgraph(sg,sigs.get,store,{})
            except Exception as exc:
                write_json(ROOT/'phase3/results'/('build-filter-'+a.pass_name+'.json'),
                           {'corpus':'ETH80_ALL8','status':'FAILED during content pooling',
                            'processed_frames':i,'failed_class':r['label'],'failed_frame':r['name'],
                            'error':str(exc),'traceback':traceback.format_exc(),'classes':[]})
                print('FILTER FAILED',i,r['label'],r['name'],str(exc),flush=True)
                raise
            graphs.append((r['label'],r['name'],cg))
            if (i+1)%16==0:print('content',i+1,'/',len(recs),'store',store.size(),flush=True)
        rows=[]
        for cls in sorted({x[0] for x in graphs}):
            t=time.monotonic()
            try:
                pos=[g for c,n,g in graphs if c==cls];neg=[g for c,n,g in graphs if c!=cls]
                nmin=_wilson_min_recurrence(len(pos),len(neg));diag={}
                templ=structural_intersection(pos,store.get,min_frequency=nmin/len(pos),n_neg=len(neg),diag=diag)
                if templ is None:
                    rows.append({'class':cls,'template_nodes':0,'template_edges':0,'core_nodes':0,'core_edges':0,'error':None,'scores_available':False});continue
                ex=select_template_exemplar(pos);core=materialize_template(templ,ex,store.get)
                filt,fd,_=_content_discriminative_filter(core,pos,neg,store.get,theta_disc_norm=P.THETA_DISC_NORM,theta_pos_min=P.THETA_POS_MIN_CONTENT,pool_sigma_floor=P.POOL_SIGMA_FLOOR)
                cs={n:store.get(n) for n in filt.nodes if store.get(n)}
                def score(g):
                    qs={n:store.get(n) for n in g.nodes if store.get(n)}
                    return evidence_score(g,filt,qs,cs)[0]
                ps=[score(g) for g in pos];ns=[score(g) for g in neg]
                rows.append({'class':cls,'positives':len(pos),'negatives':len(neg),'wilson_min_recurrence':nmin,
                    'template_nodes':len(templ.nodes),'template_edges':len(templ.edges),'materialized_nodes':len(core.nodes),'materialized_edges':len(core.edges),
                    'core_nodes':len(filt.nodes),'core_edges':len(filt.edges),'positive_mean':math.fsum(ps)/len(ps),'negative_mean':math.fsum(ns)/len(ns),
                    'positive_gt_negative':math.fsum(ps)/len(ps)>math.fsum(ns)/len(ns),
                    'real_edge_criterion':len(filt.edges)>0 if templ.edges else None,
                    'diagnostics':{k:v for k,v in fd.items() if isinstance(v,(int,float,bool,str)) or v is None},'error':None,'scores_available':True})
                print('filter',cls,'template edges',len(templ.edges),'core edges',len(filt.edges),'means',rows[-1]['positive_mean'],rows[-1]['negative_mean'],'seconds',round(time.monotonic()-t,2),flush=True)
            except Exception as exc:
                rows.append({'class':cls,'error':str(exc),'traceback':traceback.format_exc()});print('ERROR',cls,exc,flush=True)
            write_json(ROOT/'phase3/results'/('build-filter-'+a.pass_name+'.json'),{'corpus':'ETH80_ALL8','scope':'16 eval frames per class used as positives; in-sample scores','classes':rows})
        write_json(ROOT/'phase3/results'/('build-filter-'+a.pass_name+'.json'),{'corpus':'ETH80_ALL8','scope':'16 eval frames per class used as positives; in-sample scores','classes':rows})
if __name__=='__main__':main()
