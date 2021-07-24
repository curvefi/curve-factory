from functools import partial

import pytest
from brownie import ZERO_ADDRESS

# session level functions


def _deploy_plain_implementation(_project, _pool_size, _pool_type, _deployer):
    contract = getattr(_project, f"Plain{_pool_size}{_pool_type}")
    return contract.deploy({"from": _deployer})


@pytest.fixture(scope="session")
def deploy_plain_implementation(alice, project):
    return partial(_deploy_plain_implementation, _project=project, _deployer=alice)


@pytest.fixture(scope="module", autouse=True)
def set_plain_implementations(alice, factory, plain_implementations, plain_pool_size):
    factory.set_plain_implementations(
        plain_pool_size, plain_implementations + [ZERO_ADDRESS] * 6, {"from": alice}
    )


# function level functions


@pytest.fixture
def mint_alice(alice, initial_amounts, plain_coins):
    for coin, amount in zip(plain_coins, initial_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})


@pytest.fixture(scope="module")
def approve_alice(alice, plain_coins, swap):
    for coin in plain_coins:
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})


@pytest.fixture
def mint_bob(bob, initial_amounts, plain_coins):
    for coin, amount in zip(plain_coins, initial_amounts):
        coin._mint_for_testing(bob, amount, {"from": bob})


@pytest.fixture(scope="module")
def approve_bob(bob, plain_coins, swap):
    for coin in plain_coins:
        coin.approve(swap, 2 ** 256 - 1, {"from": bob})


@pytest.fixture(scope="module")
def add_initial_liquidity(alice, approve_alice, mint_alice, initial_amounts, swap):
    swap.add_liquidity(initial_amounts, 0, {"from": alice})
