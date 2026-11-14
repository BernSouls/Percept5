"""Render the fixed joint matrix and its mechanism matrices without recomputation."""
from phase3.runtime.bootstrap import ROOT,activate
activate()
import hashlib,json

def main():
    files=[ROOT/'phase3/results'/('joint-matrix-'+seed+'.json') for seed in ('seed0','seed1729')]
    content=[p.read_bytes() for p in files];hashes=[hashlib.sha256(b).hexdigest() for b in content]
    a,b=map(json.loads,content);integrity=json.loads((ROOT/'phase3/results/joint-matrix-input-integrity.json').read_text())
    guard=json.loads((ROOT/'phase3/results/joint-matrix-postguard-verification.json').read_text())
    assert a['complete'] and a['errors']==0 and len(a['per_view'])==1024
    assert integrity['frames']==136 and integrity['reverse_duplicates']==0 and guard['all_equal']
    cs=a['classes'];out=['# ETH80_ALL8 joint graded MCS matrix','','> **Analysis correction:** Raw scores have a strong graph-size/density nuisance. See [the nuisance-aware reanalysis](ETH80_NUISANCE_ANALYSIS.md) for same-pair symmetry, sizes and the double-centered matrix. The original results below are retained unchanged.','',
      'Rows are reference-class graphs; columns are held-out classes, averaged over 16 views. Each cell is a direct two-graph comparison, with no discriminative filter, positive/negative training, or learned weights. Rows and columns use different images, so the displayed matrix need not be symmetric even though each pair score is symmetric.','',
      f"**Diagonal mean: {a['summary']['diagonal_mean']:.6f}. Off-diagonal mean: {a['summary']['off_diagonal_mean']:.6f}.** The mean diagonal is higher, but the diagonal is not the row maximum for apple, car, cow, cup, or dog; horse is ahead of its closest off-diagonal by only 0.00000846.",'']
    def table(title,key,fmt):
        out.extend(['## '+title,'','| Reference \\ held-out | '+' | '.join(cs)+' |','|'+'---|'*(len(cs)+1)])
        for c in cs:out.append('| '+c+' | '+' | '.join(fmt(a['cells'][c][d][key]) for d in cs)+' |')
        out.append('')
    table('Similarity','similarity',lambda x:f'{x:.4f}')
    out+=['## Per-class diagonal margin','','| Reference | Diagonal | Best off-diagonal class | Best off-diagonal | Margin |','|---|---:|---|---:|---:|']
    for c in cs:
        best=max((j for j in cs if j!=c),key=lambda j:a['cells'][c][j]['similarity']);v=a['cells'][c]
        out.append(f"| {c} | {v[c]['similarity']:.6f} | {best} | {v[best]['similarity']:.6f} | {a['summary']['per_class_margin'][c]:+.8f} |")
    out+=['','## Mechanism per class pair','','Counts are means per comparison, not totals. Graded edge similarity is pooled across matched edges with at least one shared measured graded axis; presence-only edges are excluded from that mean. The JSON includes both graded and presence-only denominators.','']
    table('Matched nodes, mean','matched_nodes_mean',lambda x:f'{x:.1f}')
    table('Matched edges, mean','matched_edges_mean',lambda x:f'{x:.1f}')
    table('Mean graded edge similarity','mean_graded_edge_similarity',lambda x:'—' if x is None else f'{x:.4f}')
    out+=['## Score and verification','',
        'The registered score is `2 × (sum matched-node similarity + sum matched-edge credit) / (nodes_A + nodes_B + edges_A + edges_B)`. Same-type edges with comparable parameters receive their graded similarity; missing-parameter or identity-only relations contribute presence, not an invented graded measurement. Both directional bounded Hungarian/refinement solves are tried, and the larger balanced score is retained. This is an approximation, not a proof of a global maximum. Existing `mcs_similarity` was not used because it has binary node credit and axis-count edge facilitation.','',
        'The live matcher bypasses the deprecated supervised filter, uses the unfiltered selected reference graph, and has `MATCH_GLOBAL_CONSISTENCY_ENABLED=True`. Relations enter the reassignment weights. A constructed product-path test changes the mapping when one edge is removed, not merely the final score; 1,024/1,024 returned mappings were one-to-one. The 1,024 selected results reported zero alignment budget exhaustions.','',
        f'Both independent seed runs completed 1,024 comparisons with zero errors; result SHA-256: seed 0 `{hashes[0]}`, seed 1729 `{hashes[1]}`. **'+('Byte-identical.**' if content[0]==content[1] else 'NOT byte-identical.**')+' Both scoring runs used the same hash-verified reconstructed graphs; this is not a second independent graph extraction. All 136 reconstructed graph hashes matched the earlier selected-frame records, and the earlier independent 151-frame extraction matched across seeds. The 508-entry incidence probe also matched under both seeds: `4932c30f0f3ac44ab88811dd844181b156f2cfe7b0dfa53f701adc7fc0c93691`.','',
        'The explicit edge-reuse guard was added during the sweep. All 136 measured graphs contain zero reverse-duplicate undirected edges, so it does not change any measured edge correspondence; one diagonal comparison per class was independently rerun against the final code and all eight matched exactly.','',
        'Regression: 540 tests passed. Tests of `_content_discriminative_filter` or its supervised behaviour remain in the tree as deprecated-path tests, not evidence about the live matcher. The score form and corpus were registered before matrix scoring; no matrix-driven tuning was performed. Full per-view mappings, counts, and denominators are in `results/joint-matrix-seed0.json` and its seed-1729 repeat; the protocol is `audit/joint-mcs-protocol.json`.']
    path=ROOT/'phase3/ETH80_JOINT_MCS_MATRIX.md';path.write_text('\n'.join(out)+'\n');print(path)
if __name__=='__main__':main()
