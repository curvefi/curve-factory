import pytest
from brownie._config import CONFIG
from brownie.project.main import get_loaded_projects

pytest_plugins = [
    "fixtures.accounts",
    "fixtures.coins",
    "fixtures.constants",
    "fixtures.deployments",
    "fixtures.functions",
]


def pytest_addoption(parser):
    parser.addoption(
        "--plain-pool-size",
        action="store",
        default="2,3,4",
        help="comma-separated list of plain pool sizes to test against",
    )


def pytest_generate_tests(metafunc):
    if "plain_pool_size" in metafunc.fixturenames:
        pool_sizes = [int(v) for v in metafunc.config.getoption("plain_pool_size").split(",")]
        metafunc.parametrize("plain_pool_size", pool_sizes, indirect=True)


@pytest.fixture(scope="session")
def plain_pool_size(request):
    return request.param


@pytest.fixture(scope="session")
def project():
    return get_loaded_projects()[0]


@pytest.fixture(scope="session")
def is_forked():
    return "fork" in CONFIG.active_network["id"]


@pytest.fixture(scope="module", autouse=True)
def module_isolation(chain):
    start_height = chain.height
    yield
    end_height = chain.height
    if end_height - start_height:
        chain.undo(end_height - start_height)


@pytest.fixture(autouse=True)
def fn_isolation(module_isolation, chain):
    start_height = chain.height
    yield
    end_height = chain.height
    if end_height - start_height:
        chain.undo(end_height - start_height)
