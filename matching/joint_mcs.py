"""Unsupervised, balanced, graded one-to-one graph correspondence.

This score intentionally uses unweighted node and edge masses: unlike the
historical mcs_similarity its node credit is graded and its matched-edge mass
is not amplified by axis-count facilitation. Correspondence is a bounded
fixed-point approximation, not a certificate of a globally optimal MCS.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import math
import parameters as P
from core.schema import edge_graded_axes
from core.types import UNDIRECTED_EDGE_TYPES
from matching.alignment import global_consistency_alignment
from matching.structural_similarity import _lookup_edge_params, _pair_edge_sim_typed


def edge_key(e):
    a,b,t=e
    return (min(a,b),max(a,b),t.value,a,b)


def edge_pair_credit(a, b, x, y, u, v, et):
    """Typed edge credit; missing parameters yield presence, not physics."""
    p = _lookup_edge_params(a.edge_params, x, y, et)
    q = _lookup_edge_params(b.edge_params, u, v, et)
    if p is None or q is None:
        return 1.0
    return _pair_edge_sim_typed(x, y, et, p, u, v, et, q, False)


@dataclass(frozen=True)
class JointMCS:
    score: float
    mapping: dict
    matched_edges: int
    graded_edges: int
    graded_edge_similarity_sum: float
    presence_only_edges: int
    budget_exhausted: bool
    @property
    def mean_graded_edge_similarity(self):
        return self.graded_edge_similarity_sum / self.graded_edges if self.graded_edges else None


def _directional_joint_mcs(a, b, sigs_a, sigs_b):
    """Two graphs in; no labels, training sets, filtering or learned masses.

    Each matched node contributes its signature similarity; each preserved
    same-type edge contributes its parameter similarity, or one unit of
    topology-only presence if either side has no parameters. Identical
    predicates with no shared graded axes are never called a physical reading.
    The numerator is twice the total matched node/edge credit; denominator is
    the number of nodes plus edges on BOTH sides.
    """
    from memory.cores import _sig_similarity
    na,nb=sorted(a.nodes),sorted(b.nodes)
    def node_sim(u,v):
        x,y=sigs_a.get(u),sigs_b.get(v)
        if x is None or y is None or x[0]!=y[0]: return 0.0
        return _sig_similarity(x[1],y[1])

    @lru_cache(maxsize=None)
    def edge_sim(x,y,u,v,et):
        return edge_pair_credit(a,b,x,y,u,v,et)

    al=global_consistency_alignment(
        na,nb,node_sim,edges_a=a.edges,edges_b=b.edges,
        unmatched_cost=float(P.MATCH_UNMATCHED_COST),
        systematicity_weight=float(P.MATCH_SYSTEMATICITY_WEIGHT),
        rounds=int(P.MATCH_ALIGN_ROUNDS),max_pair_evals=P.MATCH_ALIGN_MAX_PAIR_EVALS,
        budget_refinement_only=bool(P.MATCH_ALIGN_BUDGET_REFINEMENT_ONLY),
        edge_similarity=edge_sim)
    assert len(set(al.mapping.values()))==len(al.mapping)
    b_und={(min(x,y),max(x,y),et) for x,y,et in b.edges if et in UNDIRECTED_EDGE_TYPES}
    b_dir={(x,y,et) for x,y,et in b.edges if et not in UNDIRECTED_EDGE_TYPES}
    credits=[];graded=[];presence=0;used_target_edges=set()
    for x,y,et in sorted(a.edges,key=edge_key):
        u,v=al.mapping.get(x),al.mapping.get(y)
        if u is None or v is None:continue
        target=(min(u,v),max(u,v),et) if et in UNDIRECTED_EDGE_TYPES else (u,v,et)
        present=(target in b_und if et in UNDIRECTED_EDGE_TYPES else target in b_dir)
        if not present or target in used_target_edges:continue
        used_target_edges.add(target)
        value=edge_sim(x,y,u,v,et);credits.append(value)
        p=_lookup_edge_params(a.edge_params,x,y,et);q=_lookup_edge_params(b.edge_params,u,v,et)
        if edge_graded_axes(p,q)>0:graded.append(value)
        else:presence+=1
    nodes=math.fsum(node_sim(u,v) for u,v in sorted(al.mapping.items()))
    denom=len(a.nodes)+len(b.nodes)+len(a.edges)+len(b.edges)
    score=2.0*(nodes+math.fsum(credits))/denom if denom else 0.0
    return JointMCS(score,dict(al.mapping),len(credits),len(graded),math.fsum(graded),presence,al.budget_exhausted)


def joint_mcs(a, b, sigs_a, sigs_b):
    """Symmetric score: retain the better of both directional heuristic solves.

    This does not certify optimality. Reversing graph arguments considers the
    same two candidates, so the scalar score is symmetric even if the bounded
    heuristic's seed or refinement behaves differently in the two directions.
    """
    forward = _directional_joint_mcs(a, b, sigs_a, sigs_b)
    reverse = _directional_joint_mcs(b, a, sigs_b, sigs_a)
    if forward.score >= reverse.score:
        return forward
    return JointMCS(reverse.score, {v:k for k,v in reverse.mapping.items()},
                    reverse.matched_edges, reverse.graded_edges,
                    reverse.graded_edge_similarity_sum, reverse.presence_only_edges,
                    forward.budget_exhausted or reverse.budget_exhausted)
