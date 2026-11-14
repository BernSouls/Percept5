# Percept5 measurement and regression harness

This directory is the replacement harness used for the ETH80_ALL8 analyses. It
is **not a standalone matcher**: run it from the root of the Percept5 checkout
at the PR containing this directory. It imports the product's `core/`,
`matching/`, `memory/`, `perception/`, `orchestration/` and other modules, plus
the included `tests/` fixtures. `phase3.runtime.bootstrap` checks that product
modules come from that checkout, not an unrelated installed copy.

The old `patchfile/` series has been integrated and removed. Its original
application record remains in `phase3/audit/phase2_apply.log`,
`phase3/audit/phase2-patch-verification.md` and
`phase3/audit/build-patch-status.json`; the regression pins are in
`tests/matcher/`. Those records are historical, not a fresh verification of
all future edits.

## Setup (Python 3.11)

Run from the repository root. These are the versions used for the recorded
matrix; other environments may change numeric or graph-hash results.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install 'numpy==2.4.6' 'scipy==1.17.1' 'Pillow==13.0.0' 'pytest==9.2.0'
OPENBLAS_NUM_THREADS=1 ./phase3/run_pytest.sh tests/matcher phase3/test_frontend_build_contract.py phase3/test_joint_mcs_contract.py phase3/test_joint_edge_grade.py phase3/test_nuisance_analysis.py -q
```

On Windows PowerShell, create the environment with `py -3.11 -m venv .venv`,
install with `.venv\Scripts\python -m pip install numpy==2.4.6 scipy==1.17.1 Pillow==13.0.0 pytest==9.2.0`, then run:

```powershell
$env:PYTHONPATH = ".;phase3/runtime/shims;tests/matcher"
$env:PYTHONHASHSEED = "0"
$env:OPENBLAS_NUM_THREADS = "1"
.venv\Scripts\python -m pytest -p phase3.runtime.pytest_guard tests/matcher phase3/test_frontend_build_contract.py phase3/test_joint_mcs_contract.py phase3/test_joint_edge_grade.py phase3/test_nuisance_analysis.py -q
```

The runtime shims are compatibility imports; the action decoder shim cannot
execute action decoding. These tests and analyses cover matching and the
sensory frontend, not the full action system.

## Inspect existing results

- `ETH80_JOINT_MCS_MATRIX.md`: original raw matrix and diagnostics.
- `ETH80_NUISANCE_ANALYSIS.md`: centered matrix, graph sizes and symmetry.
- `audit/joint-mcs-protocol.json`: score and corpus registered before scoring.
- `results/joint-matrix-seed0.json` and `...seed1729.json`: the complete
  original per-view mappings and scores. They are measurements, not fixtures
  to overwrite when doing a new experiment.
- `results/nuisance-analysis.json`: frame sizes, graph hashes and full precision
  nuisance analysis; `results/nuisance-symmetry.json` contains the order tests.

## Reconstruct and repeat the matrix (optional and expensive)

This downloads the pinned ETH-80 source archive (~307 MB) from GitHub, verifies
its SHA-256, and extracts **only** the 136 pinned reference/held-out images.
The archive and images are not included in the harness. You may instead supply
an existing verified archive via `--archive /path/to/archive.tar.gz`.
The pinned image manifest is not rewritten.

```bash
.venv/bin/python -m phase3.harness.restore_eth80
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m phase3.harness.matrix_frames
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m phase3.harness.matrix_graph_integrity
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m phase3.harness.joint_matrix --seed-name repeat0
PYTHONHASHSEED=1729 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m phase3.harness.joint_matrix --seed-name repeat1729
sha256sum phase3/results/joint-matrix-{seed0,seed1729,repeat0,repeat1729}.json
```

Frame reconstruction and 2,048 matching comparisons can take substantial
CPU time and disk space. `repeat0` and `repeat1729` are intentionally new names;
the original results remain untouched. Graph inputs are in the disposable,
ignored `.cache/joint-matrix/`. Compare hashes and inspect errors and every
cell rather than assuming a repeat is identical. Each extraction and matching
comparison asserts the local product module paths and live contract. With a
new Python/platform/dependency version, different hashes should be reported,
not silently treated as the original measurement.

The nuisance reanalysis scripts use a separately reconstructed cache: run
`nuisance_reconstruct --shard 0` and `--shard 1` (same environment, each once),
then `nuisance_symmetry`, `nuisance_analysis`, and `nuisance_report` as
`python -m phase3.harness.<name>`. Those final commands overwrite the existing
nuisance results/report; copy them elsewhere first if preserving the originals.
The code does not adjust matcher parameters or learn from labels.
