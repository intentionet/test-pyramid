import ipaddress

from pybatfish.client.session import Session
from test_suite.sot_utils import SoT, SNAPSHOT_NODES_SPEC


def test_interface_ips(bf: Session, sot: SoT) -> None:
    interface_props = bf.q.interfaceProperties(nodes=SNAPSHOT_NODES_SPEC).answer().frame()
    for _, row in interface_props.iterrows():

        interface_name = row["Interface"].interface

        if not row["Active"] or \
                row["Access_VLAN"] or \
                row["Description"] == "[type=ISP]" or \
                interface_name in {"lo0", "xe-0/0/0", "xe-0/0/1"}:
            continue

        assert row["Primary_Address"], f'No address assigned to {row["Interface"]}'

        interface_address = ipaddress.ip_network(row["Primary_Address"], strict=False)

        expected_prefix_length = sot.get_interface_prefix_length(interface_name)
        assert interface_address.prefixlen == expected_prefix_length, "Unexpected prefix length {} for {}. Expected {}".format(
            interface_address.prefixlen, row["Interface"], expected_prefix_length)

        address_in_range = any([interface_address.subnet_of(prefix)
                                for prefix in sot.get_interface_prefixes(interface_name)])
        assert address_in_range, "Unexpected address {} for {}. Expected it to be in {}".format(
            interface_address, row["Interface"], sot.get_interface_prefixes(interface_name))


def _dup_ip_msg(dup_ip, dup_ip_group):
    return "{} ({})".format(dup_ip, ", ".join(dup_ip_group["Node"]))


def test_no_duplicate_ips(bf: Session) -> None:
    dup_ip_owners = bf.q.ipOwners(duplicatesOnly=True).answer().frame()
    dup_ip_groups = dup_ip_owners.groupby("IP")
    assert len(dup_ip_groups) == 0, "Found duplicate IPs: {}".format(
        ", ".join([_dup_ip_msg(dup_ip, dup_ip_group) for dup_ip, dup_ip_group in dup_ip_groups]))


def test_local_asns(bf: Session, sot: SoT) -> None:
    peer_props = bf.q.bgpPeerConfiguration(nodes=SNAPSHOT_NODES_SPEC).answer().frame()
    for _, row in peer_props.iterrows():
        node_name = row["Node"]
        asn_range = sot.get_node_asn_range(node_name)
        assert row["Local_AS"] in asn_range, \
            "Local AS of {} ({}) is outside of the expected range {}".format(
                node_name, row["Local_AS"], asn_range)


def test_duplicate_as(bf: Session) -> None:
    peer_props = bf.q.bgpPeerConfiguration(nodes=SNAPSHOT_NODES_SPEC).answer().frame()
    as_groups = peer_props.groupby("Local_AS")
    for local_as, as_group in as_groups:
        assert as_group["Node"].nunique() == 1, "ASN {} is duplicated on {}".format(
            local_as, ", ".join(as_group["Node"].unique()))


def test_remote_asns_non_spine(bf: Session, sot: SoT):
    peer_props = bf.q.bgpPeerConfiguration(nodes=f"{SNAPSHOT_NODES_SPEC} \ /spine.*/").answer().frame()
    for _, row in peer_props.iterrows():
        node_name = row["Node"]
        assert row["Peer_Group"], "Peer group is not set for neighbor {} on {}".format(row["Remote_IP"], node_name)
        peer_group = row["Peer_Group"].lower()
        if peer_group.startswith("isp"):
            continue
        asn_range = sot.get_peer_group_asn_range(peer_group)
        assert int(row["Remote_AS"]) in asn_range, \
            "Remote AS of neighbor {} ({}) in peer group '{}' on {} is outside of the expected range {}".format(
                row["Remote_IP"], row["Remote_AS"], peer_group, node_name, asn_range)


def _in_range(input_range: str, valid_range: range):
    (input_low, input_high) = [int(end) for end in input_range.split('-')]
    return input_low in valid_range and input_high in valid_range


def test_remote_as_spine(bf: Session, sot: SoT):
    peer_props = bf.q.bgpPeerConfiguration(nodes="/spine.*/").answer().frame()
    leaf_range = sot.get_peer_group_asn_range("leaf")
    bl_range = sot.get_peer_group_asn_range("bl")
    for _, row in peer_props.iterrows():
        node_name = row["Node"]
        remote_as_ranges = row["Remote_AS"].split(",")
        for remote_as_range in remote_as_ranges:
            assert _in_range(remote_as_range, leaf_range) or \
                   _in_range(remote_as_range, bl_range), \
                "Remote AS range {} on {} is invalid".format(remote_as_range, node_name)


def test_multipath_ebgp_on_leafs(bf: Session) -> None:
    proc_props = bf.q.bgpProcessConfiguration(nodes="/leaf.*/").answer().frame()
    non_multipath = proc_props[proc_props["Multipath_EBGP"] == False]
    assert len(non_multipath) == 0, "Routers without EBGP multipath: {}".format(",".join(non_multipath["Node"]))
