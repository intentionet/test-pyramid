import ipaddress
import string
from typing import Dict, Any, List


def node_name_to_role(name: str) -> str:
    return name.rstrip(string.digits)


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


class SoT:

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def get_interface_prefix_length(self, interface_name) -> int:
        interface_type = _interface_name_to_type(interface_name)
        return self.data["ipam"][interface_type]["prefix_length"]

    def get_interface_prefixes(self, interface_name) -> List[ipaddress.IPv4Network]:
        interface_type = _interface_name_to_type(interface_name)
        return [ipaddress.ip_network(prefix) for prefix in self.data["ipam"][interface_type]["in_prefixes"]]

    def get_node_asn_range(self, node_name: str) -> range:
        node_role = node_name_to_role(node_name)
        asn_min = self.data["asn_range"][node_role]["min"]
        asn_max = self.data["asn_range"][node_role]["max"]
        return range(asn_min, asn_max + 1)

    def get_peer_group_asn_range(self, peer_group: str) -> range:
        asn_min = self.data["asn_range"][peer_group]["min"]
        asn_max = self.data["asn_range"][peer_group]["max"]
        return range(asn_min, asn_max + 1)


