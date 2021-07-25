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

pool_types = {"basic": 0, "eth": 1, "optimized": 2, "rebase": 3}
return_types = {"revert": 0, "False": 1, "None": 2}


def pytest_addoption(parser):
    parser.addoption(
        "--plain-pool-size",
        action="store",
        default="2,3,4",
        help="comma-separated list of plain pool sizes to test against",
    )
    parser.addoption(
        "--plain-pool-type",
        action="store",
        default="basic,eth,optimized,rebase",
        help="comma-separated list of plain pool sizes to test against",
    )
    parser.addoption(
        "--return-type",
        action="store",
        default="revert,False,None",
        help="comma-separated list of ERC20 token return types to test against",
    )


def pytest_generate_tests(metafunc):
    if "plain_pool_size" in metafunc.fixturenames:
        cli_options = metafunc.config.getoption("plain_pool_size").split(",")
        pool_sizes = [int(v) for v in cli_options]
        metafunc.parametrize(
            "plain_pool_size",
            pool_sizes,
            indirect=True,
            ids=[f"(PoolSize={i})" for i in cli_options],
        )
    if "plain_pool_type" in metafunc.fixturenames:
        cli_options = metafunc.config.getoption("plain_pool_type").split(",")
        pool_type_ids = [pool_types[v] for v in cli_options]
        metafunc.parametrize(
            "plain_pool_type",
            pool_type_ids,
            indirect=True,
            ids=[f"(PoolType={i})" for i in cli_options],
        )
    if "return_type" in metafunc.fixturenames:
        cli_options = metafunc.config.getoption("return_type").split(",")
        return_type_ids = [return_types[v] for v in cli_options]
        metafunc.parametrize(
            "return_type",
            return_type_ids,
            indirect=True,
            ids=[f"(ReturnType={i})" for i in cli_options],
        )


def pytest_collection_modifyitems(config, items):
    for item in items.copy():
        try:
            params = item.callspec.params
            pool_type = params["plain_pool_type"]
            return_type = params["return_type"]
        except Exception:
            continue

        # optimized pool only supports return True/revert
        if pool_type == 2 and return_type != "revert":
            items.remove(item)

    # hacky magic to ensure the correct number of tests is shown in collection report
    config.pluginmanager.get_plugin("terminalreporter")._numcollected = len(items)


@pytest.fixture(scope="session")
def plain_pool_size(request):
    return request.param


@pytest.fixture(scope="session")
def plain_pool_type(request):
    return request.param


@pytest.fixture(scope="session")
def project():
    return get_loaded_projects()[0]


@pytest.fixture(scope="session")
def is_forked():
    return "fork" in CONFIG.active_network["id"]


@pytest.fixture(scope="module", autouse=True)
def mod_isolation(chain):
    chain.snapshot()
    yield
    chain.revert()


@pytest.fixture(autouse=True)
def isolation(chain, history):
    start = len(history)
    yield
    end = len(history)
    if end - start > 0:
        chain.undo(end - start)
