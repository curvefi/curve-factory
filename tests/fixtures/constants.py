import pytest


@pytest.fixture(scope="session")
def initial_amounts(decimals):
    return [1_000_000 * 10 ** precision for precision in decimals]


@pytest.fixture(scope="session")
def initial_amounts_underlying(underlying_decimals):
    amts = [1_000_000 * 10 ** precision for precision in underlying_decimals]
    for i in range(1, len(underlying_decimals)):
        amts[i] //= 3
    return amts


@pytest.fixture(scope="session")
def deposit_amounts(decimals):
    return [1_000 * 10 ** precision for precision in decimals]
