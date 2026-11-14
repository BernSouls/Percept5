# ETH80_ALL8: nuisance-aware analysis

This is a reanalysis of the existing matrix, not a new matcher or tuned score. The earlier raw report and full per-view records are preserved. All 136 selected graphs were reconstructed from the pinned images and verified against their original hashes; each extraction and fresh comparison asserted local product module paths and the live contract.

## 1. Same-pair symmetry

| A (reference image) | B (held-out image) | S(A,B) | S(B,A) |
|---|---|---:|---:|
| apple1-000-000.png | horse2-022-000.png | 0.575082192521 | 0.575082192521 |
| horse1-000-000.png | apple2-022-000.png | 0.437289287381 | 0.437289287381 |
| car1-000-000.png | cup2-022-000.png | 0.355945658685 | 0.355945658685 |
| car1-000-000.png | car2-022-000.png | 0.480952433943 | 0.480952433943 |

All four scores are exactly equal on reversal and reproduce the original saved comparisons. The implementation evaluates both directional heuristic solves and takes the higher balanced score. Therefore, the apple→horse 0.5704 and horse→apple 0.4479 cells are different sets of images (a single object-1 reference in each row versus 16 object-2/3 views in each column), not a reversal of the same image pairs. The difference cannot be attributed specifically to viewing angle alone: object instance and reference/held-out roles also change.

## 2. Graph-size nuisance

Selected graph sizes are the actual scorer inputs, not the full frontend window. Held-out columns contain 16 views. Column means average over eight reference classes.

| Class | Reference nodes | Reference edges | Held-out nodes, mean | Held-out edges, mean | Held-out edges/nodes, mean | Raw column mean |
|---|---:|---:|---:|---:|---:|---:|
| apple | 393 | 100 | 326.56 | 167.31 | 0.518 | 0.496416 |
| car | 316 | 197 | 385.62 | 119.69 | 0.309 | 0.541521 |
| cow | 341 | 57 | 342.00 | 82.56 | 0.243 | 0.559577 |
| cup | 244 | 185 | 288.69 | 319.38 | 1.104 | 0.358083 |
| dog | 323 | 57 | 333.19 | 152.88 | 0.459 | 0.515899 |
| horse | 314 | 47 | 351.19 | 80.56 | 0.227 | 0.563311 |
| pear | 325 | 76 | 350.19 | 86.94 | 0.251 | 0.563589 |
| tomato | 424 | 140 | 391.56 | 138.75 | 0.355 | 0.526619 |

Across these **eight class means**, the Pearson correlation of raw column mean with held-out mean nodes is +0.716; with held-out mean edges it is -0.995; with mean edges/nodes it is -0.998. Cup’s column mean is 0.358083, pear’s is 0.563589: a spread of 0.205506, versus the raw diagonal-minus-off-diagonal mean of 0.056496. These are descriptive, not independent samples or causal estimates.

Excluding cup, the class-mean correlations are +0.218 (nodes), -0.987 (edges), and -0.984 (edges/nodes). At the 128-view level, averaging the eight reference scores for each view and subtracting each class mean, the pooled within-class correlations are +0.059 (nodes), -0.822 (edges), and -0.847 (edges/nodes). Views share references and objects; these are descriptive associations, not independent tests.

The raw column pattern is strongly associated with graph richness, especially edge density, and should not be interpreted as a pure shape similarity ranking. The score denominator counts nodes and edges from both graphs, while its numerator includes only matched, credited elements. Correlation alone cannot establish that graph size causes the column spread or that the matrix measures only richness rather than shape; class, viewpoint, edge density and detector behavior are entangled. Double-centering removes additive row and column averages, not all size, pose, object, or interaction effects.

## 3. Double-centered matrix

`D[i,j] = M[i,j] − row_mean[i] − column_mean[j] + grand_mean`, with grand mean 0.515627073. Each row and column sums to approximately zero. These residuals are not probabilities or calibrated similarities.

| Reference \ held-out | apple | car | cow | cup | dog | horse | pear | tomato |
|---|---|---|---|---|---|---|---|---|
| apple | +0.0258 | -0.0139 | -0.0199 | +0.0119 | -0.0093 | -0.0238 | -0.0146 | +0.0437 |
| car | +0.0185 | -0.0072 | -0.0192 | +0.0547 | +0.0141 | -0.0278 | -0.0413 | +0.0082 |
| cow | -0.0354 | +0.0251 | +0.0338 | -0.0728 | +0.0095 | +0.0388 | +0.0226 | -0.0216 |
| cup | +0.0688 | -0.0525 | -0.0643 | +0.1751 | -0.0094 | -0.0688 | -0.0541 | +0.0053 |
| dog | -0.0402 | +0.0261 | +0.0336 | -0.0668 | +0.0181 | +0.0411 | +0.0189 | -0.0308 |
| horse | -0.0487 | +0.0338 | +0.0421 | -0.0787 | -0.0008 | +0.0488 | +0.0485 | -0.0451 |
| pear | -0.0110 | -0.0036 | +0.0177 | -0.0406 | -0.0166 | +0.0168 | +0.0490 | -0.0118 |
| tomato | +0.0221 | -0.0077 | -0.0239 | +0.0171 | -0.0057 | -0.0250 | -0.0291 | +0.0521 |

| Class | Diagonal residual | Centered row argmax | Best off-diagonal | Its residual |
|---|---:|---|---|---:|
| apple | +0.025784 | tomato | tomato | +0.043737 |
| car | -0.007245 | cup | cup | +0.054735 |
| cow | +0.033771 | horse | horse | +0.038751 |
| cup | +0.175114 | cup | apple | +0.068762 |
| dog | +0.018106 | horse | horse | +0.041092 |
| horse | +0.048831 | horse | pear | +0.048545 |
| pear | +0.048995 | pear | cow | +0.017733 |
| tomato | +0.052115 | tomato | apple | +0.022142 |

Cup has the largest diagonal residual (+0.175114), reversing the impression from its low raw diagonal. Car is the only negative diagonal residual. Centered row argmax is correct for cup, horse, pear and tomato; apple, car, cow and dog have a higher off-diagonal residual. These are within-matrix associations, not a generalization test.

## 4. Why car → cup?

Car→cup is the largest centered car-row residual even though its raw score is lower than car→car. The cup column is unusually low against *all* references; subtracting that column baseline produces the inversion. This is not evidence by itself that a car and cup have the same shape.

| Car reference compared with | Raw score | Centered residual | Matched nodes, mean | Matched edges, mean | Graded edge similarity | Node score component | Edge score component |
|---|---:|---:|---:|---:|---:|---:|---:|
| car | 0.490695 | -0.007245 | 287.25 | 22.06 | 0.510883 | 0.461040 | 0.029655 |
| cup | 0.369237 | +0.054735 | 235.12 | 39.62 | 0.470368 | 0.324936 | 0.044301 |

The raw cup-minus-car gap in that row is -0.121458; column-centering adds +0.183438, yielding a centered gap of +0.061980. The score components above are the original numerator contributions after both-side normalization; they sum to the cell score. Matched edges include presence-only and graded relations.

- Car→car: largest matched edge types per comparison: CONTOUR_ORIENTATION 8.44, JUNCTION_CONTOUR 2.75, ORIENTATION_CONTINUITY 2.06, ORIENTATION_JUNCTION 2.06, CONTOUR_CONTINUITY 1.50; largest matched node lenses: CONTOUR_PEAK 119.00, ContourFragment 49.44, EndStopped 36.88, Orientation 31.56.
- Car→cup: largest matched edge types per comparison: CONTOUR_ORIENTATION 14.12, ORIENTATION_CONTINUITY 5.88, JUNCTION_CONTOUR 3.81, CURVE_CONTAINMENT 3.75, CONTOUR_CONTINUITY 2.81; largest matched node lenses: CONTOUR_PEAK 61.56, ContourFragment 52.00, Orientation 44.00, EndStopped 35.50.

`CONTOUR_ORIENTATION` is an index-only membership relation, not a continuous physical measurement: its average credited presence rises from 8.44 for car→car to 14.12 for car→cup. The cup comparisons thus preserve more generic contour/orientation membership, but their normalized node contribution is much lower. Their mean score denominator is 1,121.06 versus 1,018.31 for car→car. This breakdown shows what relations and node families are reused; without an object-role ground truth it does not establish that they correspond to car or cup parts.

## 5. Diagonal sign checks

For each class, compare its raw diagonal cell to its own raw row or column mean (including the diagonal):

| Class | Diagonal − row mean | Diagonal − column mean |
|---|---:|---:|
| apple | +0.006574 | +0.056658 |
| car | +0.018649 | -0.050826 |
| cow | +0.077720 | +0.073634 |
| cup | +0.017570 | +0.075781 |
| dog | +0.018379 | +0.029783 |
| horse | +0.096515 | +0.049009 |
| pear | +0.096957 | +0.095237 |
| tomato | +0.063106 | +0.066195 |

Diagonal exceeds its row mean for **8/8** classes and its column mean for **7/8** classes (car is the exception). Under an independent fair-sign null, the nominal two-sided exact binomial values are 0.0078125 and 0.0703125, respectively. They should not be interpreted as validated significance: matrix cells share reference and held-out graphs, so independence is not established.

Full unrounded results, frame sizes and hashes: `results/nuisance-analysis.json`; pair-order measurements: `results/nuisance-symmetry.json`. Reproduction scripts are `harness/nuisance_reconstruct.py`, `harness/nuisance_symmetry.py`, `harness/nuisance_analysis.py`, and `harness/nuisance_report.py`. Original matrix: `ETH80_JOINT_MCS_MATRIX.md`.
