from functools import partial

import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

# session level functions


def _deploy_plain_implementation(_project, _pool_size, _pool_type, _deployer):
    contract = getattr(_project, f"Plain{_pool_size}{_pool_type}")
    return contract.deploy({"from": _deployer})


@pytest.fixture(scope="session")
def deploy_plain_implementation(alice, project):
    return partial(_deploy_plain_implementation, _project=project, _deployer=alice)


@pytest.fixture(scope="module", autouse=True)
def set_plain_implementations(
    alice, factory, plain_implementations, plain_pool_size, mod_isolation
):
    factory.set_plain_implementations(
        plain_pool_size, plain_implementations + [ZERO_ADDRESS] * 6, {"from": alice}
    )


@pytest.fixture(scope="module", autouse=True)
def set_meta_implementations(
    alice, factory, base_pool, meta_implementations, pool_type, fee_receiver, mod_isolation
):
    if pool_type not in [4, 5, 6, 7]:
        return
    asset_type = 0 if pool_type == 4 else 2 if pool_type == 5 else 3
    factory.add_base_pool(
        base_pool,
        fee_receiver,
        asset_type,
        meta_implementations + [ZERO_ADDRESS] * 8,
        {"from": alice},
    )


@pytest.fixture(scope="session")
def set_gauge_implementation(alice, factory, gauge_implementation):
    factory.set_gauge_implementation(gauge_implementation, {"from": alice})


@pytest.fixture(scope="session")
def eth_amount(is_eth_pool):
    return lambda amount: amount if is_eth_pool else 0


# function level functions


@pytest.fixture
def mint_alice(alice, initial_amounts, coins):
    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            continue
        coin._mint_for_testing(alice, amount, {"from": alice})


@pytest.fixture(scope="module")
def approve_alice(alice, coins, swap):
    for coin in coins:
        if coin == ETH_ADDRESS:
            continue
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})


@pytest.fixture
def mint_bob(bob, initial_amounts, coins):
    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            continue
        coin._mint_for_testing(bob, amount, {"from": bob})


@pytest.fixture(scope="module")
def approve_bob(bob, coins, swap):
    for coin in coins:
        if coin == ETH_ADDRESS:
            continue
        coin.approve(swap, 2 ** 256 - 1, {"from": bob})


@pytest.fixture
def mint_alice_underlying(alice, initial_amounts_underlying, underlying_coins):
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        if coin == ETH_ADDRESS:
            continue
        coin._mint_for_testing(alice, amount, {"from": alice})


@pytest.fixture(scope="module")
def approve_alice_underlying(alice, underlying_coins, swap):
    for coin in underlying_coins:
        if coin == ETH_ADDRESS:
            continue
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})


@pytest.fixture
def mint_bob_underlying(bob, initial_amounts_underlying, underlying_coins):
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        if coin == ETH_ADDRESS:
            continue
        coin._mint_for_testing(bob, amount, {"from": bob})


@pytest.fixture(scope="module")
def approve_bob_underlying(bob, underlying_coins, swap):
    for coin in underlying_coins:
        if coin == ETH_ADDRESS:
            continue
        coin.approve(swap, 2 ** 256 - 1, {"from": bob})


@pytest.fixture
def add_initial_liquidity(alice, approve_alice, mint_alice, initial_amounts, swap, eth_amount):
    swap.add_liquidity(initial_amounts, 0, {"from": alice, "value": eth_amount(initial_amounts[0])})


@pytest.fixture
def approve_zap(alice, bob, coins, base_coins, swap, zap):
    for token in [*coins, *base_coins, swap]:
        token.approve(zap, 2 ** 256 - 1, {"from": alice})
        token.approve(zap, 2 ** 256 - 1, {"from": bob})
