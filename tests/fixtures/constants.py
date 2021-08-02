import pytest


@pytest.fixture(scope="session")
def initial_amounts(decimals):
    return [1_000_000 * 10 ** precision for precision in decimals]


@pytest.fixture(scope="session")
def initial_amounts_underlying(underlying_decimals):
    return [1_000_000 * 10 ** precision for precision in underlying_decimals]


@pytest.fixture(scope="session")
def deposit_amounts(decimals):
    return [1_000 * 10 ** precision for precision in decimals]
