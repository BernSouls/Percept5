"""Regression checks for the fixed-matrix, analysis-only re-presentation."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_double_center_and_signs_from_unrounded_original_cells():
    source = json.loads((ROOT/'phase3/results/joint-matrix-seed0.json').read_text())
    result = json.loads((ROOT/'phase3/results/nuisance-analysis.json').read_text())
    classes = source['classes']
    m = [[source['cells'][a][b]['similarity'] for b in classes] for a in classes]
    rows = [math.fsum(r)/8 for r in m]
    cols = [math.fsum(r[j] for r in m)/8 for j in range(8)]
    grand = math.fsum(rows)/8
    d = [[m[i][j]-rows[i]-cols[j]+grand for j in range(8)] for i in range(8)]
    for i in range(8):
        assert abs(math.fsum(d[i])) < 1e-14
        assert abs(math.fsum(row[i] for row in d)) < 1e-14
        for j in range(8): assert abs(d[i][j] - result['centered_matrix'][i][j]) < 1e-15
    assert max(range(8),key=lambda i:d[i][i]) == classes.index('cup')
    assert [classes[i] for i in range(8) if d[i][i] < 0] == ['car']
    assert sum(m[i][i]>rows[i] for i in range(8)) == 8
    assert sum(m[i][i]>cols[i] for i in range(8)) == 7
    assert result['hash_verified_frames']==136


def test_same_pair_order_checks_reproduce_original():
    out=json.loads((ROOT/'phase3/results/nuisance-symmetry.json').read_text())
    assert len(out['pairs'])==4
    assert all(p['A_to_B']==p['B_to_A']==p['original_score'] for p in out['pairs'])
