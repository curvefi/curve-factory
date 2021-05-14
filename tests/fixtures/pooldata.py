import pytest


@pytest.fixture(scope="module")
def underlying_decimals(pool_data, base_pool_data):
    # number of decimal places for each underlying coin in the active pool
    if pool_data["type"] == "meta":
        decimals = [pool_data["coins"][0]["decimals"]] + [i.get("decimals") for i in pool_data["base_coins"]]
    else:
        decimals = [i.get("decimals") for i in pool_data["coins"]]
    return decimals


@pytest.fixture(scope="module")
def wrapped_decimals(pool_data):
    # number of decimal places for each wrapped coin in the active pool
    yield [i.get("decimals") for i in pool_data["coins"]]
