"""Write the nuisance-aware report from the saved analysis, without scoring."""
from phase3.runtime.bootstrap import ROOT,activate
activate()
import json

def main():
    x=json.loads((ROOT/'phase3/results/nuisance-analysis.json').read_text()); cs=x['classes']; z=x['centered_matrix']; sizes=x['sizes']; mechanism=x['car_mechanism']
    out=['# ETH80_ALL8: nuisance-aware analysis','',
         'This is a reanalysis of the existing matrix, not a new matcher or tuned score. The earlier raw report and full per-view records are preserved. All 136 selected graphs were reconstructed from the pinned images and verified against their original hashes; each extraction and fresh comparison asserted local product module paths and the live contract.','',
         '## 1. Same-pair symmetry','','| A (reference image) | B (held-out image) | S(A,B) | S(B,A) |','|---|---|---:|---:|']
    for p in x['symmetry']['pairs']:
        out.append(f"| {p['A']} | {p['B']} | {p['A_to_B']:.12f} | {p['B_to_A']:.12f} |")
    out += ['', 'All four scores are exactly equal on reversal and reproduce the original saved comparisons. The implementation evaluates both directional heuristic solves and takes the higher balanced score. Therefore, the apple→horse 0.5704 and horse→apple 0.4479 cells are different sets of images (a single object-1 reference in each row versus 16 object-2/3 views in each column), not a reversal of the same image pairs. The difference cannot be attributed specifically to viewing angle alone: object instance and reference/held-out roles also change.','',
        '## 2. Graph-size nuisance','','Selected graph sizes are the actual scorer inputs, not the full frontend window. Held-out columns contain 16 views. Column means average over eight reference classes.','',
        '| Class | Reference nodes | Reference edges | Held-out nodes, mean | Held-out edges, mean | Held-out edges/nodes, mean | Raw column mean |','|---|---:|---:|---:|---:|---:|---:|']
    for c in cs:
        s=sizes[c];out.append(f"| {c} | {s['reference_nodes']} | {s['reference_edges']} | {s['heldout_nodes_mean']:.2f} | {s['heldout_edges_mean']:.2f} | {s['heldout_edges_nodes_ratio_mean']:.3f} | {s['column_mean']:.6f} |")
    correlations=x['correlations']
    out+=['',f"Across these **eight class means**, the Pearson correlation of raw column mean with held-out mean nodes is {correlations['column_mean_vs_heldout_nodes']:+.3f}; with held-out mean edges it is {correlations['column_mean_vs_heldout_edges']:+.3f}; with mean edges/nodes it is {correlations['column_mean_vs_heldout_edges_per_node']:+.3f}. Cup’s column mean is {sizes['cup']['column_mean']:.6f}, pear’s is {sizes['pear']['column_mean']:.6f}: a spread of {sizes['pear']['column_mean']-sizes['cup']['column_mean']:.6f}, versus the raw diagonal-minus-off-diagonal mean of {sum(x['matrix'][i][i] for i in range(8))/8-sum(x['matrix'][i][j] for i in range(8) for j in range(8) if i!=j)/56:.6f}. These are descriptive, not independent samples or causal estimates.",
      '',f"Excluding cup, the class-mean correlations are {correlations['excluding_cup_column_mean_vs_heldout_nodes_mean']:+.3f} (nodes), {correlations['excluding_cup_column_mean_vs_heldout_edges_mean']:+.3f} (edges), and {correlations['excluding_cup_column_mean_vs_heldout_edges_nodes_ratio_mean']:+.3f} (edges/nodes). At the 128-view level, averaging the eight reference scores for each view and subtracting each class mean, the pooled within-class correlations are {correlations['within_class_image_mean_score_vs_nodes']:+.3f} (nodes), {correlations['within_class_image_mean_score_vs_edges']:+.3f} (edges), and {correlations['within_class_image_mean_score_vs_density']:+.3f} (edges/nodes). Views share references and objects; these are descriptive associations, not independent tests.",
      '', 'The raw column pattern is strongly associated with graph richness, especially edge density, and should not be interpreted as a pure shape similarity ranking. The score denominator counts nodes and edges from both graphs, while its numerator includes only matched, credited elements. Correlation alone cannot establish that graph size causes the column spread or that the matrix measures only richness rather than shape; class, viewpoint, edge density and detector behavior are entangled. Double-centering removes additive row and column averages, not all size, pose, object, or interaction effects.','',
      '## 3. Double-centered matrix','',f"`D[i,j] = M[i,j] − row_mean[i] − column_mean[j] + grand_mean`, with grand mean {x['grand_mean']:.9f}. Each row and column sums to approximately zero. These residuals are not probabilities or calibrated similarities.",'', '| Reference \\ held-out | '+' | '.join(cs)+' |','|'+'---|'*9]
    for i,c in enumerate(cs):out.append('| '+c+' | '+' | '.join(f'{v:+.4f}' for v in z[i])+' |')
    out+=['','| Class | Diagonal residual | Centered row argmax | Best off-diagonal | Its residual |','|---|---:|---|---|---:|']
    for c in cs:
        p=x['per_class'][c];out.append(f"| {c} | {p['diagonal_residual']:+.6f} | {p['centered_argmax']} | {p['top_confuser']} | {p['confuser_residual']:+.6f} |")
    out+=['','Cup has the largest diagonal residual (+0.175114), reversing the impression from its low raw diagonal. Car is the only negative diagonal residual. Centered row argmax is correct for cup, horse, pear and tomato; apple, car, cow and dog have a higher off-diagonal residual. These are within-matrix associations, not a generalization test.','',
       '## 4. Why car → cup?','',
       'Car→cup is the largest centered car-row residual even though its raw score is lower than car→car. The cup column is unusually low against *all* references; subtracting that column baseline produces the inversion. This is not evidence by itself that a car and cup have the same shape.','',
       '| Car reference compared with | Raw score | Centered residual | Matched nodes, mean | Matched edges, mean | Graded edge similarity | Node score component | Edge score component |','|---|---:|---:|---:|---:|---:|---:|---:|']
    i=cs.index('car')
    for c in ('car','cup'):
        j=cs.index(c);p=x['per_class']['car'];m=mechanism[c]
        # Metrics already computed in original per-view records.
        orig=json.loads((ROOT/'phase3/results/joint-matrix-seed0.json').read_text())['cells']['car'][c]
        out.append(f"| {c} | {orig['similarity']:.6f} | {z[i][j]:+.6f} | {orig['matched_nodes_mean']:.2f} | {orig['matched_edges_mean']:.2f} | {orig['mean_graded_edge_similarity']:.6f} | {m['node_score_component']:.6f} | {m['edge_score_component']:.6f} |")
    rawgap=x['matrix'][i][cs.index('cup')]-x['matrix'][i][i]; adj=x['column_means'][i]-x['column_means'][cs.index('cup')]; centeredgap=z[i][cs.index('cup')]-z[i][i]
    out+=['',f'The raw cup-minus-car gap in that row is {rawgap:+.6f}; column-centering adds {adj:+.6f}, yielding a centered gap of {centeredgap:+.6f}. The score components above are the original numerator contributions after both-side normalization; they sum to the cell score. Matched edges include presence-only and graded relations.','']
    for c in ('car','cup'):
        m=mechanism[c]; top=sorted(m['matched_edge_type_mean'].items(),key=lambda v:-v[1])[:5]; lens=sorted(m['matched_node_lens_mean'].items(),key=lambda v:-v[1])[:4]
        out.append(f"- Car→{c}: largest matched edge types per comparison: "+', '.join(f'{name} {n:.2f}' for name,n in top)+'; largest matched node lenses: '+', '.join(f'{name} {n:.2f}' for name,n in lens)+'.')
    out+=['','`CONTOUR_ORIENTATION` is an index-only membership relation, not a continuous physical measurement: its average credited presence rises from 8.44 for car→car to 14.12 for car→cup. The cup comparisons thus preserve more generic contour/orientation membership, but their normalized node contribution is much lower. Their mean score denominator is 1,121.06 versus 1,018.31 for car→car. This breakdown shows what relations and node families are reused; without an object-role ground truth it does not establish that they correspond to car or cup parts.','',
        '## 5. Diagonal sign checks','','For each class, compare its raw diagonal cell to its own raw row or column mean (including the diagonal):','',
        '| Class | Diagonal − row mean | Diagonal − column mean |','|---|---:|---:|']
    for c in cs:
        p=x['per_class'][c];out.append(f"| {c} | {p['diagonal_minus_rowmean']:+.6f} | {p['diagonal_minus_colmean']:+.6f} |")
    out+=['',f"Diagonal exceeds its row mean for **{x['sign_counts']['diagonal_above_rowmean']}/8** classes and its column mean for **{x['sign_counts']['diagonal_above_colmean']}/8** classes (car is the exception). Under an independent fair-sign null, the nominal two-sided exact binomial values are 0.0078125 and 0.0703125, respectively. They should not be interpreted as validated significance: matrix cells share reference and held-out graphs, so independence is not established.",'',
          'Full unrounded results, frame sizes and hashes: `results/nuisance-analysis.json`; pair-order measurements: `results/nuisance-symmetry.json`. Reproduction scripts are `harness/nuisance_reconstruct.py`, `harness/nuisance_symmetry.py`, `harness/nuisance_analysis.py`, and `harness/nuisance_report.py`. Original matrix: `ETH80_JOINT_MCS_MATRIX.md`.']
    (ROOT/'phase3/ETH80_NUISANCE_ANALYSIS.md').write_text('\n'.join(out)+'\n')
    print('wrote phase3/ETH80_NUISANCE_ANALYSIS.md')
if __name__=='__main__': main()
