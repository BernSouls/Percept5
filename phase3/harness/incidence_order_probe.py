"""Hash canonical incidence order for the pinned cup frame under a hash seed.

Run matrix_frames or nuisance_reconstruct first to restore the graph cache.
"""
from phase3.runtime.bootstrap import ROOT, activate, imported_product_paths
activate()
import hashlib, json, os
from phase3.harness.build_pairs import graph
from matching.structural_similarity import _incidence
from core.frontend_contract import frontend_contract, assert_live_contract

name = 'cup2-022-000.png'
paths = [ROOT/'.cache/joint-matrix'/(name+'.json'),
         ROOT/'.cache/nuisance-reconstructed'/(name+'.json'),
         ROOT/'.cache/build-measure/restored'/('ETH80_ALL8__'+name+'.json')]
p = next((path for path in paths if path.is_file()), None)
if p is None:
    raise FileNotFoundError('cup graph not restored; run phase3.harness.matrix_frames first')
r = json.loads(p.read_text())
expected = next(row['seed0'] for row in json.loads((ROOT/'phase3/results/build-determinism.json').read_text())['frame_comparison'] if row['corpus']=='ETH80_ALL8' and row['name']==name)
actual = hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
if actual != expected:
    raise ValueError('cup graph hash mismatch')
with frontend_contract():
    assert_live_contract(); imported_product_paths(); g, s = graph(r, 0); inc = _incidence(g, s)
x = [(n, [(v, e.name, o) for v, e, o in inc[n]]) for n in sorted(inc)]
print(json.dumps({'seed':os.getenv('PYTHONHASHSEED'),'sha256':hashlib.sha256(json.dumps(x).encode()).hexdigest(),'entries':sum(len(a) for _,a in x),'incident_nodes':len(x)},sort_keys=True))
