"""Small, explicit estimators for the independent Phase-0 audit."""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
import math
from typing import Iterable, Sequence

import numpy as np


def canonical_key(v):
    """A total, hash-seed-independent ordering key for heterogeneous values.

    No repr(), no id(): every value becomes a nested tuple whose first
    element is a stable type tag and whose payload is comparable within that
    tag. Floats use their exact hex encoding, so the key never depends on
    repr formatting or locale. Used ONLY to order the terms of an exactly
    rounded fsum and to derive a permutation seed -- never as a measurement.
    """
    if v is None:
        return ("none",)
    if isinstance(v, bool):
        return ("bool", int(v))
    if isinstance(v, int):
        return ("int", v)
    if isinstance(v, float):
        return ("float", "nan") if math.isnan(v) else ("float", v.hex())
    if isinstance(v, str):
        return ("str", v)
    if isinstance(v, bytes):
        return ("bytes", v.hex())
    if isinstance(v, (tuple, list)):
        return ("seq", tuple(canonical_key(x) for x in v))
    if isinstance(v, (set, frozenset)):
        return ("set", tuple(sorted(canonical_key(x) for x in v)))
    raise TypeError(f"canonical_key: unsupported type {type(v).__name__}")


def entropy(values: Iterable) -> float | None:
    counts = Counter(values)
    n = sum(counts.values())
    if n == 0:
        return None
    return -math.fsum((c / n) * math.log2(c / n)
                      for _, c in sorted(counts.items(), key=lambda kv: canonical_key(kv[0])))


def mutual_information(x: Sequence, y: Sequence) -> float | None:
    if len(x) != len(y):
        raise ValueError("paired variables must have equal length")
    if not x:
        return None
    n = len(x)
    cx, cy, joint = Counter(x), Counter(y), Counter(zip(x, y))
    return math.fsum((count / n) * math.log2((count * n) / (cx[a] * cy[b]))
                     for (a, b), count in sorted(joint.items(), key=lambda kv: (canonical_key(kv[0][0]), canonical_key(kv[0][1]))))


def quantiles(values: Sequence[float]) -> dict:
    if not values:
        return {"n": 0, "min": None, "median": None, "p95": None, "max": None}
    a = np.asarray(values, dtype=np.float64)
    return {"n": len(values), "min": float(np.min(a)),
            "median": float(np.median(a)), "p95": float(np.quantile(a, .95)),
            "max": float(np.max(a))}


def canonical_edge(e):
    from phase3.runtime.bootstrap import load
    undirected = load("core.types").UNDIRECTED_EDGE_TYPES
    return (min(e[0], e[1]), max(e[0], e[1]), e[2]) if e[2] in undirected else tuple(e)


def edge_key(e):
    a, b, et = canonical_edge(e)
    return (a, b, int(et.value))


def edge_sort(edges):
    return sorted(edges, key=edge_key)


def permutation_mi(values: Sequence, labels: Sequence, *, seed: int,
                   permutations: int = 1000) -> dict:
    observed = mutual_information(values, labels)
    if observed is None:
        return {"n": 0, "observed_bits": None, "permutations": permutations,
                "p_one_sided": None, "null_median_bits": None, "null_p95_bits": None}
    # A stable content-derived stream avoids dependence on hash iteration.
    # Canonical typed encoding, never repr(): the seed is reproducible across
    # processes and hash seeds.
    items = sorted(Counter(zip(values, labels)).items(),
                   key=lambda kv: (canonical_key(kv[0][0]), canonical_key(kv[0][1])))
    content = json.dumps([[canonical_key(a), canonical_key(b), c] for (a, b), c in items]).encode()
    stable_seed = int.from_bytes(hashlib.sha256(content).digest()[:8], "little") ^ seed
    rng = np.random.default_rng(stable_seed)
    y = np.asarray(labels)
    null = []
    for _ in range(permutations):
        shuffled = rng.permutation(y).tolist()
        null.append(mutual_information(values, shuffled))
    return {
        "n": len(values), "observed_bits": observed,
        "permutations": permutations,
        "exceedances": sum(v >= observed for v in null),
        "p_one_sided": (1 + sum(v >= observed for v in null)) / (permutations + 1),
        "null_median_bits": float(np.median(null)),
        "null_p95_bits": float(np.quantile(null, .95)),
    }


def correlation(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 2 or len(x) != len(y):
        return None
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if float(np.std(a)) <= 1e-15 or float(np.std(b)) <= 1e-15:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def jaccard(a: set, b: set) -> float | None:
    if not a and not b:
        return None
    return len(a & b) / len(a | b)


def connected_components(nodes: Iterable[int], edges: Iterable[tuple]) -> list[int]:
    parent = {n: n for n in nodes}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, *_ in edges:
        if a not in parent or b not in parent:
            continue
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    sizes = Counter(find(n) for n in sorted(parent))
    return sorted(sizes.values(), reverse=True)
