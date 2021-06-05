from typing import Dict, Any

import pytest
import os
import sys
import yaml

from pybatfish.client.session import Session

# Set to true if you don't want to initialize snapshots and use one that is already initialized
#  - the BF_NETWORK and BF_SNAPSHOT environment variables must be set for this to work
# So, a valid way to run is "DEBUG_TESTS=True BF_NETWORK=mynetwoork BF_SNAPSHOT=mysnapshot pytest test_suite"
DEBUG_TESTS = bool(os.environ.get("DEBUG_TESTS", False))

BF_HOST = os.environ.get("BF_HOST", "localhost")

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
SNAPSHOT_DIR = os.path.join(REPO_DIR, "snapshot")
SOT_DIR = os.path.join(REPO_DIR, "SoT")

sys.path.append(REPO_DIR)

from test_suite.sot_utils import SoT, SNAPSHOT_NODES_SPEC


def _validate_snapshot(bf: Session, sot: SoT) -> None:
    """Check that snapshot matches inventory"""

    snapshot_nodes = set(bf.q.nodeProperties(nodes=SNAPSHOT_NODES_SPEC).answer().frame()["Node"])
    inventory_nodes = {host.get_name() for host in sot.inventory.get_hosts()}

    assert snapshot_nodes == inventory_nodes


@pytest.fixture(scope="session")
def bf(sot: SoT) -> Session:
    bf = Session.get(host=BF_HOST)
    if DEBUG_TESTS:
        bf.set_network(os.environ["BF_NETWORK"])
        bf.set_snapshot(os.environ["BF_SNAPSHOT"])
    else:
        bf.init_snapshot(SNAPSHOT_DIR)
    _validate_snapshot(bf, sot)
    return bf


@pytest.fixture(scope="session")
def sot() -> SoT:
    sot = SoT(SOT_DIR)
    return sot
