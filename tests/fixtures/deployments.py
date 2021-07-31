import pytest
from brownie import ZERO_ADDRESS, compile_source

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


@pytest.fixture(scope="session")
def plain_implementations(plain_basic, plain_eth, plain_optimized, plain_rebase):
    return [plain_basic, plain_eth, plain_optimized, plain_rebase]


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


# gauge implementation


@pytest.fixture(scope="session")
def crv(alice, pm):
    ERC20CRV = pm("curvefi/curve-dao-contracts@1.1.0").ERC20CRV
    return ERC20CRV.deploy("Dummy CRV", "CRV", 18, {"from": alice})


@pytest.fixture(scope="session")
def voting_escrow(alice, crv, pm):
    VotingEscrow = pm("curvefi/curve-dao-contracts@1.1.0").VotingEscrow
    return VotingEscrow.deploy(crv, "veCRV", "veCRV", 1, {"from": alice})


@pytest.fixture(scope="session")
def gauge_controller(alice, pm, crv, voting_escrow):
    GaugeController = pm("curvefi/curve-dao-contracts@1.1.0").GaugeController
    return GaugeController.deploy(crv, voting_escrow, {"from": alice})


@pytest.fixture(scope="session")
def minter(alice, crv, pm, gauge_controller):
    Minter = pm("curvefi/curve-dao-contracts@1.1.0").Minter
    minter = Minter.deploy(crv, gauge_controller, {"from": alice})
    crv.set_minter(minter, {"from": alice})
    return minter


@pytest.fixture(scope="session")
def gauge_implementation(alice, LiquidityGauge, minter, crv, voting_escrow, gauge_controller):
    source = LiquidityGauge._build["source"]
    old_addrs = [
        "0xd061D61a4d941c39E5453435B6345Dc261C2fcE0",  # minter
        "0xD533a949740bb3306d119CC777fa900bA034cd52",  # crv
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",  # voting escrow
        "0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB",  # gauge controller
    ]
    for old, new in zip(old_addrs, [minter, crv, voting_escrow, gauge_controller]):
        source = source.replace(old, new.address)

    NewLiquidityGauge = compile_source(source).Vyper
    return NewLiquidityGauge.deploy({"from": alice})


# Factories


@pytest.fixture(scope="session")
def factory(alice, frank, Factory):
    return Factory.deploy(frank, {"from": alice})


# Mock contracts


@pytest.fixture(scope="session")
def lending_pool(alice, AaveLendingPoolMock):
    return AaveLendingPoolMock.deploy({"from": alice})


@pytest.fixture(scope="module")
def swap(
    alice,
    factory,
    plain_implementations,
    coins,
    project,
    plain_pool_size,
    pool_type,
):
    # modifies the factory so should be module scoped
    tx = factory.deploy_plain_pool(
        "Test Plain Pool",
        "TPP",
        coins + [ZERO_ADDRESS] * (4 - plain_pool_size),
        200,
        4000000,
        0,
        pool_type,
        {"from": alice},
    )
    return getattr(project, plain_implementations[pool_type]._name).at(tx.return_value)


@pytest.fixture(scope="module")
def owner_proxy(alice, OwnerProxy):
    return OwnerProxy.deploy(alice, alice, alice, {"from": alice})


@pytest.fixture(scope="module")
def gauge(alice, factory, swap, LiquidityGauge, set_gauge_implementation):
    tx = factory.deploy_gauge(swap, {"from": alice})
    return LiquidityGauge.at(tx.return_value)
