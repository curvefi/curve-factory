import pytest


@pytest.fixture(scope="module")
def underlying_decimals(pool_data):
    # number of decimal places for each underlying coin in the active pool
    decimals = []
    if pool_data["type"] == "meta":
        decimals = [pool_data["coins"][0]["decimals"]] + [i.get("decimals") for i in pool_data["base_coins"]]
    else:
        if pool_data.get("coins") and len(pool_data["coins"]) >= 2:
            decimals = [i.get("decimals") for i in pool_data["coins"]]
        else:
            for _ in range(pool_data["n_coins"]):
                decimals.append(18)
    return decimals


@pytest.fixture(scope="module")
def wrapped_decimals(pool_data, is_meta):
    # number of decimal places for each wrapped coin in the active pool
    decimals = []
    if is_meta:
        decimals = [i.get("decimals") for i in pool_data["coins"]]
    else:
        decimals = [18 for _ in range(pool_data["n_coins"])]
    yield decimals


@pytest.fixture(scope="module")
def is_meta(pool_data):
    return pool_data["type"] == "meta"


@pytest.fixture(scope="module")
def is_rebase(pool_data):
    return pool_data["rebase"]
