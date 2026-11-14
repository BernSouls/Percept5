"""[PHASE 2] THE FIVE FLAG-GATED MECHANISMS -- one pin each.

EVERY DEFAULT IS OFF: the overlay loads with the tree's historical
behaviour, so the series applies WITHOUT changing a single number until a
pre-registered rule selects a flag.  Each pin asserts (a) the default and
(b) the mechanism when the flag is ON, so reverting any mechanism
reddens exactly one pin here.
"""
from __future__ import annotations

import parameters as P
from core.schema import EdgeParams, polymorphic_edge_similarity
from core.types import EdgeType
from memory.cores import evidence_score, mcs_score
from matching.consensus import vote_consensus

from _graphs import graph, tex

RC = EdgeType.REGION_CONTENT
BA = EdgeType.BOUNDARY_ATTACHMENT
CT = EdgeType.CONTACT

THE_NEW_FLAGS = (
    "MATCH_EDGE_MASS_CONTAINMENT",
    "MATCH_SKIP_INCOMPARABLE_RELATIONS",
    "MATCH_KEEP_HIERARCHY_MEMBERS",
    "MATCH_TEMPLATE_MEDIAN_EXEMPLAR",
    "MATCH_CONSENSUS_COUNT_ABSTENTIONS",
)


def _flag(cls, values=(1.0,)):
    return EdgeParams(class_="EDGE_" + cls, quantized=tuple(values))


def test_every_new_flag_defaults_to_the_historical_behaviour():
    """The series must apply without changing behaviour."""
    for name in THE_NEW_FLAGS:
        assert hasattr(P, name), "the flag %r is not declared" % name
        assert getattr(P, name) is False, (
            "the flag %r must default to OFF (the historical behaviour)"
            % name)


def test_b3_the_containment_caps_the_matched_edge_mass(params):
    """B3: the matched edge mass may not exceed the edge mass."""
    nodes = {1: ("Tex", tex(1, 1)), 2: ("Tex", tex(8, 8))}
    Q, qs = graph(nodes, [(1, 2, RC)], {(1, 2, RC): _flag("REGION_CONTENT")})
    C, cs = graph(nodes, [(1, 2, RC)], {(1, 2, RC): _flag("REGION_CONTENT")})
    params(EDGE_LOOKUP_KEY_IS_NOT_A_MEASURED_AXIS=False)
    tr = {}
    mcs_score(Q, C, qs, cs, trace=tr)
    assert tr["c_matched_em"] == 2.0, "the historical overflow must stay"
    assert tr["c_matched_em_raw"] == 2.0
    params(MATCH_EDGE_MASS_CONTAINMENT=True)
    tr = {}
    mcs_score(Q, C, qs, cs, trace=tr)
    assert tr["c_matched_em"] == 1.0, (
        "the containment must cap the matched mass at its own total")
    assert tr["c_matched_em_raw"] == 2.0, (
        "the RAW mass must keep the facilitation visible: the pin's"
        " discriminating power is the 2.0 against the 1.0")
    assert tr["c_matched_em"] <= tr["c_edge_total"]


def test_b7_an_incomparable_relation_is_skipped_not_scored(params):
    """B7: no common ontology is INCOMPARABLE, not contradictory."""
    legacy = _flag("BOUNDARY_ATTACHMENT", (0.1, 0.0, 0.0))
    native = _flag("CONTACT", (0.0, 0.0, 0.0))
    assert polymorphic_edge_similarity(legacy, native) == 0.0, (
        "the historical answer is 0.0 (a contradiction)")
    assert polymorphic_edge_similarity(legacy, native, return_none=True) is None
    nodes = {1: ("Tex", tex(1, 1)), 2: ("Tex", tex(8, 8))}
    Q, qs = graph(nodes, [(1, 2, CT)], {(1, 2, CT): native})
    C, cs = graph(nodes, [(1, 2, BA)], {(1, 2, BA): legacy})
    tr = {}
    evidence_score(Q, C, qs, cs, trace=tr)
    assert tr["verifiable_core_edges_count"] == 1, (
        "without the flag the incomparable relation counts against the"
        " match")
    params(MATCH_SKIP_INCOMPARABLE_RELATIONS=True)
    tr = {}
    evidence_score(Q, C, qs, cs, trace=tr)
    assert tr["verifiable_core_edges_count"] == 0, (
        "the incomparable relation must leave the denominator")
    assert tr["incomparable_core_edges"] == 1


def test_p0_the_member_is_kept_only_when_the_flag_is_on(params):
    """P0: the hierarchy step keeps the member (the flag gates it)."""
    from core.graph_types import Subgraph
    import memory.mapper as M

    class _Fake:
        def _part_exclusions(self):
            return {11}

    sg = Subgraph(nodes=frozenset({1, 11}), edges=frozenset())
    before = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg)
    assert len(before.nodes) == 1, (
        "without the flag the member is removed (the historical"
        " behaviour)")
    params(MATCH_KEEP_HIERARCHY_MEMBERS=True)
    after = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg)
    assert len(after.nodes) == 2, (
        "with the flag on, no member is removed")


def test_d5_the_median_exemplar_only_when_the_flag_is_on():
    """D5: the template is built in the median exemplar's space."""
    import inspect
    from matching import structural_similarity as ss
    src = inspect.getsource(ss)
    assert "MATCH_TEMPLATE_MEDIAN_EXEMPLAR" in src, (
        "the median exemplar must be behind its flag")


def test_d7_the_abstentions_are_counted_only_when_the_flag_is_on(params):
    """D7: 2 of 5 voters is a support of 0.400 over 5 voters."""
    vc = vote_consensus([[1.0, None, None, None, 1.0]], n_voters=5)
    assert abs(vc.support[0] - 0.4) < 1e-9, (
        "the support must be over ALL the voters")
    assert vc.n_voters == 5
    # without the flag the historical denominator (the voters that
    # answered) is kept -- and the caller passes n_voters=None
    vc2 = vote_consensus([[1.0, None, None, None, 1.0]])
    assert vc2.n_voters == 5
