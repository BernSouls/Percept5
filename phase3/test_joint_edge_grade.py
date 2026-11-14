"""The edge mass is graded and topology-only evidence is not physics."""
import pytest
from core.frontend_contract import frontend_contract
from core.graph_types import Subgraph
from core.schema import EdgeParams
from core.types import EdgeType,TypedSignature
from matching.joint_mcs import joint_mcs


def test_edge_parameter_distance_changes_balanced_score():
    s=TypedSignature(kind='CANONICAL',class_='TEXTURE',relation='x',quantized=(1.,1.))
    sa={1:('Contour',s),2:('Contour',s)};sb={11:('Contour',s),12:('Contour',s)}
    et=EdgeType.CONTOUR_CONTINUITY;ea=(1,2,et);eb=(11,12,et)
    p=EdgeParams('EDGE_CONTOUR_CONTINUITY',(1.,1.,1.))
    q=EdgeParams('EDGE_CONTOUR_CONTINUITY',(5.,1.,1.))
    a=Subgraph(nodes=frozenset(sa),edges=frozenset({ea}),edge_params={ea:p})
    b=Subgraph(nodes=frozenset(sb),edges=frozenset({eb}),edge_params={eb:q})
    exact=Subgraph(nodes=b.nodes,edges=b.edges,edge_params={eb:p})
    with frontend_contract():
        different=joint_mcs(a,b,sa,sb);identical=joint_mcs(a,exact,sa,sb)
    assert different.matched_edges==different.graded_edges==1
    assert different.mean_graded_edge_similarity==pytest.approx(2/3)
    assert different.score==pytest.approx(8/9)
    assert identical.score==pytest.approx(1.)
    assert different.score<identical.score


def test_feature_id_preserves_full_precision_and_historical_unfeatured_id():
    from core.graded_features import NamedFeature,with_features
    from core.hashing import serialize_float
    from memory.content import ContentSignatureStore,content_node_id
    a,b=.1234561,.1234562
    assert serialize_float(a)==serialize_float(b)
    frame=TypedSignature(kind='CANONICAL',class_='TEXTURE',relation='x',quantized=(1.,1.))
    def feature(v):
        return NamedFeature('Color','Color',TypedSignature(kind='CANONICAL',class_='COLOR',relation='x',quantized=(1.,1.,1.,1.,1.),population=((v,1-v),)))
    assert content_node_id('Contour',frame)==15594290172388952525
    with frontend_contract():
        store=ContentSignatureStore()
        assert store.resolve('Contour',frame)==15594290172388952525
        assert store.resolve('Contour',with_features(frame,[feature(a)])) != store.resolve('Contour',with_features(frame,[feature(b)]))


def test_duplicate_undirected_reversal_cannot_reuse_one_target_edge():
    s=TypedSignature(kind='CANONICAL',class_='TEXTURE',relation='x',quantized=(1.,1.))
    sa={1:('Contour',s),2:('Contour',s)};sb={11:('Contour',s),12:('Contour',s)}
    et=EdgeType.CONTOUR_CONTINUITY
    a=Subgraph(nodes=frozenset(sa),edges=frozenset({(1,2,et),(2,1,et)}))
    b=Subgraph(nodes=frozenset(sb),edges=frozenset({(11,12,et)}))
    with frontend_contract():r=joint_mcs(a,b,sa,sb)
    assert r.matched_edges==1
    assert r.score<=1.0
