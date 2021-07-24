import pytest

# implementation contracts - paramaterized by pool size


@pytest.fixture(scope="session")
def plain_basic(deploy_plain_implementation, plain_pool_size):
    return deploy_plain_implementation(_pool_size=plain_pool_size, _pool_type="Basic")


@pytest.fixture(scope="session")
def plain_eth(deploy_plain_implementation, plain_pool_size):
    return deploy_plain_implementation(_pool_size=plain_pool_size, _pool_type="ETH")


@pytest.fixture(scope="session")
def plain_optimized(deploy_plain_implementation, plain_pool_size):
    return deploy_plain_implementation(_pool_size=plain_pool_size, _pool_type="Optimized")


@pytest.fixture(scope="session")
def plain_rebase(deploy_plain_implementation, plain_pool_size):
    return deploy_plain_implementation(_pool_size=plain_pool_size, _pool_type="Balances")


# meta-pools require mainnet-fork network for testing


@pytest.fixture(scope="session")
def meta_btc(alice, MetaBTC):
    return MetaBTC.deploy({"from": alice})


@pytest.fixture(scope="session")
def meta_usd(alice, MetaBTCBalances):
    return MetaBTCBalances.deploy({"from": alice})


@pytest.fixture(scope="session")
def meta_btc_rebase(alice, MetaUSD):
    return MetaUSD.deploy({"from": alice})


@pytest.fixture(scope="session")
def meta_usd_rebase(alice, MetaUSDBalances):
    return MetaUSDBalances.deploy({"from": alice})


# Factories


@pytest.fixture(scope="session")
def factory(alice, frank, Factory):
    return Factory.deploy(frank, {"from": alice})


# Mock contracts


@pytest.fixture(scope="session")
def lending_pool(alice, AaveLendingPoolMock):
    return AaveLendingPoolMock.deploy({"from": alice})
