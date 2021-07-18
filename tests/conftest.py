import pytest
from brownie import ZERO_ADDRESS

pytest_plugins = ["fixtures.accounts", "fixtures.coins", "fixtures.deployments"]


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


@pytest.fixture(scope="module", params=[0, 1])
def is_rebase(request):
    yield request.param


@pytest.fixture(scope="module")
def wrapped_decimals(wrapped_coins):
    yield [i.decimals() if i != ZERO_ADDRESS else 0 for i in wrapped_coins]


@pytest.fixture(scope="module")
def plain_decimals(plain_coins):
    yield [i.decimals() if i != ZERO_ADDRESS else 0 for i in plain_coins]


@pytest.fixture(scope="module")
def underlying_decimals(underlying_coins):
    yield [i.decimals() for i in underlying_coins]


@pytest.fixture(scope="module")
def initial_amounts(wrapped_decimals, base_pool):
    # 1e6 of each coin - used to make an even initial deposit in many test setups
    amounts = [10 ** i * 1000000 for i in wrapped_decimals]
    amounts[1] = amounts[1] * 10 ** 18 // base_pool.get_virtual_price()
    yield amounts


@pytest.fixture(scope="module")
def initial_amounts_underlying(underlying_decimals):
    # 1e6 of each coin - used to make an even initial deposit in many test setups
    amounts = [10 ** i * 1000000 for i in underlying_decimals]
    amounts[1:] = [i // 3 for i in amounts[1:]]
    yield amounts


# shared logic for pool and base_pool setup fixtures


def _add_liquidity(acct, swap, coins, amounts):
    swap.add_liquidity(amounts, 0, {"from": acct})


def _mint(acct, wrapped_coins, wrapped_amounts, underlying_coins, underlying_amounts):
    for coin, amount in zip(wrapped_coins, wrapped_amounts):
        coin._mint_for_testing(acct, amount, {"from": acct})

    for coin, amount in zip(underlying_coins[1:], underlying_amounts[1:]):
        coin._mint_for_testing(acct, amount, {"from": acct})


def _approve(owner, spender, *coins):
    for coin in set(x for i in coins for x in i):
        coin.approve(spender, 2 ** 256 - 1, {"from": owner})


# pool setup fixtures


@pytest.fixture()
def add_initial_liquidity(
    alice, mint_alice, approve_alice, underlying_coins, swap, initial_amounts
):
    # mint (10**7 * precision) of each coin in the pool
    _add_liquidity(alice, swap, underlying_coins, initial_amounts)


@pytest.fixture()
def mint_bob(bob, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(bob, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_bob(bob, swap, underlying_coins, wrapped_coins):
    _approve(bob, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def mint_alice(alice, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(alice, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_alice(alice, swap, underlying_coins, wrapped_coins):
    _approve(alice, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def approve_zap(alice, bob, zap, swap, underlying_coins, initial_amounts_underlying):
    for underlying, amount in zip(underlying_coins, initial_amounts_underlying):
        if underlying == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            continue
        underlying.approve(zap, 2 ** 256 - 1, {"from": alice})
        underlying.approve(zap, 2 ** 256 - 1, {"from": bob})

    swap.approve(zap, 2 ** 256 - 1, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": bob})


# Added for rebase tokens


@pytest.fixture(scope="module")
def wrapped_rebase_amounts(base_pool, wrapped_coins, wrapped_decimals):
    wrapped_amounts = [10 ** i * 1000000 for i in wrapped_decimals]
    wrapped_amounts[1] = wrapped_amounts[1] * 10 ** 18 // base_pool.get_virtual_price()
    yield wrapped_amounts


@pytest.fixture()
def mint_and_deposit(wrapped_rebase_coins, wrapped_rebase_amounts, alice, swap_rebase):
    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap_rebase, amount, {"from": alice})
    swap_rebase.add_liquidity(wrapped_rebase_amounts, 0, {"from": alice})
