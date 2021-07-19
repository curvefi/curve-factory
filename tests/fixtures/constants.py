import pytest
from brownie import ZERO_ADDRESS


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


@pytest.fixture(scope="module")
def wrapped_rebase_amounts(base_pool, wrapped_coins, wrapped_decimals):
    wrapped_amounts = [10 ** i * 1000000 for i in wrapped_decimals]
    wrapped_amounts[1] = wrapped_amounts[1] * 10 ** 18 // base_pool.get_virtual_price()
    yield wrapped_amounts
