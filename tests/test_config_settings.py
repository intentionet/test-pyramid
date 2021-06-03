from pybatfish.client.session import Session


def test_multipath_ebgp(bf: Session):
    """ Multipath must be turned on for all EBGP sessions in the network """
    bgp_process_props = bf.q.bgpProcessConfiguration().answer().frame()

