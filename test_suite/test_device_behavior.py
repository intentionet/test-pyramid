import ipaddress
import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import BgpRouteConstraints, HeaderConstraints

from test_suite.sot_utils import (SoT, BLOCKED_PREFIXES, BL_EXPORT_ROUTEMAP_NAME, BOR_INBOUND_ACL_NAME, MARTIANS,
                                  RFC1918, BOR_IMPORT_ROUTEMAP_NAME)


@pytest.mark.network_independent
def test_no_shadowed_filters(bf: Session) -> None:
    """
    Check that there are no shadowed lines in ACLs and firewall rules.

    Shadowed lines that those that will never match a packet because of earlier lines in the filter.
    """
    # ignoring filters that start with ~ ignores auto-generated filters in the BF model
    unreachable_lines = bf.q.filterLineReachability(filters="/^[^~]/").answer().frame()
    assert unreachable_lines.empty, \
        "Found unreachable filter lines: {}".format(unreachable_lines.to_dict(orient="records"))


def test_blocked_ip_space_at_bor_acl(bf: Session) -> None:
    """Check that no traffic from blocked IP space is permitted by border ACLs"""
    blocked_ip_space = ",".join(BLOCKED_PREFIXES)
    allowed_flows = bf.q.searchFilters(filters=BOR_INBOUND_ACL_NAME,
                                       headers=HeaderConstraints(srcIps=blocked_ip_space),
                                       action="permit").answer().frame()
    assert allowed_flows.empty, \
        "Some traffic from blocked space is allowed: {}".format(allowed_flows["Flow"])


def test_svi_specifics_denied_at_bl_rm(bf: Session, sot: SoT) -> None:
    """Check that more specific SVI prefixes are filtered at the border leafs."""
    specifics = [f"{prefix}:{prefix.prefixlen + 1}-32" for prefix in sot.get_interface_prefixes_by_type("svi")]

    answer = bf.q.searchRoutePolicies(nodes="/bl.*/",
                                      policies=BL_EXPORT_ROUTEMAP_NAME,
                                      inputConstraints=BgpRouteConstraints(prefix=specifics),
                                      action="permit").answer().frame()

    assert answer.empty, "Some SVI specifics are allowed by a 'bl' router"


def test_svi_aggregates_permitted_at_bl_rm(bf: Session, sot: SoT) -> None:
    """Check that SVI aggregates are permitted at the border leafs."""
    specifics = [f"{prefix}" for prefix in sot.get_interface_prefixes_by_type("svi")]

    answer = bf.q.searchRoutePolicies(nodes="/bl.*/",
                                      policies=BL_EXPORT_ROUTEMAP_NAME,
                                      inputConstraints=BgpRouteConstraints(prefix=specifics),
                                      action="deny").answer().frame()

    assert answer.empty, "SVI aggregate is denied by a 'bl' router"

    all_bl_nodes = set(sot.inventory.get_groups_dict()["bl"])
    answer = bf.q.searchRoutePolicies(nodes="/bl.*/",
                                      policies=BL_EXPORT_ROUTEMAP_NAME,
                                      inputConstraints=BgpRouteConstraints(prefix=specifics),
                                      outputConstraints=BgpRouteConstraints(communities="65535:1"),
                                      action="permit").answer().frame()
    community_attaching_nodes = set(answer["Node"].unique())

    assert all_bl_nodes == community_attaching_nodes, \
        "At least one node is not attaching the right community to the SVI aggregate prefix"


def test_blocked_prefixes_at_bor_rm(bf: Session) -> None:
    """Check that martians and private space is filtered at the data center border."""
    prefixes = [ipaddress.ip_network(prefix) for prefix in MARTIANS + RFC1918]
    blocked_prefixes = [f"{prefix}:{prefix.prefixlen}-32" for prefix in prefixes]

    answer = bf.q.searchRoutePolicies(nodes="/bor.*/",
                                      policies=BOR_IMPORT_ROUTEMAP_NAME,
                                      inputConstraints=BgpRouteConstraints(prefix=blocked_prefixes),
                                      action="permit").answer().frame()

    assert answer.empty, "Some meant-to-be-blocked prefix is allowed by 'bor' router"
