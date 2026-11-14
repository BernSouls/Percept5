"""Live unfiltered joint correspondence and deterministic incidence pins."""
from pathlib import Path
import pytest
import parameters as P
from core.frontend_contract import frontend_contract
from core.graph_types import Subgraph
from core.types import EdgeType, TypedSignature


def _sigs(nodes):
    return {i: ('Contour',TypedSignature(kind='CANONICAL',class_='TEXTURE',relation='x',quantized=(float(i),))) for i in nodes}


def test_live_edge_removal_changes_correspondence_and_is_one_to_one(monkeypatch):
    import memory.cores as cores
    import matching.joint_mcs as jm
    root=Path(__file__).resolve().parents[1]
    assert Path(jm.__file__).resolve().is_relative_to(root)
    assert Path(cores.__file__).resolve().is_relative_to(root)
    matrix=[[.67,.77,.59,.70],[.58,.55,.68,.60],[.69,.88,.57,.83],[.61,.91,.88,.64]]
    def sim(a,b):
        i,j=int(a.quantized[0]),int(b.quantized[0])
        return matrix[i-1][j-11] if i<10 else matrix[j-1][i-11]
    monkeypatch.setattr(cores,'_sig_similarity',sim)
    e=EdgeType.CONTOUR_CONTINUITY; a=[1,2,3,4]; b=[11,12,13,14]
    qa=Subgraph(nodes=frozenset(a),edges=frozenset({(1,2,e),(2,3,e),(3,4,e)}))
    cb=Subgraph(nodes=frozenset(b),edges=frozenset({(11,12,e),(12,13,e),(13,14,e)}))
    removed=Subgraph(nodes=cb.nodes,edges=cb.edges-{(12,13,e)})
    with frontend_contract():
        assert P.MATCH_GLOBAL_CONSISTENCY_ENABLED is True
        intact=jm.joint_mcs(qa,cb,_sigs(a),_sigs(b))
        altered=jm.joint_mcs(qa,removed,_sigs(a),_sigs(b))
        back=jm.joint_mcs(cb,qa,_sigs(b),_sigs(a))
    assert intact.mapping=={1:14,2:13,3:12,4:11}
    assert altered.mapping=={1:14,2:12,3:11,4:13}
    assert intact.mapping != altered.mapping
    for r in (intact,altered):
        assert len(r.mapping)==len(set(r.mapping))==len(set(r.mapping.values()))
    assert intact.matched_edges==3 and intact.graded_edges==0 and intact.presence_only_edges==3
    assert intact.mean_graded_edge_similarity is None
    assert intact.score==back.score


def test_live_reference_and_category_query_bypass_supervised_filter(monkeypatch):
    import consolidator
    import memory.mapper as mapper_module
    import matching.joint_mcs as jm
    from concept_graph import ConceptGraph
    root=Path(__file__).resolve().parents[1]
    for module in (consolidator,mapper_module,jm):
        assert Path(module.__file__).resolve().is_relative_to(root)
    sigs=_sigs([1,2]);e=EdgeType.CONTOUR_CONTINUITY
    graph=Subgraph(nodes=frozenset(sigs),edges=frozenset({(1,2,e)}),perceptual_prepared=True)
    cg=ConceptGraph();engine=consolidator.Consolidator(cg,sigs.get)
    def forbidden(*a,**k):raise AssertionError('supervised filtering invoked')
    monkeypatch.setattr(consolidator,'_content_discriminative_filter',forbidden)
    monkeypatch.setattr(consolidator,'_structural_intersection',forbidden)
    with frontend_contract():
        entry=engine.discriminative_core(0,('class','fixture'),[graph],[])
    assert entry is not None and entry.core_subgraph is graph
    assert entry.core_tier=='perceptual' and not entry.content_distribution
    mapper=mapper_module.Mapper(cg,engine.core_library,sigs.get)
    result=mapper.query_category(1,('class','fixture'),graph,read_only=True)
    assert len(result.labels)==1
    assert result.labels[0].label==('class','fixture')
    assert result.labels[0].raw_score==pytest.approx(1.)


def test_canonical_incidence_orders_directed_ties():
    import matching.structural_similarity as ss
    e=EdgeType.CONTOUR_CONTINUITY;sg=Subgraph(nodes=frozenset({1,2,3}),edges=frozenset({(2,1,e),(1,2,e),(2,3,e)}))
    inc=ss._incidence(sg,_sigs(sg.nodes))
    assert inc[1]==[(2,e,True),(2,e,False)]


def test_pipeline_uses_one_reference_without_negative_window_training():
    from types import SimpleNamespace
    import orchestration.pipeline as pipeline_module
    from memory.cores import CoreLibrary
    from core.handoff import LabelSignal
    assert Path(pipeline_module.__file__).resolve().is_relative_to(Path(__file__).resolve().parents[1])
    p=pipeline_module.Pipeline.__new__(pipeline_module.Pipeline)
    p.all_effect_flags={3}
    p.consolidator=SimpleNamespace(core_library=CoreLibrary())
    g=Subgraph(nodes=frozenset({1}))
    p.providers=SimpleNamespace(state_index=lambda state:g)
    p._derive_label_signals=lambda t:[LabelSignal(('effect_atom',3),1,t),LabelSignal(('effect_atom',4),-1,t)]
    calls=[]
    p._extract_category_core=lambda t,label,positives,negatives: calls.append((t,label,positives,negatives))
    with frontend_contract():p._update_label_windows(2,123)
    assert calls==[(2,('effect_atom',3),[g],[])]
