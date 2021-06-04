import attr
import ipaddress
import string
from typing import Dict, Any, List, Set

from ansible.inventory.manager import InventoryManager


def _interface_name_to_type(name: str) -> str:
    # remover trailing digits, slashes, dashes
    name_prefix = name.rstrip(string.digits + '/-.').lower()

    if name_prefix in {"lo", "loopback"}:
        return "loopback"
    if name_prefix in {"mgmt", "management"}:
        return "management"
    if name_prefix in {"ethernet", "xe", "eth"}:
        return "physical"
    if name_prefix in {"vlan"}:
        return "vlan"

    raise ValueError(f"Unknown interface name prefix {name_prefix}")


@attr.s(frozen=True)
class NodePair:

    node1 = attr.ib(type=str)
    node2 = attr.ib(type=str)


SNAPSHOT_NODES_SPEC = '(/.*/ \ /(isp|internet).*/)'

CONNECTED_ROLES = {
    "leaf" : ["spine"],
    "spine" : ["leaf", "bl"],
    "bl" : ["spine", "fwl"],
    "fwl" : ["bl", "bor"],
    "bor": ["fwl"],
}


class SoT:

    def __init__(self, data: Dict[str, Any], inventory: InventoryManager):
        self.data = data
        self.inventory = inventory

    def node_name_to_role(self, name: str) -> str:
        """Returns the role of the node.

        Per our inventory setup, role is the non-default group ('all'), and there should be only one such group.
        """
        roles = list({group.get_name() for group in self.inventory.get_host(name).get_groups()} - {'all'})
        assert len(roles) == 1, f"Found {len(roles)} non-default groups for {name}"
        return roles[0]

    def get_interface_prefix_length(self, interface_name) -> int:
        interface_type = _interface_name_to_type(interface_name)
        return self.data["ipam"][interface_type]["prefix_length"]

    def get_interface_prefixes(self, interface_name) -> List[ipaddress.IPv4Network]:
        interface_type = _interface_name_to_type(interface_name)
        return [ipaddress.ip_network(prefix) for prefix in self.data["ipam"][interface_type]["in_prefixes"]]

    def get_node_asn_range(self, node_name: str) -> range:
        node_role = self.node_name_to_role(node_name)
        asn_min = self.data["asn_range"][node_role]["min"]
        asn_max = self.data["asn_range"][node_role]["max"]
        return range(asn_min, asn_max + 1)

    def get_peer_group_asn_range(self, peer_group: str) -> range:
        asn_min = self.data["asn_range"][peer_group]["min"]
        asn_max = self.data["asn_range"][peer_group]["max"]
        return range(asn_min, asn_max + 1)

    def get_connected_node_pairs(self) -> Set[NodePair]:
        edges = set()
        for host1 in self.inventory.get_hosts():
            role1 = self.node_name_to_role(host1.get_name())
            for host2 in self.inventory.get_hosts():
                role2 = self.node_name_to_role(host2.get_name())
                if role2 in CONNECTED_ROLES[role1]:
                    edges.add(NodePair(node1=host1.get_name(), node2=host2.get_name()))
        return edges


