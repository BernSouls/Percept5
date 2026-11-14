"""Analysis-only re-presentation of saved ETH80 matrix; no matcher tuning.

Inputs must be hash-identical reconstructions. It derives node/edge counts,
centering and car/cup mechanisms, and preserves the original measurement.
"""
from phase3.runtime.bootstrap import ROOT, activate, imported_product_paths, write_json
activate()
import hashlib, json, math
from collections import Counter, defaultdict
from statistics import fmean
from phase3.harness.build_pairs import graph
from matching.joint_mcs import edge_key, edge_pair_credit
from core.frontend_contract import frontend_contract, assert_live_contract
from core.types import UNDIRECTED_EDGE_TYPES
from memory.cores import _sig_similarity


def corr(x, y):
    mx, my = fmean(x), fmean(y)
    xx = math.fsum((v-mx)**2 for v in x); yy = math.fsum((v-my)**2 for v in y)
    return math.fsum((a-mx)*(b-my) for a, b in zip(x, y)) / math.sqrt(xx*yy)


def main():
    saved = json.loads((ROOT/'phase3/results/joint-matrix-seed0.json').read_text())
    symmetry = json.loads((ROOT/'phase3/results/nuisance-symmetry.json').read_text())
    assert saved['complete'] and saved['errors'] == 0
    classes = saved['classes']; matrix = [[saved['cells'][a][b]['similarity'] for b in classes] for a in classes]
    rowmeans = [fmean(r) for r in matrix]; colmeans = [fmean(row[j] for row in matrix) for j in range(8)]; grand = fmean(rowmeans)
    centered = [[matrix[i][j]-rowmeans[i]-colmeans[j]+grand for j in range(8)] for i in range(8)]
    manifest = json.loads((ROOT/'phase3/inputs/eth80_all8.json').read_text())
    baseline = {r['name']:r['seed0'] for r in json.loads((ROOT/'phase3/results/build-determinism.json').read_text())['frame_comparison'] if r['corpus']=='ETH80_ALL8'}
    cache = ROOT/'.cache/nuisance-reconstructed'; data = {}; sizes = {}
    with frontend_contract():
        assert_live_contract(); imported_product_paths()
        for cls in classes:
            refs = [manifest['references'][cls]]; evals = manifest['eval'][cls]
            for r in refs+evals:
                name = r['path'].split('/')[-1]; rec = json.loads((cache/(name+'.json')).read_text())
                digest = hashlib.sha256(json.dumps(rec, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                if digest != baseline[name]: raise ValueError('hash mismatch '+name)
                if len(rec['selected_graph']['nodes']) != rec['selected_nodes'] or len(rec['selected_graph']['edges']) != rec['selected_edges']:
                    raise ValueError('selected count mismatch '+name)
                data[name] = rec
            ref = data[refs[0]['path'].split('/')[-1]]; views = [data[r['path'].split('/')[-1]] for r in evals]
            sizes[cls] = {'reference_frame':ref['name'],'reference_nodes':ref['selected_nodes'],'reference_edges':ref['selected_edges'],'heldout_nodes_mean':fmean(r['selected_nodes'] for r in views),'heldout_edges_mean':fmean(r['selected_edges'] for r in views),'heldout_edges_nodes_ratio_mean':fmean(r['selected_edges']/r['selected_nodes'] for r in views),'heldout_edges_min':min(r['selected_edges'] for r in views),'heldout_edges_max':max(r['selected_edges'] for r in views),'column_mean':colmeans[classes.index(cls)]}
            for v in views:
                matches=[p for p in saved['per_view'] if p['heldout_frame']==v['name']]
                assert len(matches)==8 and all(p['matched_nodes']+p['unmatched_heldout_nodes']==v['selected_nodes'] for p in matches)
    per_class = {}
    for i,c in enumerate(classes):
        best=max(range(8),key=lambda j:centered[i][j]); conf=max((j for j in range(8) if j!=i),key=lambda j:centered[i][j])
        per_class[c]={'diagonal_residual':centered[i][i], 'centered_argmax':classes[best], 'centered_argmax_value':centered[i][best], 'top_confuser':classes[conf], 'confuser_residual':centered[i][conf], 'diagonal_minus_rowmean':matrix[i][i]-rowmeans[i], 'diagonal_minus_colmean':matrix[i][i]-colmeans[i]}
    correlations={'column_mean_vs_heldout_nodes':corr(colmeans,[sizes[c]['heldout_nodes_mean'] for c in classes]),'column_mean_vs_heldout_edges':corr(colmeans,[sizes[c]['heldout_edges_mean'] for c in classes]),'column_mean_vs_heldout_edges_per_node':corr(colmeans,[sizes[c]['heldout_edges_nodes_ratio_mean'] for c in classes])}
    other=[c for c in classes if c!='cup']
    for metric in ('heldout_nodes_mean','heldout_edges_mean','heldout_edges_nodes_ratio_mean'):
        correlations['excluding_cup_column_mean_vs_'+metric]=corr([sizes[c]['column_mean'] for c in other],[sizes[c][metric] for c in other])
    # Average the eight reference comparisons for each image, then subtract
    # its class mean to check the association within classes as well.
    frame_values=[]
    for cls in classes:
        for rec in manifest['eval'][cls]:
            name=rec['path'].split('/')[-1]; frame=data[name]
            score=fmean(p['score'] for p in saved['per_view'] if p['heldout_frame']==name)
            frame_values.append({'class':cls,'score':score,'nodes':frame['selected_nodes'],'edges':frame['selected_edges'],'density':frame['selected_edges']/frame['selected_nodes']})
    for key in ('nodes','edges','density'):
        correlations['image_mean_score_vs_'+key]=corr([v['score'] for v in frame_values],[v[key] for v in frame_values])
        residual_score=[];residual_size=[]
        for c in classes:
            group=[v for v in frame_values if v['class']==c]; ms=fmean(v['score'] for v in group); mk=fmean(v[key] for v in group)
            residual_score.extend(v['score']-ms for v in group);residual_size.extend(v[key]-mk for v in group)
        correlations['within_class_image_mean_score_vs_'+key]=corr(residual_score,residual_size)
    # Reconstruct score attribution for saved assignments; no new optimization.
    mechanism = {}; refname=manifest['references']['car']['path'].split('/')[-1]; a,sa=graph(data[refname],0)
    for cls in ('car','cup'):
        sums=defaultdict(list); nodes=Counter(); edges=Counter(); nodecredits=Counter(); edgecredits=Counter()
        pairs=[p for p in saved['per_view'] if p['reference']=='car' and p['heldout_class']==cls]
        with frontend_contract():
            assert_live_contract(); imported_product_paths()
            for p in pairs:
                b,sb=graph(data[p['heldout_frame']],1<<80); mapping={u:v+(1<<80) for u,v in p['mapping']}
                b_und={(min(x,y),max(x,y),t) for x,y,t in b.edges if t in UNDIRECTED_EDGE_TYPES}
                b_dir={(x,y,t) for x,y,t in b.edges if t not in UNDIRECTED_EDGE_TYPES}
                numerator_nodes=[]; numerator_edges=[]; used=set()
                for u,v in sorted(mapping.items()):
                    assert sa[u][0]==sb[v][0]
                    value=_sig_similarity(sa[u][1],sb[v][1]); numerator_nodes.append(value); nodes[sa[u][0]]+=1; nodecredits[sa[u][0]]+=value
                for x,y,t in sorted(a.edges,key=edge_key):
                    u,v=mapping.get(x),mapping.get(y)
                    if u is None or v is None:continue
                    target=(min(u,v),max(u,v),t) if t in UNDIRECTED_EDGE_TYPES else (u,v,t)
                    if target not in (b_und if t in UNDIRECTED_EDGE_TYPES else b_dir) or target in used:continue
                    used.add(target); value=edge_pair_credit(a,b,x,y,u,v,t); numerator_edges.append(value); edges[t.name]+=1; edgecredits[t.name]+=value
                denom=len(a.nodes)+len(b.nodes)+len(a.edges)+len(b.edges)
                nodepart=2*math.fsum(numerator_nodes)/denom; edgepart=2*math.fsum(numerator_edges)/denom
                assert len(mapping)==p['matched_nodes'] and len(numerator_edges)==p['matched_edges'] and math.isclose(nodepart+edgepart,p['score'],rel_tol=0,abs_tol=1e-14)
                for key,val in [('node_score_component',nodepart),('edge_score_component',edgepart),('denominator',denom),('heldout_nodes',len(b.nodes)),('heldout_edges',len(b.edges)),('node_credit',math.fsum(numerator_nodes)),('edge_credit',math.fsum(numerator_edges))]: sums[key].append(val)
        n=len(pairs); mechanism[cls]={k:fmean(v) for k,v in sums.items()}
        mechanism[cls].update({'matched_node_lens_mean':{k:v/n for k,v in sorted(nodes.items())},'matched_edge_type_mean':{k:v/n for k,v in sorted(edges.items())},'edge_credit_by_type_mean':{k:v/n for k,v in sorted(edgecredits.items())},'matched_node_credit_by_lens_mean':{k:v/n for k,v in sorted(nodecredits.items())}})
    frame_sizes = {name: {'class':rec['label'], 'arm':rec['arm'], 'nodes':rec['selected_nodes'], 'edges':rec['selected_edges'], 'graph_sha256':baseline[name], 'source_sha256':rec['source_sha256']} for name,rec in sorted(data.items())}
    out={'source_sha256':hashlib.sha256((ROOT/'phase3/results/joint-matrix-seed0.json').read_bytes()).hexdigest(),'classes':classes,'matrix':matrix,'row_means':rowmeans,'column_means':colmeans,'grand_mean':grand,'centered_matrix':centered,'per_class':per_class,'sizes':sizes,'frame_sizes':frame_sizes,'correlations':correlations,'car_mechanism':mechanism,'symmetry':symmetry,'sign_counts':{'diagonal_above_rowmean':sum(per_class[c]['diagonal_minus_rowmean']>0 for c in classes),'diagonal_above_colmean':sum(per_class[c]['diagonal_minus_colmean']>0 for c in classes)},'hash_verified_frames':len(data)}
    write_json(ROOT/'phase3/results/nuisance-analysis.json',out)
    print('correlations',correlations,'signs',out['sign_counts']); print('sizes',sizes); print('mechanism',mechanism)

if __name__=='__main__': main()
