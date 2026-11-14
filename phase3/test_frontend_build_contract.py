"""Unit contracts for the front-end build (no corpus measurements)."""
import pytest
import parameters as P

from core.frontend_contract import (
    LIVE_FLAGS, assert_live_contract, frontend_contract, frontend_contract_active,
)
from core.schema import EDGE_UNIT_TABLE, CONSTITUTIONAL_EDGE_RANGES
from perception.polar import _arc_split, _arc_mid, polar_boundary_fragments


def test_profile_nests_and_restores_on_exception():
    initial = {name: getattr(P, name) for name in LIVE_FLAGS}
    assert not frontend_contract_active()
    with pytest.raises(RuntimeError):
        with frontend_contract():
            assert_live_contract()
            with frontend_contract():
                assert_live_contract()
            assert_live_contract()
            raise RuntimeError("sentinel")
    assert not frontend_contract_active()
    assert {name: getattr(P, name) for name in LIVE_FLAGS} == initial


def test_unit_spans_do_not_replace_bin_ranges():
    assert EDGE_UNIT_TABLE["EDGE_CONTOUR_CONTINUITY"][0].hi == 6.0
    assert CONSTITUTIONAL_EDGE_RANGES["EDGE_CONTOUR_CONTINUITY"][0] == 8.0
    assert EDGE_UNIT_TABLE["EDGE_BORDER_OWNERSHIP"][1].hi == 2.0
    assert EDGE_UNIT_TABLE["EDGE_SHARED_BOUNDARY"][0].hi == 2.5


def test_fragment_cut_is_independent_of_vertex_spacing():
    fine = [(float(x), 0.0) for x in range(21)]
    coarse = [(0.0, 0.0), (7.0, 0.0), (20.0, 0.0)]
    for poly in (fine, coarse):
        cuts = _arc_split(poly, 5.0)
        assert len(cuts) == 4
        assert [_arc_mid(c)[0][0] for c in cuts] == pytest.approx([2.5, 7.5, 12.5, 17.5])
        assert [_arc_mid(c)[1] for c in cuts] == pytest.approx([5.0] * 4)


def test_fragment_host_partition_is_translation_and_other_host_stable():
    line = [(float(i), 0.0) for i in range(41)]
    other = [(float(i), 300.0) for i in range(41)]
    base, _ = polar_boundary_fragments([{"polyline": line}, {"polyline": other}])
    more, _ = polar_boundary_fragments([{"polyline": line}, {"polyline": other},
                                        {"polyline": [(float(i), 3000.0) for i in range(41)]}])
    moved, _ = polar_boundary_fragments([{"polyline": [(x + 3, y - 3) for x, y in line]},
                                         {"polyline": [(x + 3, y - 3) for x, y in other]}])
    b = [f for f in base if f["contour"] == 0]
    m = [f for f in more if f["contour"] == 0]
    t = [f for f in moved if f["contour"] == 0]
    assert len(b) == len(m) == len(t) > 1
    assert [f["host_arc_start"] for f in b] == pytest.approx([f["host_arc_start"] for f in m])
    for x, y in zip(b, t):
        assert y["mid"] == pytest.approx((x["mid"][0] + 3, x["mid"][1] - 3))
        assert y["host_arc_end"] == pytest.approx(x["host_arc_end"])


def test_live_evidence_requires_structure_on_both_sides():
    from _graphs import graph, tex
    from core.types import EdgeType
    from memory.cores import evidence_score
    nodes_a = {i: ("Texture", tex(i, i)) for i in range(3)}
    nodes_b = {100 + i: ("Texture", tex(i, i)) for i in range(3)}
    q, qs = graph(nodes_a, [(0, 1, EdgeType.TOPOLOGY)])
    c, cs = graph(nodes_b)
    historical = {}
    evidence_score(q, c, qs, cs, trace=historical)
    assert historical["relational_consistency"] == 1.0
    with frontend_contract():
        for left, right, ls, rs in [(q, c, qs, cs), (c, q, cs, qs)]:
            trace = {}
            score, _ = evidence_score(left, right, ls, rs, trace=trace)
            assert trace["relational_multiplier"] == 0.0
            assert score == 0.0
        trace = {}
        evidence_score(c, c, cs, cs, trace=trace)
        assert trace["relational_multiplier"] == 1.0


def test_absent_population_axes_are_skipped_not_credited_or_penalized():
    from core.registries import ABSENT, population_from_values
    from core.types import TypedSignature
    p = population_from_values("COLOR", (0.5, 0.0, 0.0, 0.4, 1.0))
    q = population_from_values("COLOR", (0.5, None, 0.0, 0.4, 1.0))
    a = TypedSignature(kind="CANONICAL", class_="COLOR", relation="x",
                       quantized=(4., 4., 4., 3., 4.), population=p)
    b = TypedSignature(kind="CANONICAL", class_="COLOR", relation="x",
                       quantized=(4., ABSENT, 4., 3., 4.), population=q)
    assert a.similarity(b) == pytest.approx(1.0)
    empty = TypedSignature(kind="CANONICAL", class_="COLOR", relation="x",
                           quantized=(ABSENT,) * 5, population=q)
    assert a.similarity(empty) == 0.0


def test_named_feature_preserves_distinct_populations_and_class_gate():
    from core.graded_features import NamedFeature, with_features
    from core.registries import population_from_values
    from core.types import TypedSignature
    def sig(cls, q, pop=()):
        return TypedSignature(kind="CANONICAL", class_=cls, relation="x", quantized=q, population=pop)
    red = sig("COLOR", (1., 2., 3., 4., 5.), population_from_values("COLOR", (0.2, 0., 0., 0.5, 1.0)))
    red2 = sig("COLOR", red.quantized, population_from_values("COLOR", (0.3, 0., 0., 0.5, 1.0)))
    frame = sig("TEXTURE", (1., 2.))
    f1, f2 = NamedFeature("color", "Color", red), NamedFeature("color", "Color", red2)
    decorated = with_features(frame, (f1, f2))
    assert decorated.quantized == frame.quantized and len(decorated._named_features) == 2
    other = with_features(sig("BOUNDARY", (1., 2.)), (f1,))
    assert decorated.similarity(other) == 0.0


def test_direct_curve_complex_has_registered_population_and_missing_arc():
    from core.registries import ABSENT
    from core.types import Detection, TypedSignature
    from lenses.v4 import CurveComplexLens_B13
    sig = TypedSignature(kind="CANONICAL", class_="CONTOUR", relation="x",
                         quantized=(1., 2., 3., 0., 4., 5., 4.))
    det = Detection(k="Contour", source_layer=2, scale=0, sigma=sig,
                    alpha=1, z=1., t=0, rho=(("entity", 1, 0, "+"),))
    lens = CurveComplexLens_B13()
    (out,) = lens._emit_cluster(0, [det], [], {1: (0., 0.)}, 1.)
    assert len(out.sigma.quantized) == len(out.sigma.population) == 44
    assert out.sigma.quantized[-20:] == (ABSENT,) * 20


def test_lattice_isotropy_is_not_spatial_elongation():
    import numpy as np
    from perception.contour_structure import V1RetinotopicLattice
    lattice = V1RetinotopicLattice(density=1, overlap_factor=2)
    energy = np.zeros((2, 1, 9, 9))
    # Uniform directions but a spatially narrow vertical energy footprint.
    energy[:, 0, :, 4] = 1.0
    regions = lattice.tile_with_features(9, 9, energy, np.array([0., np.pi / 2]),
                                         np.array([1.]), np.zeros((9, 9)),
                                         np.zeros((9, 9, 3)))
    assert regions[0]["isotropy"] == pytest.approx(1.0)
    assert regions[0]["elongation"] == pytest.approx(0.0)


def test_perceptual_selection_family_seeds_budget_and_metadata():
    from core.graph_types import Subgraph
    from core.types import EdgeType, TypedSignature
    from matching.perceptual_selection import select_perceptual_graph
    sigs = {i: ("Contour" if i != 6 else "Color",
                TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x", quantized=(float(i), 1.)))
            for i in range(7)}
    a = (0, 1, EdgeType.CONTOUR_CONTINUITY)
    b = (1, 2, EdgeType.CONTOUR_CONTINUITY)
    c = (2, 3, EdgeType.JUNCTION_CONTOUR)
    d = (3, 4, EdgeType.JUNCTION_CONTOUR)
    attr = (0, 6, EdgeType.CO_LOCATED)
    g = Subgraph(nodes=frozenset(sigs), edges=frozenset((a, b, c, d, attr)),
                 weights={a: 0.2, b: 0.9, c: 0.8, d: 0.1, attr: 1.0},
                 anchor_of_node={i: (float(i), 0.) for i in sigs})
    selected, diag = select_perceptual_graph(g, sigs.get, budget=2, family_seeds=1)
    assert selected.edges == frozenset((b, c))
    assert selected.weights == {b: 0.9, c: 0.8}
    assert 5 in selected.nodes and 6 not in selected.nodes
    assert diag["selected_edges"] == 2 and not diag["structural_families_missing"]
    assert select_perceptual_graph(g, sigs.get, budget=2, family_seeds=1)[0].edges == selected.edges


def test_registered_attributes_attach_without_mutating_frame_identity():
    from core.graph_types import Subgraph
    from core.types import EdgeType, TypedSignature
    from core.registries import population_from_values
    from matching.feature_attachment import attach_named_features
    frame = TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x", quantized=(1., 2.))
    color = TypedSignature(kind="CANONICAL", class_="COLOR", relation="x", quantized=(1., 2., 3., 4., 5.),
                           population=population_from_values("COLOR", (0.2, 0., 0., 0.5, 1.0)))
    position = TypedSignature(kind="CANONICAL", class_="POSITION", relation="x", quantized=(1., 2., 3.))
    provider = {0: ("Contour", frame), 1: ("Color", color), 2: ("Position", position)}
    graph = Subgraph(nodes=frozenset(provider), edges=frozenset({(0, 1, EdgeType.CO_LOCATED),
                                                                  (2, 0, EdgeType.CO_LOCATED)}))
    overrides = attach_named_features(graph, provider.get)
    assert set(overrides) == {0}
    enriched = overrides[0][1]
    assert enriched.serialize() == frame.serialize()
    assert len(enriched._named_features) == 1
    assert enriched._named_features[0].signature.population == color.population
    assert not hasattr(frame, "_named_features")
    assert enriched.similarity(frame) == pytest.approx(0.5)


def test_repeated_named_features_use_all_measurements_symmetrically():
    from core.graded_features import NamedFeature, with_features
    from core.types import TypedSignature
    def sig(cls, *q):
        return TypedSignature(kind="CANONICAL", class_=cls, relation="x", quantized=tuple(map(float, q)))
    physical = sig("TEXTURE", 2, 3)
    first, second = sig("TEXTURE", 0, 0), sig("TEXTURE", 7, 7)
    def feature(value):
        return NamedFeature("texture", "Texture", value)
    left = with_features(physical, [feature(first), feature(second)])
    right = with_features(physical, [feature(first)])
    assert left.similarity(right) == pytest.approx(0.75)
    assert right.similarity(left) == pytest.approx(0.75)


def test_live_spatial_situation_selects_and_attaches_product_path():
    from pathlib import Path
    import matching.perceptual_selection as selection
    import matching.feature_attachment as attachment
    import memory.mapper as mapper_module
    import orchestration.pipeline as pipeline_module
    from concept_graph import ConceptGraph
    from core.hashing import _node_signature_hash
    from core.types import EdgeType, TypedSignature
    from memory.cores import CoreLibrary
    from memory.content import ContentSignatureStore, build_content_subgraph
    root = Path(__file__).resolve().parents[1]
    for module in (selection, attachment, mapper_module, pipeline_module):
        assert Path(module.__file__).resolve().is_relative_to(root)
    cg = ConceptGraph()
    nodes = []
    for i in range(35):
        sig = TypedSignature(kind="CANONICAL", class_="CONTOUR", relation="x",
                             quantized=(float(i), 1., 2., 0., 3., 4., 4.) + (4.,) * 20)
        nodes.append(cg.get_or_create_pattern_node("Contour", _node_signature_hash(sig), signature=sig))
    color = TypedSignature(kind="CANONICAL", class_="COLOR", relation="x",
                           quantized=(1., 2., 3., 4., 5.))
    color_id = cg.get_or_create_pattern_node("Color", _node_signature_hash(color), signature=color)
    pos = TypedSignature(kind="CANONICAL", class_="POSITION", relation="x", quantized=(1., 2., 3.))
    pos_id = cg.get_or_create_pattern_node("Position", _node_signature_hash(pos), signature=pos)
    for i, u in enumerate(nodes):
        for v in nodes[i + 1:]:
            cg.upsert_edge(u, v, EdgeType.CONTOUR_CONTINUITY, 0.7, 0)
    cg.upsert_edge(nodes[0], nodes[1], EdgeType.JUNCTION_CONTOUR, 0.9, 0)
    cg.upsert_edge(nodes[2], nodes[3], EdgeType.JUNCTION_CONTOUR, 0.8, 0)
    cg.upsert_edge(nodes[0], color_id, EdgeType.CO_LOCATED, 1.0, 0)
    cg.upsert_edge(nodes[0], pos_id, EdgeType.CO_LOCATED, 1.0, 0)
    provider = pipeline_module.make_signature_provider(cg)
    mapper = mapper_module.Mapper(cg, CoreLibrary(), provider)
    with frontend_contract():
        result = mapper._spatial_situation(0)
    assert len(result.edges) == 512
    assert sum(e[2] == EdgeType.JUNCTION_CONTOUR for e in result.edges) == 2
    assert color_id not in result.nodes and pos_id not in result.nodes
    assert result.signature_overrides[nodes[0]][1]._named_features[0].signature == color
    assert not hasattr(provider(nodes[0])[1], "_named_features")
    assert mapper.diagnostics["perceptual_selection"]["selected_edges"] == 512
    store = ContentSignatureStore()
    build_content_subgraph(result, provider, store)
    assert any(getattr(info[1], "_named_features", ()) for info in store._sigs.values())


def test_fuzzy_singleton_edgeless_identical_is_not_vacuous_one():
    from core.graph_types import Subgraph
    from core.types import TypedSignature
    from matching.fuzzy import fuzzy_match
    signature = TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x", quantized=(2., 3.))
    provider = {1: ("Texture", signature), 2: ("Texture", signature)}.get
    result = fuzzy_match(Subgraph(nodes=frozenset({1})), Subgraph(nodes=frozenset({2})), provider)
    assert result.chance == pytest.approx(0.0)
    assert result.score == pytest.approx(0.5)


def test_live_hierarchy_retains_members_and_lifts_contour_direction():
    from pathlib import Path
    import memory.mapper as mm
    from concept_graph import ConceptGraph
    from core.hashing import _node_signature_hash
    from core.registries import ABSENT, population_from_values
    from core.types import EdgeType, TypedSignature
    from memory.cores import CoreLibrary
    from orchestration.pipeline import make_signature_provider
    assert Path(mm.__file__).resolve().is_relative_to(Path(__file__).resolve().parents[1])
    cg = ConceptGraph()
    contour = TypedSignature(kind="CANONICAL", class_="CONTOUR", relation="x",
                             quantized=(2., 3., 4., 0., 2., 3., 4.) + (4.,) * 20)
    complex_sig = TypedSignature(kind="CANONICAL", class_="CURVE_COMPLEX", relation="x",
                                 quantized=(1.,) * 44)
    c = cg.get_or_create_pattern_node("Contour", _node_signature_hash(contour), signature=contour)
    p = cg.get_or_create_pattern_node("CurveComplex", _node_signature_hash(complex_sig), signature=complex_sig)
    cg.upsert_edge(p, c, EdgeType.CURVE_CONTAINMENT, 1., 0)
    mapper = mm.Mapper(cg, CoreLibrary(), make_signature_provider(cg))
    with frontend_contract():
        graph = mapper.build_situation_subgraph(0)
    assert {p, c} <= graph.nodes
    assert (p, c, EdgeType.CURVE_CONTAINMENT) in graph.edges
    for n in (p, c):
        features = graph.signature_overrides[n][1]._named_features
        direction = next(f for f in features if f.name == "contour_direction").signature
        assert direction.quantized[1:3] == (3., 4.)
        assert direction.quantized[0] == ABSENT


def test_filter_keeps_discriminative_relational_unit_with_shared_endpoints():
    from pathlib import Path
    import consolidator
    from core.graph_types import Subgraph
    from core.types import EdgeType, TypedSignature
    assert Path(consolidator.__file__).resolve().is_relative_to(Path(__file__).resolve().parents[1])
    sigs = {i: ("Contour", TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x",
                                         quantized=(float(i), 1.))) for i in (1, 2)}
    edge = (1, 2, EdgeType.CONTOUR_CONTINUITY)
    pos = Subgraph(nodes=frozenset(sigs), edges=frozenset({edge}))
    neg = Subgraph(nodes=frozenset(sigs))
    result, diag, _ = consolidator._content_discriminative_filter(
        pos, [pos] * 4, [neg] * 4, sigs.get, 0., 0., 0.,
        top_k_nodes=2, top_k_edges=1, dual_enabled=False)
    assert result.edges == frozenset({edge})
    assert result.nodes == frozenset({1, 2})
    assert diag["nodes_promoted_by_edge"] == 2
    assert result.node_weights[1] > 0 and result.weights[edge] > 0
    capped, diag, _ = consolidator._content_discriminative_filter(
        pos, [pos] * 4, [neg] * 4, sigs.get, 0., 0., 0.,
        top_k_nodes=1, top_k_edges=1, dual_enabled=False)
    assert not capped.edges and len(capped.nodes) <= 1


def test_live_junction_emits_extended_families_and_registered_alias():
    from pathlib import Path
    import math
    import lenses.v2 as v2
    from lenses.derived_common import JUNCTION_FAMILY_KINDS, junction_alias, LENS_DECLARATION_BY_NAME
    from matching.relation_frame import FRAME_LENS_TYPES, FRAME_LENS_EXTENSIONS, is_frame
    from memory.content import CONTENT_LENS_TYPES, content_signature, _JUNCTION_FAMILY_KINDS
    from memory.cores import lens_tier
    from core.hashing import _node_signature_hash
    from core.types import Detection, EdgeType, TypedSignature
    from concept_graph import ConceptGraph
    assert Path(v2.__file__).resolve().is_relative_to(Path(__file__).resolve().parents[1])
    assert JUNCTION_FAMILY_KINDS == _JUNCTION_FAMILY_KINDS == ("Corner", "T", "Y")
    assert not FRAME_LENS_TYPES.intersection(FRAME_LENS_EXTENSIONS)
    assert {"L", "Arrow"}.issubset(LENS_DECLARATION_BY_NAME["Junction"].also_produces)
    def emit(angles):
        cg = ConceptGraph()
        points = [(10., 10.)] + [(10. + math.cos(a), 10. + math.sin(a)) for a in angles]
        dets, ids, positions = [], [], {}
        for i, xy in enumerate(points):
            sig = TypedSignature(kind="CANONICAL", class_="ORIENTATION", relation="x",
                                 quantized=(float(i), 1., 0.))
            det = Detection(k="Orientation", source_layer=0, scale=0, sigma=sig,
                            alpha=i, z=1., t=0, rho=(("entity", i, 0, "+"),))
            dets.append(det)
            positions[i] = xy
            ids.append(cg.get_or_create_pattern_node(det.k, _node_signature_hash(sig), signature=sig))
        for n in ids[1:]:
            cg.upsert_edge(ids[0], n, EdgeType.ORIENTATION_BEND, 1., 0)
        with frontend_contract():
            return v2.JunctionLens().step(0, cg, None, positions, None,
                                          {"Orientation": dets}, extraction_scale=2.)
    for kind, angles in (("L", (0., math.pi/2)), ("Arrow", (0., math.pi/3, 2*math.pi/3))):
        emitted = emit(angles)
        det = next(d for d in emitted if d.k == kind)
        assert det in junction_alias(emitted)
        assert is_frame(kind) and kind in CONTENT_LENS_TYPES and lens_tier(kind) == 1
        assert content_signature(kind, det.sigma) is not None


def test_live_b7_incomparable_is_not_reintroduced_as_zero_evidence():
    from core.graph_types import Subgraph
    from core.schema import EdgeParams, polymorphic_edge_similarity
    from core.types import EdgeType, TypedSignature
    from memory.cores import evidence_score
    nodes = {i: ("Contour", TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x",
                                          quantized=(float(i), 1.))) for i in (1, 2)}
    qedge = (1, 2, EdgeType.CONTACT)
    cedge = (1, 2, EdgeType.BOUNDARY_ATTACHMENT)
    qparam = EdgeParams(class_="EDGE_CONTACT", quantized=(0., 0., 0.))
    cparam = EdgeParams(class_="EDGE_BOUNDARY_ATTACHMENT", quantized=(0., 0., 0.))
    assert polymorphic_edge_similarity(qparam, cparam, return_none=True) is None
    q = Subgraph(nodes=frozenset(nodes), edges=frozenset({qedge}), edge_params={qedge: qparam})
    c = Subgraph(nodes=frozenset(nodes), edges=frozenset({cedge}), edge_params={cedge: cparam})
    trace = {}
    with frontend_contract():
        score, _ = evidence_score(q, c, nodes, nodes, trace=trace)
    assert trace["incomparable_core_edges"] == 1
    assert trace["verifiable_core_edges_count"] == 0
    assert trace["relational_multiplier"] == pytest.approx(1.0)
    assert trace["edge_absence"] == 0.0
    assert score > 0.99


def test_live_category_query_does_not_undo_structure_selection():
    from concept_graph import ConceptGraph
    from core.graph_types import Subgraph
    from memory.cores import CoreLibrary
    from memory.mapper import Mapper
    mapper = Mapper(ConceptGraph(), CoreLibrary(), lambda _: None)
    window = Subgraph(nodes=frozenset(range(30)))
    with frontend_contract():
        assert mapper._extract_query_core_category(window, None) is window


def test_preparation_is_idempotent_even_without_an_overlay():
    from core.graph_types import Subgraph
    from core.types import TypedSignature
    from matching.perceptual_selection import prepare_perceptual_graph
    sig = TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x", quantized=(1.,))
    graph = Subgraph(nodes=frozenset({1}))
    first, _ = prepare_perceptual_graph(graph, lambda _: ("Contour", sig))
    second, diag = prepare_perceptual_graph(first, lambda _: ("Contour", sig))
    assert first is second and diag["already_prepared"] and not first.signature_overrides


def test_live_surface_missing_boundary_measurements_are_absent():
    from lenses.v4 import SurfaceLens
    from core.registries import ABSENT, slot_axes
    with frontend_contract():
        d = SurfaceLens()._emit_one(0, 1, 1., [], None, None, None, {}, None, {})
    names = [s.name for s, _ in slot_axes("SURFACE_PATCH")]
    for name in ("shape", "grad_mag", "grad_side"):
        i = names.index(name)
        assert d.sigma.quantized[i] == ABSENT
        assert len(set(d.sigma.population[i])) == 1


def test_content_store_does_not_pool_different_window_features():
    from core.types import TypedSignature
    from core.graded_features import NamedFeature, with_features
    from memory.content import ContentSignatureStore
    base = TypedSignature(kind="CANONICAL", class_="TEXTURE", relation="x", quantized=(1., 1.))
    a = with_features(base, [NamedFeature("Color", "Color", TypedSignature(kind="CANONICAL", class_="COLOR", relation="x", quantized=(1., 1., 1., 1., 1.)))])
    b = with_features(base, [NamedFeature("Color", "Color", TypedSignature(kind="CANONICAL", class_="COLOR", relation="x", quantized=(2., 1., 1., 1., 1.)))])
    with frontend_contract():
        store = ContentSignatureStore()
        aid, bid = store.resolve("Contour", a), store.resolve("Contour", b)
        assert aid != bid
        assert store.get(aid)[1]._named_features[0].signature.quantized[0] == 1.
        assert store.get(bid)[1]._named_features[0].signature.quantized[0] == 2.


def test_fuzzy_off_correspondence_null_excludes_selected_pairs(monkeypatch):
    import matching.fuzzy as fuzzy
    import matching.alignment as alignment
    from core.graph_types import Subgraph
    from core.types import TypedSignature
    sigs = {i: TypedSignature(kind='CANONICAL', class_='TEXTURE', relation='x', quantized=(float(i),)) for i in (1, 2, 3, 4)}
    matrix = {(1,3):.9, (1,4):.1, (2,3):.3, (2,4):.8}
    monkeypatch.setattr(fuzzy, '_sig_sim', lambda a,b: matrix[(int(a.quantized[0]),int(b.quantized[0]))])
    fake = alignment.Alignment({1:3,2:4},{1:.9,2:.8},1.,1.,1.,1.)
    monkeypatch.setattr(alignment, 'global_consistency_alignment', lambda *a,**k: fake)
    result=fuzzy.fuzzy_match(Subgraph(nodes=frozenset({1,2})),Subgraph(nodes=frozenset({3,4})),lambda i:('Texture',sigs[i]))
    assert result.chance == pytest.approx(.2)
    assert result.node_coverage_weighted == pytest.approx(.85)
    assert result.score == pytest.approx((.85-.2)/.8)
