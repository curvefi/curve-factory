import pytest

pytest_plugins = [
    "fixtures.accounts",
    "fixtures.actions",
    "fixtures.coins",
    "fixtures.constants",
    "fixtures.deployments",
]


def pytest_addoption(parser):
    parser.addoption(
        "--decimals",
        action="store",
        default=18,
        type=int,
        help="Number of decimal places for test token",
    )
    parser.addoption(
        "--return_value",
        action="store",
        default="True",
        help="Return value for test token",
    )


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass
