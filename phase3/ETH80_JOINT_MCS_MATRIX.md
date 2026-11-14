# ETH80_ALL8 joint graded MCS matrix

> **Analysis correction:** Raw scores have a strong graph-size/density nuisance. See [the nuisance-aware reanalysis](ETH80_NUISANCE_ANALYSIS.md) for same-pair symmetry, sizes and the double-centered matrix. The original results below are retained unchanged.

Rows are reference-class graphs; columns are held-out classes, averaged over 16 views. Each cell is a direct two-graph comparison, with no discriminative filter, positive/negative training, or learned weights. Rows and columns use different images, so the displayed matrix need not be symmetric even though each pair score is symmetric.

**Diagonal mean: 0.565061. Off-diagonal mean: 0.508565.** The mean diagonal is higher, but the diagonal is not the row maximum for apple, car, cow, cup, or dog; horse is ahead of its closest off-diagonal by only 0.00000846.

## Similarity

| Reference \ held-out | apple | car | cow | cup | dog | horse | pear | tomato |
|---|---|---|---|---|---|---|---|---|
| apple | 0.5531 | 0.5585 | 0.5705 | 0.4009 | 0.5375 | 0.5704 | 0.5799 | 0.6012 |
| car | 0.4713 | 0.4907 | 0.4968 | 0.3692 | 0.4865 | 0.4919 | 0.4787 | 0.4912 |
| cow | 0.5009 | 0.6065 | 0.6332 | 0.3252 | 0.5653 | 0.6419 | 0.6261 | 0.5448 |
| cup | 0.4658 | 0.3897 | 0.3960 | 0.4339 | 0.4071 | 0.3951 | 0.4102 | 0.4326 |
| dog | 0.4679 | 0.5793 | 0.6049 | 0.3029 | 0.5457 | 0.6161 | 0.5941 | 0.5075 |
| horse | 0.4479 | 0.5755 | 0.6019 | 0.2796 | 0.5153 | 0.6123 | 0.6123 | 0.4817 |
| pear | 0.5317 | 0.5842 | 0.6236 | 0.3637 | 0.5456 | 0.6263 | 0.6588 | 0.5611 |
| tomato | 0.5326 | 0.5479 | 0.5498 | 0.3893 | 0.5243 | 0.5523 | 0.5486 | 0.5928 |

## Per-class diagonal margin

| Reference | Diagonal | Best off-diagonal class | Best off-diagonal | Margin |
|---|---:|---|---:|---:|
| apple | 0.553075 | tomato | 0.601230 | -0.04815565 |
| car | 0.490695 | cow | 0.496792 | -0.00609690 |
| cow | 0.633211 | horse | 0.641926 | -0.00871453 |
| cup | 0.433864 | apple | 0.465846 | -0.03198158 |
| dog | 0.545683 | horse | 0.616080 | -0.07039724 |
| horse | 0.612320 | pear | 0.612312 | +0.00000846 |
| pear | 0.658826 | horse | 0.626342 | +0.03248374 |
| tomato | 0.592814 | horse | 0.552342 | +0.04047154 |

## Mechanism per class pair

Counts are means per comparison, not totals. Graded edge similarity is pooled across matched edges with at least one shared measured graded axis; presence-only edges are excluded from that mean. The JSON includes both graded and presence-only denominators.

## Matched nodes, mean

| Reference \ held-out | apple | car | cow | cup | dog | horse | pear | tomato |
|---|---|---|---|---|---|---|---|---|
| apple | 309.6 | 328.0 | 309.9 | 258.3 | 305.6 | 310.3 | 317.1 | 353.2 |
| car | 282.4 | 287.2 | 274.4 | 235.1 | 286.2 | 274.0 | 268.2 | 299.9 |
| cow | 266.3 | 324.4 | 307.7 | 195.9 | 293.7 | 313.1 | 310.1 | 293.3 |
| cup | 235.1 | 216.0 | 205.4 | 231.1 | 213.2 | 203.6 | 205.8 | 231.6 |
| dog | 239.8 | 302.7 | 288.2 | 168.8 | 277.5 | 295.6 | 288.9 | 269.3 |
| horse | 220.6 | 288.4 | 274.8 | 147.7 | 255.7 | 280.2 | 280.2 | 247.2 |
| pear | 265.6 | 311.7 | 302.7 | 195.7 | 284.2 | 304.0 | 306.3 | 293.0 |
| tomato | 315.0 | 343.1 | 321.4 | 261.9 | 319.8 | 323.5 | 323.1 | 371.5 |

## Matched edges, mean

| Reference \ held-out | apple | car | cow | cup | dog | horse | pear | tomato |
|---|---|---|---|---|---|---|---|---|
| apple | 24.6 | 15.1 | 12.5 | 23.5 | 19.9 | 13.8 | 16.1 | 24.8 |
| car | 30.8 | 22.1 | 20.2 | 39.6 | 28.9 | 20.7 | 19.7 | 26.9 |
| cow | 14.8 | 13.7 | 14.0 | 12.6 | 13.2 | 15.0 | 16.3 | 14.6 |
| cup | 38.7 | 23.6 | 19.4 | 56.4 | 33.8 | 20.2 | 22.1 | 31.5 |
| dog | 14.5 | 14.1 | 14.7 | 18.2 | 15.8 | 16.2 | 16.6 | 14.2 |
| horse | 11.6 | 12.8 | 13.2 | 17.2 | 8.1 | 14.8 | 18.4 | 10.6 |
| pear | 20.3 | 16.2 | 20.3 | 24.2 | 15.5 | 20.9 | 28.8 | 20.8 |
| tomato | 28.4 | 18.6 | 14.1 | 27.6 | 23.4 | 13.6 | 17.1 | 28.1 |

## Mean graded edge similarity

| Reference \ held-out | apple | car | cow | cup | dog | horse | pear | tomato |
|---|---|---|---|---|---|---|---|---|
| apple | 0.5359 | 0.4148 | 0.5061 | 0.5178 | 0.5175 | 0.5064 | 0.4428 | 0.4922 |
| car | 0.4876 | 0.5109 | 0.5094 | 0.4704 | 0.5135 | 0.4043 | 0.4839 | 0.5197 |
| cow | 0.3599 | 0.3973 | 0.3994 | 0.4886 | 0.5262 | 0.4111 | 0.4458 | 0.4546 |
| cup | 0.4795 | 0.4742 | 0.4444 | 0.5400 | 0.5203 | 0.3882 | 0.4215 | 0.4614 |
| dog | 0.4996 | 0.4136 | 0.4561 | 0.5476 | 0.5319 | 0.4072 | 0.3579 | 0.5567 |
| horse | 0.3019 | 0.3411 | 0.2049 | 0.3624 | 0.4447 | 0.2978 | 0.3304 | 0.4045 |
| pear | 0.4383 | 0.4444 | 0.4306 | 0.5161 | 0.4800 | 0.4502 | 0.5529 | 0.4635 |
| tomato | 0.4413 | 0.4859 | 0.4244 | 0.4175 | 0.4519 | 0.3996 | 0.4720 | 0.4716 |

## Score and verification

The registered score is `2 × (sum matched-node similarity + sum matched-edge credit) / (nodes_A + nodes_B + edges_A + edges_B)`. Same-type edges with comparable parameters receive their graded similarity; missing-parameter or identity-only relations contribute presence, not an invented graded measurement. Both directional bounded Hungarian/refinement solves are tried, and the larger balanced score is retained. This is an approximation, not a proof of a global maximum. Existing `mcs_similarity` was not used because it has binary node credit and axis-count edge facilitation.

The live matcher bypasses the deprecated supervised filter, uses the unfiltered selected reference graph, and has `MATCH_GLOBAL_CONSISTENCY_ENABLED=True`. Relations enter the reassignment weights. A constructed product-path test changes the mapping when one edge is removed, not merely the final score; 1,024/1,024 returned mappings were one-to-one. The 1,024 selected results reported zero alignment budget exhaustions.

Both independent seed runs completed 1,024 comparisons with zero errors; result SHA-256: seed 0 `031b27d2c9d13ba92c9129944c5a6f591ef59cc86a77c9d5b102bd11d8add04c`, seed 1729 `031b27d2c9d13ba92c9129944c5a6f591ef59cc86a77c9d5b102bd11d8add04c`. **Byte-identical.** Both scoring runs used the same hash-verified reconstructed graphs; this is not a second independent graph extraction. All 136 reconstructed graph hashes matched the earlier selected-frame records, and the earlier independent 151-frame extraction matched across seeds. The 508-entry incidence probe also matched under both seeds: `4932c30f0f3ac44ab88811dd844181b156f2cfe7b0dfa53f701adc7fc0c93691`.

The explicit edge-reuse guard was added during the sweep. All 136 measured graphs contain zero reverse-duplicate undirected edges, so it does not change any measured edge correspondence; one diagonal comparison per class was independently rerun against the final code and all eight matched exactly.

Regression: 540 tests passed. Tests of `_content_discriminative_filter` or its supervised behaviour remain in the tree as deprecated-path tests, not evidence about the live matcher. The score form and corpus were registered before matrix scoring; no matrix-driven tuning was performed. Full per-view mappings, counts, and denominators are in `results/joint-matrix-seed0.json` and its seed-1729 repeat; the protocol is `audit/joint-mcs-protocol.json`.
