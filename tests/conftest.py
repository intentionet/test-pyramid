from typing import Dict, Any

import pytest
import os
import yaml

from pybatfish.client.session import Session

BF_HOST = os.environ.get("BF_HOST", "localhost")

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
SNAPSHOT_DIR = os.path.join(REPO_DIR, "snapshot")

MOCK_SOT = os.path.join(REPO_DIR, "mock_sot.yml")

@pytest.fixture(scope="session")
def bf() -> Session:
    bf = Session.get(host=BF_HOST)
    bf.init_snapshot(SNAPSHOT_DIR)
    return bf


def mock_sot() -> Dict[str, Any]:
    mock_sot = yaml.load(MOCK_SOT, Loader=yaml.SafeLoader)
    return mock_sot
