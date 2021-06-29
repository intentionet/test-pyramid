import pytest

from pybatfish.client.session import Session

from test_suite.sot_utils import NodePair, SoT, SNAPSHOT_NODES_SPEC


@pytest.mark.network_independent
def test_no_incompatible_bgp_sessions(bf: Session) -> None:
    bgp_session_status = bf.q.bgpSessionStatus().answer().frame()
    unestablished_sessions = bgp_session_status[bgp_session_status["Established_Status"] != "ESTABLISHED"]
    assert unestablished_sessions.empty, \
        "Found BGP sessions that will not be established: {}".format(unestablished_sessions.to_dict(orient="records"))


def test_layer3_edges(bf: Session, sot: SoT) -> None:
    """Check that all and only expected Layer3 edges are present."""
    # We check for L3 edges at the node-pair level, not interface level.
    # This suffices since we have only one edge between node pairs.
    layer3_edges = bf.q.layer3Edges(nodes=SNAPSHOT_NODES_SPEC,
                                    remoteNodes=SNAPSHOT_NODES_SPEC).answer().frame()
    layer3_node_pairs = {NodePair(node1=row["Interface"].hostname, node2=row["Remote_Interface"].hostname)
                         for _, row in layer3_edges.iterrows()}
    assert layer3_node_pairs == sot.get_connected_node_pairs()


def test_bgp_edges(bf: Session, sot: SoT) -> None:
    """Check that all and only expected BGP edges are present."""
    bgp_edges = bf.q.bgpEdges(nodes=SNAPSHOT_NODES_SPEC,
                              remoteNodes=SNAPSHOT_NODES_SPEC).answer().frame()
    bgp_node_pairs = {NodePair(node1=row["Node"], node2=row["Remote_Node"])
                      for _, row in bgp_edges.iterrows()}
    assert bgp_node_pairs == sot.get_connected_node_pairs()
