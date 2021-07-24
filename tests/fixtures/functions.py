from functools import partial

import pytest


def _deploy_plain_implementation(_project, _pool_size, _pool_type, _deployer):
    contract = getattr(_project, f"Plain{_pool_size}{_pool_type}")
    return contract.deploy({"from": _deployer})


@pytest.fixture(scope="session")
def deploy_plain_implementation(alice, project):
    return partial(_deploy_plain_implementation, _project=project, _deployer=alice)
