import attr
import ipaddress
import os
import string
import yaml

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from typing import List, Set

# specification for all non-modeled snapshot nodes
SNAPSHOT_NODES_SPEC = '(/.*/ \\ /(isp|internet).*/)'

# how the roles connect in our network
CONNECTED_ROLES = {"leaf": ["spine"],
                   "spine": ["leaf", "bl"],
                   "bl": ["spine", "fwl"],
                   "fwl": ["bl", "bor"],
                   "bor": ["fwl"],
                   }

MALICIOUS_SOURCES = ["52.15.165.117/32",
                     "78.93.180.80/32",
                     "109.235.246.70/32",
                     "190.210.230.78/32",
                     "194.27.18.18/32",
                     "201.216.233.13/32"]

RFC1918 = ["10.0.0.0/8",
           "172.16.0.0/12",
           "192.168.0.0/16"]

MARTIANS = ["0.0.0.0/8",
            "127.0.0.0/8",
            "169.254.0.0/16"]

BLOCKED_PREFIXES = MALICIOUS_SOURCES + RFC1918 + MARTIANS

# Source port range that is never blocked in our network
OPEN_CLIENT_PORTS = "49152-65535"

# Physical interfaces that do not have IP addresses assigned (because we assign addresses to sub-interfaces)
INTERFACES_WITHOUT_ADDRESS = {"lo0", "xe-0/0/0", "xe-0/0/1"}

# names of structures used in the configs
BL_EXPORT_ROUTEMAP_NAME = "FABRIC_AGG"
BOR_INBOUND_ACL_NAME = "ISP-INBOUND"
BOR_IMPORT_ROUTEMAP_NAME = "IMPORT-PROVIDER-GENERIC"


@attr.s(frozen=True)
class NodePair:
    node1 = attr.ib(type=str)
    node2 = attr.ib(type=str)


class SoT:

    def __init__(self, sot_dir: str):
        self.asns = yaml.load(open(os.path.join(sot_dir, "asn_assignments.yml")), Loader=yaml.SafeLoader)
        self.ips = yaml.load(open(os.path.join(sot_dir, "ip_assignments.yml")), Loader=yaml.SafeLoader)
        self.inventory = InventoryManager(loader=DataLoader(), sources=[os.path.join(sot_dir, "inventory")])
        self.public_services = yaml.load(open(os.path.join(sot_dir, "public_services.yml")), Loader=yaml.SafeLoader)
        self.private_services = yaml.load(open(os.path.join(sot_dir, "private_services.yml")), Loader=yaml.SafeLoader)
        self.external_services = yaml.load(open(os.path.join(sot_dir, "external_services.yml")), Loader=yaml.SafeLoader)

    @staticmethod
    def interface_name_to_type(name: str) -> str:
        """Returns the interface type based on its name."""
        name_prefix = name.rstrip(string.digits + '/-.').lower()

        if name_prefix in {"lo", "loopback"}:
            return "loopback"
        if name_prefix in {"mgmt", "management"}:
            return "management"
        if name_prefix in {"ethernet", "xe", "eth"}:
            return "physical"
        if name_prefix in {"vlan"}:
            return "svi"

        raise ValueError(f"Unknown interface name prefix {name_prefix}")

    def node_name_to_role(self, name: str) -> str:
        """Returns the role of the node."""
        # In our inventory, role is the non-default group ('all'), and there should be only one such group.
        roles = list({group.get_name() for group in self.inventory.get_host(name).get_groups()} - {'all'})
        assert len(roles) == 1, f"Found {len(roles)} non-default groups for {name}"
        return roles[0]

    def get_interface_prefix_length(self, interface_name) -> int:
        """Returns expected prefix length for an interface."""
        interface_type = self.interface_name_to_type(interface_name)
        return self.ips["interface_types"][interface_type]["prefix_length"]

    def get_interface_prefixes(self, interface_name) -> List[ipaddress.IPv4Network]:
        """Returns prefixes from which the interface's address must be from."""
        return self.get_interface_prefixes_by_type(self.interface_name_to_type(interface_name))

    def get_interface_prefixes_by_type(self, interface_type) -> List[ipaddress.IPv4Network]:
        """Returns prefixes from which an interface type's addresses must be from."""
        return [ipaddress.ip_network(prefix) for prefix in self.ips["interface_types"][interface_type]["in_prefixes"]]

    def get_node_asn_range(self, node_name: str) -> range:
        """Returns the ASN range from which a router's ASN must be from."""
        return self.get_node_role_asn_range(self.node_name_to_role(node_name))

    def get_peer_group_asn_range(self, peer_group: str) -> range:
        """Returns the ASN range from which a peer group's ASN must be from."""
        # we use peer group names that correspond to node roles
        return self.get_node_role_asn_range(peer_group)

    def get_node_role_asn_range(self, node_role: str) -> range:
        """Returns the ASN range from which a router's ASN must be from."""
        asn_min = self.asns["node_roles"][node_role]["min"]
        asn_max = self.asns["node_roles"][node_role]["max"]
        return range(asn_min, asn_max + 1)

    def get_connected_node_pairs(self) -> Set[NodePair]:
        """Returns all pairs of nodes that we expect to be connected to each other."""
        edges = set()
        for host1 in self.inventory.get_hosts():
            role1 = self.node_name_to_role(host1.get_name())
            for host2 in self.inventory.get_hosts():
                role2 = self.node_name_to_role(host2.get_name())
                if role2 in CONNECTED_ROLES[role1]:
                    edges.add(NodePair(node1=host1.get_name(), node2=host2.get_name()))
        return edges
