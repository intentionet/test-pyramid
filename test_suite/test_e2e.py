from pybatfish.client.session import Session
from pybatfish.datamodel import PathConstraints, HeaderConstraints

from test_suite.sot_utils import SoT, ALLOWED_CLIENT_PORTS, BLOCKED_SOURCES


def test_public_services(bf: Session, sot: SoT) -> None:
    path_constraints = PathConstraints(startLocation="internet")
    src_ips = '0.0.0.0/0 \ ({})'.format(",".join(BLOCKED_SOURCES))
    src_ports = f"{ALLOWED_CLIENT_PORTS.start}-{ALLOWED_CLIENT_PORTS.stop-1}"
    for service in sot.public_services:
        applications = ",".join(service["applications"])
        service_ips = ",".join(service["ips"])
        denied_flows = bf.q.reachability(pathConstraints=path_constraints,
                                         headers=HeaderConstraints(srcIps=src_ips,
                                                                   srcPorts=src_ports,
                                                                   dstIps=service_ips,
                                                                   applications=applications),
                                         actions="failure").answer().frame()
        assert denied_flows.empty, "Some traffic to {} is denied: {}".format(service["description"],
                                                                             denied_flows["Flow"])


def test_private_services(bf: Session, sot: SoT) -> None:
    path_constraints = PathConstraints(startLocation="internet")
    for service in sot.private_services:
        applications = ",".join(service["applications"])
        service_ips = ",".join(service["ips"])
        allowed_flows = bf.q.reachability(pathConstraints=path_constraints,
                                          headers=HeaderConstraints(dstIps=service_ips,
                                                                    applications=applications),
                                          actions="success").answer().frame()
        assert allowed_flows.empty, "Some traffic to {} is denied: {}".format(service["description"],
                                                                              allowed_flows["Flow"])

