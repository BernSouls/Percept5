"""Reconstruct pinned matrix inputs, validating each original graph hash.

Two independent shards may run concurrently. Graphs are disposable cache;
no score or matcher parameters are modified. Each frame asserts provenance.
"""
from phase3.runtime.bootstrap import ROOT, activate, imported_product_paths, write_json
activate()
import argparse, gc, hashlib, json, traceback
from phase3.harness.frontend import read_rgb, run_frame
from phase3.harness.build_measure import capture
from core.frontend_contract import frontend_contract, assert_live_contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shard', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'phase3/inputs/eth80_all8.json').read_text())
    rows = [('reference', c, r) for c, r in sorted(manifest['references'].items())]
    evaluations = [('eval', c, r) for c, rs in sorted(manifest['eval'].items()) for r in rs]
    # The four pairs needed for the order check and car/cup inspection come first.
    evaluations.sort(key=lambda row: (0 if row[1] in ('apple', 'horse', 'car', 'cup') and row[2]['path'].endswith('2-022-000.png') else 1, row[1], row[2]['path']))
    rows.extend(evaluations)
    baseline = json.loads((ROOT / 'phase3/results/build-determinism.json').read_text())['frame_comparison']
    expected = {r['name']: r['seed0'] for r in baseline if r['corpus'] == 'ETH80_ALL8'}
    root = ROOT / '.cache/nuisance-reconstructed'
    root.mkdir(parents=True, exist_ok=True)
    errors = []
    for i, (arm, cls, rec) in enumerate(rows):
        if i % 2 != args.shard:
            continue
        name = rec['path'].split('/')[-1]
        try:
            image = ROOT / rec['path']
            if hashlib.sha256(image.read_bytes()).hexdigest() != rec['sha256']:
                raise ValueError('source image hash mismatch')
            with frontend_contract():
                assert_live_contract(); imported_product_paths()
                frame = run_frame(read_rgb(image), name)
                result = capture(frame, 'ETH80_ALL8', arm, cls, rec)
            digest = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            if digest != expected[name]:
                raise ValueError(f'original graph hash mismatch: {digest} != {expected[name]}')
            write_json(root / (name + '.json'), result)
            print(args.shard, i + 1, '/136', name, 'nodes', result['selected_nodes'], 'edges', result['selected_edges'], 'hash OK', flush=True)
            del frame, result
            gc.collect()
        except Exception as exc:
            errors.append({'name': name, 'error': str(exc), 'traceback': traceback.format_exc()})
            print('ERROR', name, repr(exc), flush=True)
    write_json(root / f'shard-{args.shard}-errors.json', errors)
    if errors:
        raise RuntimeError(f'{len(errors)} reconstruction errors')
    print('DONE shard', args.shard, flush=True)

if __name__ == '__main__':
    main()
