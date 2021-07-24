import pytest
from brownie_tokens import ERC20


@pytest.fixture(scope="session")
def _plain_coins(alice):
    return [ERC20(deployer=alice) for _ in range(4)]


@pytest.fixture(scope="session")
def plain_coins(_plain_coins, plain_pool_size):
    return _plain_coins[:plain_pool_size]


@pytest.fixture(scope="session")
def decimals(plain_coins):
    return [coin.decimals() for coin in plain_coins]


@pytest.fixture(scope="session")
def initial_amounts(decimals):
    return [10_000 * 10 ** precision for precision in decimals]


@pytest.fixture(scope="session")
def deposit_amounts(decimals):
    return [1_000 * 10 ** precision for precision in decimals]
