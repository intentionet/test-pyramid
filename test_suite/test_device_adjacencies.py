from pybatfish.client.session import Session

from test_suite.sot_utils import NodePair, SoT, SNAPSHOT_NODES_SPEC


def test_layer3_edges(bf: Session, sot: SoT) -> None:
    layer3_edges = bf.q.layer3Edges(nodes=SNAPSHOT_NODES_SPEC, remoteNodes=SNAPSHOT_NODES_SPEC).answer().frame()
    layer3_node_pairs = {NodePair(node1=row["Interface"].hostname,
                                  node2=row["Remote_Interface"].hostname) for _, row in layer3_edges.iterrows()}
    expected_layer3_node_pairs = sot.get_connected_node_pairs()

    assert layer3_node_pairs == expected_layer3_node_pairs


def test_bgp_edges(bf: Session, sot: SoT) -> None:
    bgp_edges = bf.q.bgpEdges(nodes=SNAPSHOT_NODES_SPEC, remoteNodes=SNAPSHOT_NODES_SPEC).answer().frame()
    layer3_node_pairs = {NodePair(node1=row["Node"],
                                  node2=row["Remote_Node"]) for _, row in bgp_edges.iterrows()}
    expected_bgp_node_pairs = sot.get_connected_node_pairs()

    assert layer3_node_pairs == expected_bgp_node_pairs

