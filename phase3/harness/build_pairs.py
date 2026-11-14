"""Renderer role-oracle and returned fuzzy alignment, separate corpus only.

The truth denominator is the sum of min role counts on the two sides.
Nodes without known object positions are unscorable and explicitly counted;
all solver pairs remain in the precision denominator (conservative).
The canonical role-compatible truth mapping is not a claimed unique truth.
The product solver is bounded/heuristic: its return is not certified optimal.
"""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, write_json, provenance
activate()
import argparse,json,time,traceback
from collections import defaultdict
import parameters as P
from core.types import TypedSignature, EdgeType
from core.schema import EdgeParams, EdgeParamsMixture
from core.graph_types import Subgraph
from core.graded_features import NamedFeature,with_features
from core.frontend_contract import frontend_contract, assert_live_contract
from matching.fuzzy import fuzzy_match, _edge_param_mean
from matching.structural_similarity import _sig_sim
from matching.alignment import build_incidence,_edge_indexes,_relational_agreement,systematicity
from matching.calibration import NullModel
from phase3.harness.metrics import quantiles


def sig(d):
    s=TypedSignature(kind=d['kind'],class_=d['class'],relation=d['relation'],type_tag=d['type_tag'],hash_value=d['hash_value'],quantized=tuple(d['quantized']),population=tuple(tuple(x) for x in d['population']))
    fs=[NamedFeature(f['name'],f['source_lens'],sig(f['signature']),tuple(tuple(x) for x in f['attachment'])) for f in d['features']]
    return with_features(s,fs) if fs else s


def edge_parameter(raw):
    if raw is None:
        return None
    if 'protos' in raw:
        return EdgeParamsMixture([edge_parameter(p) for p in raw['protos']], list(raw['mass']), raw['t_last'])
    if 'class_' not in raw:
        raise ValueError('unrecognized recorded edge parameter')
    d=raw.copy();d['quantized']=tuple(d['quantized']);d['population']=tuple(tuple(v) for v in d.get('population',()))
    if d.get('identity_slots') is not None:d['identity_slots']=tuple(d['identity_slots'])
    return EdgeParams(**d)


def graph(row,offset):
    infos={n['id']+offset:(n['lens'],sig(n['sig'])) for n in row['selected_graph']['nodes']}
    edges=[]; params={};weights={}
    for x in row['selected_graph']['edges']:
        e=(x['a']+offset,x['b']+offset,EdgeType[x['type']]);edges.append(e);weights[e]=x['weight']
        ep=edge_parameter(x['params'])
        if ep is not None: params[e]=ep
    return Subgraph(nodes=frozenset(infos),edges=frozenset(edges),edge_params=params,weights=weights),infos


def roles(row, scene, offset):
    result={};stats=defaultdict(int); labels=scene['labels'];h=len(labels);w=len(labels[0])
    for n in row['selected_graph']['nodes']:
        pos=n['position']
        if pos is None or len(pos)<2:
            stats['missing_position']+=1;continue
        x,y=round(pos[0]),round(pos[1])
        if not (0<=x<w and 0<=y<h): stats['outside_image']+=1;continue
        obj=labels[y][x]
        if obj=='background':stats['background']+=1;continue
        result[n['id']+offset]=(obj,n['lens'],n['sig']['class']);stats['object_roles']+=1
    return result,dict(stats)


def truth_map(ra,rb):
    ga,gb=defaultdict(list),defaultdict(list)
    for n,r in ra.items():ga[r].append(n)
    for n,r in rb.items():gb[r].append(n)
    pairs={}
    for role in sorted(ga.keys() & gb.keys()):
        pairs.update(zip(sorted(ga[role]),sorted(gb[role])))
    return pairs


def objective(a,b,infos,mapping):
    na,nb=sorted(a.nodes),sorted(b.nodes)
    matrix=[[_sig_sim(infos[u][1],infos[v][1]) for v in nb] for u in na]
    alternatives=[matrix[i][j] for i,u in enumerate(na) for j,v in enumerate(nb) if mapping.get(u)!=v]
    chance=sum(alternatives)/len(alternatives) if alternatives else 0.
    ia,ib=build_incidence(a.edges),build_incidence(b.edges)
    ad,au=_edge_indexes(a.edges);bd,bu=_edge_indexes(b.edges);rev={v:u for u,v in mapping.items()}
    beta=float(P.MATCH_SYSTEMATICITY_WEIGHT);q=[]
    for u,v in sorted(mapping.items()):
        rel=_relational_agreement(u,v,mapping,ia,ib,bd,bu,ad,au,rev) if a.edges or b.edges else 1.
        q.append(_sig_sim(infos[u][1],infos[v][1])*(1-beta+beta*rel))
    coverage=2*sum(q)/(len(na)+len(nb)) if na or nb else 0.
    node=NullModel(chance).calibrate(coverage)
    if not alternatives and na and nb:node*=.5
    _,fwd,bwd=systematicity(mapping,a.edges,b.edges)
    ep=_edge_param_mean(a,b,mapping,False)
    edge=(fwd+bwd)*.5*ep
    score=node if not a.edges and not b.edges else node*((1-P.MATCH_EDGE_WEIGHT)+P.MATCH_EDGE_WEIGHT*edge)
    return {'score':score,'chance':chance,'node_calibrated':node,'edge_term':edge,'mapping_size':len(mapping)}


def rates(tp,pred,truth):
    p=tp/pred if pred else None;r=tp/truth if truth else None
    f=(2*p*r/(p+r) if p is not None and r is not None and p+r else 0. if p is not None and r is not None else None)
    return {'tp':tp,'predicted':pred,'truth_denominator':truth,'precision':p,'recall':r,'f1':f}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pass-name',required=True);args=ap.parse_args()
    root=ROOT/'.cache/build-measure'/args.pass_name
    idx=json.loads((root/'index.json').read_text())['records']; lookup={r['name']:r for r in idx if r['corpus']=='RENDERER_TRUTH_V1'}
    truth=json.loads((ROOT/'data/renderer-truth-v1/truth.json').read_text());scenes={s['name']:s for s in truth['scenes']}
    rows=[]
    for x,y in truth['pairs']:
        try:
            if x not in lookup or y not in lookup or lookup[x]['error'] or lookup[y]['error']:raise RuntimeError('missing or failed frame')
            rx=json.loads((ROOT/lookup[x]['path']).read_text());ry=json.loads((ROOT/lookup[y]['path']).read_text())
            a,sa=graph(rx,0);b,sb=graph(ry,1<<80);infos={**sa,**sb}
            ra,da=roles(rx,scenes[x],0);rb,db=roles(ry,scenes[y],1<<80);tm=truth_map(ra,rb)
            t=time.monotonic()
            with frontend_contract():
                assert_live_contract(); result=fuzzy_match(a,b,infos.get)
            elapsed=time.monotonic()-t
            tp=sum(1 for u,v in result.mapping.items() if u in ra and v in rb and ra[u]==rb[v])
            with frontend_contract(): truth_objective=objective(a,b,infos,tm)
            rows.append({'pair':[x,y],'solver':rates(tp,len(result.mapping),len(tm)),
                'truth':rates(len(tm),len(tm),len(tm)), 'truth_objective':truth_objective,
                'returned_solver_objective':result.score,'solver_budget_exhausted':result.budget_exhausted,
                'solver_vs_truth_objective':result.score-truth_objective['score'],
                'solver_mapping':sorted([u,v-(1<<80)] for u,v in result.mapping.items()),
                'role_availability':{'a':da,'b':db},'match_seconds':elapsed,'error':None})
            print('pair',x,y,'seconds',round(elapsed,3),'P/R/F',rows[-1]['solver'],'objective truth/returned',truth_objective['score'],result.score,flush=True)
        except Exception as e:
            rows.append({'pair':[x,y],'error':str(e),'traceback':traceback.format_exc()});print('ERROR',x,y,e,flush=True)
        write_json(ROOT/'phase3/results'/('build-pairs-'+args.pass_name+'.json'),{'corpus':'RENDERER_TRUTH_V1','pairs':rows})
    good=[r for r in rows if not r['error']]
    timing=quantiles([r['match_seconds'] for r in good])
    micro=rates(sum(r['solver']['tp'] for r in good),sum(r['solver']['predicted'] for r in good),sum(r['solver']['truth_denominator'] for r in good))
    canonical=[{k:v for k,v in row.items() if k not in ('match_seconds','traceback')} for row in rows]
    write_json(ROOT/'phase3/results'/('build-pairs-'+args.pass_name+'.json'),{'corpus':'RENDERER_TRUTH_V1','pairs':rows,'micro':micro,'match_seconds':timing,'runtime_pass':bool(good) and timing['p95']<=1. and timing['max']<=3.,'error_count':len(rows)-len(good),'interpretation':'Truth role equivalence, canonical representative; unknown positions excluded from truth but retained in precision denominator. Returned solver result is not a proof of global optimum.','canonical_without_timing':canonical})
    write_json(root/'pairs-provenance.json',provenance('phase3/harness/build_pairs.py',['matching.fuzzy','matching.alignment','phase3.harness.frontend']))
    print('DONE',micro,timing,flush=True)
if __name__=='__main__':main()
