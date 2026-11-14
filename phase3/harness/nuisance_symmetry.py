"""Same-image-pair order check against the original saved matrix comparisons."""
from phase3.runtime.bootstrap import ROOT, activate, imported_product_paths, write_json
activate()
import json, hashlib
from phase3.harness.build_pairs import graph
from core.frontend_contract import frontend_contract, assert_live_contract
from matching.joint_mcs import joint_mcs


def main():
    root = ROOT / '.cache/nuisance-reconstructed'
    manifest = json.loads((ROOT / 'phase3/inputs/eth80_all8.json').read_text())
    original = json.loads((ROOT / 'phase3/results/joint-matrix-seed0.json').read_text())
    baseline = {r['name']: r['seed0'] for r in json.loads((ROOT / 'phase3/results/build-determinism.json').read_text())['frame_comparison'] if r['corpus'] == 'ETH80_ALL8'}
    cases = [('apple', 'horse'), ('horse', 'apple'), ('car', 'cup'), ('car', 'car')]
    out = []
    for ref, held in cases:
        name_a = manifest['references'][ref]['path'].split('/')[-1]
        name_b = next(r['path'].split('/')[-1] for r in manifest['eval'][held] if r['path'].endswith('2-022-000.png'))
        records = [json.loads((root / (name + '.json')).read_text()) for name in (name_a, name_b)]
        for name, record in zip((name_a, name_b), records):
            digest = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            if digest != baseline[name]:
                raise ValueError('graph hash mismatch ' + name)
        a, sa = graph(records[0], 0); b, sb = graph(records[1], 1 << 80)
        with frontend_contract():
            assert_live_contract(); imported_product_paths(); ab = joint_mcs(a, b, sa, sb)
        with frontend_contract():
            assert_live_contract(); imported_product_paths(); ba = joint_mcs(b, a, sb, sa)
        prior = next(r['score'] for r in original['per_view'] if r['reference'] == ref and r['heldout_frame'] == name_b)
        out.append({'reference_class': ref, 'heldout_class': held, 'A': name_a, 'B': name_b, 'A_to_B': ab.score, 'B_to_A': ba.score, 'difference': ab.score-ba.score, 'original_score': prior, 'reproduces_original': ab.score == prior, 'exactly_symmetric': ab.score == ba.score})
        print(out[-1], flush=True)
    write_json(ROOT / 'phase3/results/nuisance-symmetry.json', {'pairs': out, 'all_original_scores_reproduced': all(x['reproduces_original'] for x in out), 'all_exactly_symmetric': all(x['exactly_symmetric'] for x in out)})
    if not all(x['reproduces_original'] and x['exactly_symmetric'] for x in out):
        raise RuntimeError('symmetry or original reproduction failed; inspect results')

if __name__ == '__main__':
    main()
