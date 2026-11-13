"""[PHASE 2] THE MECHANISM CHECKS for the overlay (revision 3).

Every check prints the loaded module path and ASSERTS it is under
`phase2/build`, so a check can never pass against the original tree by
accident (the revision-2 harness had that trap).

Every new flag must default to OFF (the historical behaviour), and each
mechanism must WORK when its flag is on.  No benchmark accuracy is claimed
here: the arms are measured separately, with precision first and the
renderer truth's row carried.
"""
from __future__ import annotations

import sys

import parameters as P
from core.graph_types import Subgraph
from core.schema import edge_params, polymorphic_edge_similarity
from core.types import EdgeType, TypedSignature
from memory.cores import evidence_score, mcs_score
from matching.consensus import vote_consensus
from matching.relation_frame import ATTRIBUTE_LENS_TYPES, FRAME_LENS_TYPES


def sig(vals, cls="CONTOUR"):
    return TypedSignature(kind="CANONICAL", class_=cls,
                          quantized=tuple(float(v) for v in vals))


def sg(nodes):
    return Subgraph(nodes=frozenset(nodes), edges=frozenset(), edge_params={},
                    anchor_of_node={n: (float(n), 0.0) for n in nodes})


def main() -> int:
    ok = True
    import core.schema as schema
    import matching.consensus as consensus
    import matching.structural_similarity as ss
    import memory.cores as cores
    import memory.mapper as mapper
    for m in (cores, schema, consensus, ss, mapper):
        print("module %-28s %s" % (m.__name__, m.__file__))
        ok &= "phase2" in m.__file__ and "build" in m.__file__

    # ---- every new flag defaults OFF --------------------------------
    flags = ("MATCH_EDGE_MASS_CONTAINMENT",
             "MATCH_SKIP_INCOMPARABLE_RELATIONS",
             "MATCH_KEEP_HIERARCHY_MEMBERS",
             "MATCH_TEMPLATE_MEDIAN_EXEMPLAR",
             "MATCH_CONSENSUS_COUNT_ABSTENTIONS")
    for f in flags:
        v = getattr(P, f, "MISSING")
        print("FLAG  %-36s %s" % (f, v))
        ok &= v is False

    # ---- B3: the containment -----------------------------------------
    # the same construction as the pin: a flag edge that counts as a
    # measured axis, so the facilitation (f(1) = 2) doubles the matched mass
    # above the edge total (1.0).
    q, c = sg({1, 2}), sg({1, 2})
    ep = edge_params("EDGE_REGION_CONTENT", {"containment": 1.0})
    q.edges = c.edges = frozenset({(1, 2, EdgeType.REGION_CONTENT)})
    q.edge_params = {(1, 2, EdgeType.REGION_CONTENT): ep}
    c.edge_params = {(1, 2, EdgeType.REGION_CONTENT): ep}
    qs3 = {1: ("CONTOUR", sig([0] * 7)), 2: ("CONTOUR", sig([0] * 7))}
    cs3 = {1: ("CONTOUR", sig([0] * 7)), 2: ("CONTOUR", sig([0] * 7))}
    P.EDGE_LOOKUP_KEY_IS_NOT_A_MEASURED_AXIS = False
    tr = {}
    mcs_score(q, c, qs3, cs3, trace=tr)
    print("B3  off: c_matched_em=%r c_edge_total=%r (the overflow)"
          % (tr.get("c_matched_em"), tr.get("c_edge_total")))
    ok &= tr.get("c_matched_em") == 2.0
    P.MATCH_EDGE_MASS_CONTAINMENT = True
    tr = {}
    mcs_score(q, c, qs3, cs3, trace=tr)
    print("B3  on : c_matched_em=%r raw=%r c_edge_total=%r (capped)"
          % (tr.get("c_matched_em"), tr.get("c_matched_em_raw"),
             tr.get("c_edge_total")))
    ok &= tr.get("c_matched_em") == 1.0
    ok &= tr.get("c_matched_em_raw") == 2.0
    P.MATCH_EDGE_MASS_CONTAINMENT = False
    P.EDGE_LOOKUP_KEY_IS_NOT_A_MEASURED_AXIS = True

    # ---- B7: the third state, wired into the live path ---------------
    legacy = edge_params("EDGE_BOUNDARY_ATTACHMENT",
                         {"arc_end_dist": 0.1, "tangent_angle": 0.0,
                          "perp_dist": 0.0})
    native = edge_params("EDGE_CONTACT",
                         {"normal_angle": 0.0, "dist": 0.0, "depth_step": 0.0})
    b7 = polymorphic_edge_similarity(legacy, native, return_none=True)
    print("B7  the third state: %r (the historical answer is 0.0)" % (b7,))
    ok &= b7 is None
    Q = sg({1, 2})
    C = sg({11, 12})
    Q.edges = frozenset({(1, 2, EdgeType.CONTACT)})
    C.edges = frozenset({(11, 12, EdgeType.BOUNDARY_ATTACHMENT)})
    Q.edge_params = {(1, 2, EdgeType.CONTACT): native}
    C.edge_params = {(11, 12, EdgeType.BOUNDARY_ATTACHMENT): legacy}
    qsig = {1: ("CONTOUR", sig([0] * 7)), 2: ("CONTOUR", sig([0] * 7))}
    csig = {11: ("CONTOUR", sig([0] * 7)), 12: ("CONTOUR", sig([0] * 7))}
    tr7 = {}
    evidence_score(Q, C, qsig, csig, trace=tr7)
    print("B7  off: n_core=%r comparable=%r"
          % (tr7.get("n_core_edges"), tr7.get("verifiable_core_edges_count")))
    P.MATCH_SKIP_INCOMPARABLE_RELATIONS = True
    tr7 = {}
    evidence_score(Q, C, qsig, csig, trace=tr7)
    print("B7  on : n_core=%r comparable=%r"
          % (tr7.get("n_core_edges"), tr7.get("verifiable_core_edges_count")))
    ok &= tr7.get("verifiable_core_edges_count") == 0
    P.MATCH_SKIP_INCOMPARABLE_RELATIONS = False

    # ---- P0: the member is kept -------------------------------------
    import memory.mapper as M

    class _Fake:
        def _part_exclusions(self):
            return {11}

    before = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg({1, 11}))
    P.MATCH_KEEP_HIERARCHY_MEMBERS = True
    after = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg({1, 11}))
    P.MATCH_KEEP_HIERARCHY_MEMBERS = False
    print("P0  off: %s   on: %s" % (sorted(before.nodes), sorted(after.nodes)))
    ok &= len(before.nodes) == 1 and len(after.nodes) == 2

    # ---- D5: the median exemplar -------------------------------------
    import inspect
    src = inspect.getsource(ss)
    d5 = "MATCH_TEMPLATE_MEDIAN_EXEMPLAR" in src
    print("D5  the median exemplar is behind its flag: %s" % d5)
    ok &= d5

    # ---- D7: the abstentions -----------------------------------------
    vc = vote_consensus([[1.0, None, None, None, 1.0]], n_voters=5)
    print("D7  support=%.3f n_voters=%d (the expected 0.400/5)"
          % (vc.support[0], vc.n_voters))
    ok &= abs(vc.support[0] - 0.4) < 1e-9 and vc.n_voters == 5

    # ---- B7b: the mechanism exists; the DEFAULT IS NOT FLIPPED -------
    flag = edge_params("EDGE_CONTOUR_ORIENTATION", {"containment": 1.0})
    b7b = polymorphic_edge_similarity(flag, flag)
    from core.schema import edge_graded_axes
    print("B7b the flag: EVIDENCE_RELATION_COUNT_APART=%s  the identity"
          " self-similarity=%.6f  the graded axes=%d"
          % (P.EVIDENCE_RELATION_COUNT_APART, b7b, edge_graded_axes(flag, flag)))
    ok &= P.EVIDENCE_RELATION_COUNT_APART is False

    # ---- the frame partition ------------------------------------------
    from lenses.base import _LENS_NAMES
    from lenses.derived_common import HIGHER_LENS_NAMES
    emitted = set(_LENS_NAMES) | set(HIGHER_LENS_NAMES)
    missing = sorted(emitted - (FRAME_LENS_TYPES | ATTRIBUTE_LENS_TYPES))
    print("FRAME the unregistered emitted types=%r" % (missing,))
    ok &= not missing

    print("OVERLAY: %s" % ("GREEN" if ok else "RED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
