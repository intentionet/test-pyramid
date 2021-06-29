import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import PathConstraints, HeaderConstraints

from test_suite.sot_utils import (SoT, BLOCKED_PREFIXES, SNAPSHOT_NODES_SPEC, OPEN_CLIENT_PORTS)


@pytest.mark.network_independent
def test_no_forwarding_loops(bf: Session) -> None:
    """Check that there are no forwarding loops in the network."""
    looping_flows = bf.q.detectLoops().answer().frame()
    assert looping_flows.empty, \
        "Found flows that loop: {}".format(looping_flows.to_dict(orient="records"))


@pytest.mark.network_independent
def test_subnet_multipath_consistency(bf: Session) -> None:
    """
    Check that all flows between all pairs are multipath consistent.

    Searches across all flows between subnets that are treated differently (i.e., dropped versus forwarded)
    by different paths in the network and returns example flows.
    """
    multipath_inconsistent_flows = bf.q.subnetMultipathConsistency().answer().frame()
    assert multipath_inconsistent_flows.empty, \
        "Found flows that are multipath inconsistent: {}".format(multipath_inconsistent_flows.to_dict(orient="records"))


def test_public_services(bf: Session, sot: SoT) -> None:
    """Check that all public services are accessible from the Internet."""
    for service in sot.public_services:
        failed_flows = bf.q.reachability(
            pathConstraints=PathConstraints(startLocation="internet"),
            headers=HeaderConstraints(
                srcIps='0.0.0.0/0 \\ ({})'.format(",".join(BLOCKED_PREFIXES)),
                srcPorts=OPEN_CLIENT_PORTS,
                dstIps=",".join(service["ips"]),
                applications=",".join(service["applications"])),
            actions="failure").answer().frame()
        assert failed_flows.empty, \
            "Some flows to public service '{}' fail: {}".format(service["description"],
                                                                failed_flows["Flow"])


def test_private_services(bf: Session, sot: SoT) -> None:
    """Check that all private services are inaccessible from the Internet."""
    for service in sot.private_services:
        allowed_flows = bf.q.reachability(
            pathConstraints=PathConstraints(startLocation="internet"),
            headers=HeaderConstraints(
                dstIps=",".join(service["ips"]),
                applications=",".join(service["applications"])),
            actions="success").answer().frame()
        assert allowed_flows.empty, \
            "Some traffic to private service {} is allowed: {}".format(service["description"],
                                                                       allowed_flows["Flow"])


def test_external_services(bf: Session, sot: SoT) -> None:
    """Check that all external services are accessible from all leaf routers."""
    for service in sot.external_services:
        failed_flows = bf.q.reachability(
            pathConstraints=PathConstraints(startLocation="/leaf.*/"),
            headers=HeaderConstraints(
                dstIps=",".join(service["ips"]),
                applications=",".join(service["applications"])),
            actions="failure").answer().frame()
        assert failed_flows.empty, \
            "Some flows to external service {} fail: {}".format(service["description"],
                                                                failed_flows["Flow"])


def test_all_svi_prefixes_are_on_all_leafs(bf: Session, sot: SoT):
    """Check that all SVI prefixes are on all leafs."""
    all_leafs = set(sot.inventory.get_groups_dict()['leaf'])
    # for each prefix set on each vlan interface
    for svi_prefixes in bf.q.interfaceProperties(interfaces="/vlan.*/").answer().frame()['All_Prefixes']:
        for prefix in svi_prefixes:
            # each vlan prefix should be present on each leaf
            leafs_with_prefix = set(bf.q.routes(nodes="/leaf.*/",
                                                network=prefix).answer().frame()["Node"].unique())
            assert all_leafs == leafs_with_prefix


def test_default_route_presence(bf: Session, sot: SoT):
    """Check that all routers have the default route."""
    all_nodes = {host.get_name() for host in sot.inventory.get_hosts()}
    nodes_with_default = set(bf.q.routes(nodes=SNAPSHOT_NODES_SPEC,
                                         network="0.0.0.0/0").answer().frame()["Node"].unique())
    assert all_nodes == nodes_with_default
