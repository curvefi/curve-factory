import pytest
from brownie import ZERO_ADDRESS, Contract, compile_source, convert
from brownie.network import state
from hexbytes import HexBytes

# keys are keccak256(source)
# values are
meta_contracts = {}


def pack_values(values) -> bytes:
    """Stolen from curvefi/curve-pool-registry"""
    assert max(values) < 256
    return sum(i << c * 8 for c, i in enumerate(values))


# mock infra


@pytest.fixture(scope="session", autouse=True)
def address_provider(alice, AddressProvider, base_coins):
    return AddressProvider.deploy(alice, {"from": alice})


@pytest.fixture(scope="session", autouse=True)
def registry(alice, address_provider, Registry):
    registry = Registry.deploy(address_provider, ZERO_ADDRESS, {"from": alice})
    address_provider.set_address(0, registry, {"from": alice})
    return registry


@pytest.fixture(scope="session")
def mock_veboost_proxy(alice, MockBoostDelegationProxy, voting_escrow):
    return MockBoostDelegationProxy.deploy(voting_escrow, ZERO_ADDRESS, {"from": alice})


# mock base pool


@pytest.fixture(scope="session", autouse=True)
def base_pool(alice, CurvePool, base_coins, lp_token, registry, accounts):
    pool = CurvePool.deploy(alice, base_coins, lp_token, 200, 3000000, 5000000000, {"from": alice})
    lp_token.set_minter(pool, {"from": alice})

    amount = (10 ** 9) * 10 ** 18  # 1_000_000_000
    for coin in base_coins:
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(pool, 2 ** 256 - 1, {"from": alice})
    pool.add_liquidity([amount] * 3, 0, {"from": alice})
    lp_token.transfer(accounts[-1], lp_token.balanceOf(alice), {"from": alice})

    registry.add_pool_without_underlying(
        pool,
        3,
        lp_token,
        "0x0",
        pack_values([18, 18, 18]),
        pack_values([0, 0, 0]),
        True,
        False,
        "Test Base Pool",
    )

    return pool


@pytest.fixture(scope="session")
def base_gauge(alice, pm, lp_token):
    RewardsOnlyGauge = pm("curvefi/curve-dao-contracts@1.3.0").RewardsOnlyGauge
    return RewardsOnlyGauge.deploy(lp_token, alice, {"from": alice})


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


def _replace_btc(source, base_pool, base_coins, lp_token):
    real_addrs = [
        "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714",  # pool addr
        "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",  # lp token
        "0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D",  # renBTC
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # wBTC
        "0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6",  # sBTC
    ]
    replacements = [base_pool, lp_token] + base_coins
    for old, new in zip(real_addrs, replacements):
        source = source.replace(old, new.address)
    return source


def _replace_usd(source, base_pool, base_coins, lp_token):
    real_addrs = [
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",  # pool addr
        "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",  # lp token
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    ]
    replacements = [base_pool, lp_token] + base_coins
    for old, new in zip(real_addrs, replacements):
        source = source.replace(old, new.address)
    return source


@pytest.fixture(scope="session")
def meta_btc(alice, MetaBTC, base_pool, base_coins, lp_token, pytestconfig):
    meta_btc_abi = pytestconfig.cache.get("meta_btc_abi", False)
    meta_btc_bytecode = pytestconfig.cache.get("meta_btc_bytecode", False)
    if meta_btc_abi and meta_btc_bytecode:
        tx = alice.transfer(data=meta_btc_bytecode)
        instance = Contract.from_abi("Meta BTC", tx.contract_address, meta_btc_abi)
        meta_contracts[tx.contract_address] = meta_btc_abi
        return instance

    source = MetaBTC._build["source"]
    new_source = _replace_btc(source, base_pool, base_coins, lp_token)
    NewMetaBTC = compile_source(new_source).Vyper
    instance = NewMetaBTC.deploy({"from": alice})
    meta_contracts[instance.address] = NewMetaBTC.abi

    pytestconfig.cache.set("meta_btc_abi", NewMetaBTC.abi)
    pytestconfig.cache.set("meta_btc_bytecode", NewMetaBTC.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_usd(alice, MetaUSD, base_pool, base_coins, lp_token, pytestconfig):
    meta_usd_abi = pytestconfig.cache.get("meta_usd_abi", False)
    meta_usd_bytecode = pytestconfig.cache.get("meta_usd_bytecode", False)
    if meta_usd_abi and meta_usd_bytecode:
        tx = alice.transfer(data=meta_usd_bytecode)
        instance = Contract.from_abi("Meta USD", tx.contract_address, meta_usd_abi)
        meta_contracts[tx.contract_address] = meta_usd_abi
        return instance

    source = MetaUSD._build["source"]
    new_source = _replace_usd(source, base_pool, base_coins, lp_token)
    NewMetaUSD = compile_source(new_source).Vyper
    instance = NewMetaUSD.deploy({"from": alice})
    meta_contracts[instance.address] = NewMetaUSD.abi

    pytestconfig.cache.set("meta_usd_abi", NewMetaUSD.abi)
    pytestconfig.cache.set("meta_usd_bytecode", NewMetaUSD.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_rai(alice, MetaRAI, base_pool, base_coins, lp_token, pytestconfig):
    meta_rai_abi = pytestconfig.cache.get("meta_rai_abi", False)
    meta_rai_bytecode = pytestconfig.cache.get("meta_rai_bytecode", False)
    if meta_rai_abi and meta_rai_bytecode:
        tx = alice.transfer(data=meta_rai_bytecode)
        instance = Contract.from_abi("Meta RAI", tx.contract_address, meta_rai_abi)
        meta_contracts[tx.contract_address] = meta_rai_abi
        return instance

    source = MetaRAI._build["source"]
    new_source = _replace_usd(source, base_pool, base_coins, lp_token)
    NewMetaRAI = compile_source(new_source).Vyper
    instance = NewMetaRAI.deploy({"from": alice})
    meta_contracts[instance.address] = NewMetaRAI.abi

    pytestconfig.cache.set("meta_rai_abi", NewMetaRAI.abi)
    pytestconfig.cache.set("meta_rai_bytecode", NewMetaRAI.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_btc_rebase(alice, MetaBTCBalances, base_pool, base_coins, lp_token, pytestconfig):
    meta_btc_rebase_abi = pytestconfig.cache.get("meta_btc_rebase_abi", False)
    meta_btc_rebase_bytecode = pytestconfig.cache.get("meta_btc_rebase_bytecode", False)
    if meta_btc_rebase_abi and meta_btc_rebase_bytecode:
        tx = alice.transfer(data=meta_btc_rebase_bytecode)
        instance = Contract.from_abi("Meta BTC Rebase", tx.contract_address, meta_btc_rebase_abi)
        meta_contracts[tx.contract_address] = meta_btc_rebase_abi
        return instance

    source = MetaBTCBalances._build["source"]
    new_source = _replace_btc(source, base_pool, base_coins, lp_token)
    NewMetaBTCBalances = compile_source(new_source).Vyper
    instance = NewMetaBTCBalances.deploy({"from": alice})
    meta_contracts[instance.address] = NewMetaBTCBalances.abi

    pytestconfig.cache.set("meta_btc_rebase_abi", NewMetaBTCBalances.abi)
    pytestconfig.cache.set("meta_btc_rebase_bytecode", NewMetaBTCBalances.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_usd_rebase(alice, MetaUSDBalances, base_pool, base_coins, lp_token, pytestconfig):
    meta_usd_rebase_abi = pytestconfig.cache.get("meta_usd_rebase_abi", False)
    meta_usd_rebase_bytecode = pytestconfig.cache.get("meta_usd_rebase_bytecode", False)
    if meta_usd_rebase_abi and meta_usd_rebase_bytecode:
        tx = alice.transfer(data=meta_usd_rebase_bytecode)
        instance = Contract.from_abi("Meta USD Rebase", tx.contract_address, meta_usd_rebase_abi)
        meta_contracts[tx.contract_address] = meta_usd_rebase_abi
        return instance

    source = MetaUSDBalances._build["source"]
    new_source = _replace_usd(source, base_pool, base_coins, lp_token)
    NewMetaUSDBalances = compile_source(new_source).Vyper
    instance = NewMetaUSDBalances.deploy({"from": alice})
    meta_contracts[instance.address] = NewMetaUSDBalances.abi

    pytestconfig.cache.set("meta_usd_rebase_abi", NewMetaUSDBalances.abi)
    pytestconfig.cache.set("meta_usd_rebase_bytecode", NewMetaUSDBalances.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_sidechain(
    alice,
    MetaStandard,
    sidechain_meta_gauge,
    base_gauge,
    base_pool,
    base_coins,
    lp_token,
    pytestconfig,
):
    meta_sidechain_abi = pytestconfig.cache.get("meta_sidechain_abi", False)
    meta_sidechain_bytecode = pytestconfig.cache.get("meta_sidechain_bytecode", False)
    if meta_sidechain_abi and meta_sidechain_bytecode:
        tx = alice.transfer(data=meta_sidechain_bytecode)
        instance = Contract.from_abi(
            "MetaStandard Sidechain", tx.contract_address, meta_sidechain_abi
        )
        meta_contracts[tx.contract_address] = meta_sidechain_abi
        return instance

    source = MetaStandard._build["source"]
    for repl in [base_pool, *base_coins, lp_token, base_gauge, sidechain_meta_gauge]:
        source = source.replace(ZERO_ADDRESS, repl.address, 1)

    NewMeta = compile_source(source).Vyper
    instance = NewMeta.deploy({"from": alice})
    meta_contracts[instance.address] = NewMeta.abi

    pytestconfig.cache.set("meta_sidechain_abi", NewMeta.abi)
    pytestconfig.cache.set("meta_sidechain_bytecode", NewMeta.bytecode)
    return instance


@pytest.fixture(scope="session")
def meta_sidechain_rebase(
    alice,
    MetaBalances,
    sidechain_meta_gauge,
    base_gauge,
    base_pool,
    base_coins,
    lp_token,
    pytestconfig,
):
    meta_sidechain_rebase_abi = pytestconfig.cache.get("meta_sidechain_rebase_abi", False)
    meta_sidechain_rebase_bytecode = pytestconfig.cache.get("meta_sidechain_rebase_bytecode", False)
    if meta_sidechain_rebase_abi and meta_sidechain_rebase_bytecode:
        tx = alice.transfer(data=meta_sidechain_rebase_bytecode)
        instance = Contract.from_abi(
            "MetaBalances Sidechain", tx.contract_address, meta_sidechain_rebase_abi
        )
        meta_contracts[tx.contract_address] = meta_sidechain_rebase_abi
        return instance

    source = MetaBalances._build["source"]
    for repl in [base_pool, *base_coins, lp_token, base_gauge, sidechain_meta_gauge]:
        source = source.replace(ZERO_ADDRESS, repl.address, 1)

    NewMeta = compile_source(source).Vyper
    instance = NewMeta.deploy({"from": alice})
    meta_contracts[instance.address] = NewMeta.abi

    pytestconfig.cache.set("meta_sidechain_rebase_abi", NewMeta.abi)
    pytestconfig.cache.set("meta_sidechain_rebase_bytecode", NewMeta.bytecode)
    return instance


# gauge implementation


@pytest.fixture(scope="session")
def crv(alice, pm):
    ERC20CRV = pm("curvefi/curve-dao-contracts@1.3.0").ERC20CRV
    return ERC20CRV.deploy("Dummy CRV", "CRV", 18, {"from": alice})


@pytest.fixture(scope="session")
def voting_escrow(alice, crv, pm):
    VotingEscrow = pm("curvefi/curve-dao-contracts@1.3.0").VotingEscrow
    return VotingEscrow.deploy(crv, "veCRV", "veCRV", 1, {"from": alice})


@pytest.fixture(scope="session")
def gauge_controller(alice, pm, crv, voting_escrow):
    GaugeController = pm("curvefi/curve-dao-contracts@1.3.0").GaugeController
    return GaugeController.deploy(crv, voting_escrow, {"from": alice})


@pytest.fixture(scope="session")
def minter(alice, crv, pm, gauge_controller):
    Minter = pm("curvefi/curve-dao-contracts@1.3.0").Minter
    minter = Minter.deploy(crv, gauge_controller, {"from": alice})
    crv.set_minter(minter, {"from": alice})
    return minter


@pytest.fixture(scope="session")
def gauge_implementation(
    alice, LiquidityGauge, minter, crv, voting_escrow, gauge_controller, mock_veboost_proxy
):
    source = LiquidityGauge._build["source"]
    old_addrs = [
        "0xd061D61a4d941c39E5453435B6345Dc261C2fcE0",  # minter
        "0xD533a949740bb3306d119CC777fa900bA034cd52",  # crv
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",  # voting escrow
        "0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB",  # gauge controller
        "0x8E0c00ed546602fD9927DF742bbAbF726D5B0d16",  # veboost proxy
    ]
    for old, new in zip(
        old_addrs, [minter, crv, voting_escrow, gauge_controller, mock_veboost_proxy]
    ):
        source = source.replace(old, new.address)

    NewLiquidityGauge = compile_source(source).Vyper
    return NewLiquidityGauge.deploy({"from": alice})


@pytest.fixture(scope="session")
def sidechain_meta_gauge(alice, GaugeExtension, factory):
    source = GaugeExtension._build["source"]
    source = source.replace("0x0000000000000000000000000000000000000000", factory.address, 1)
    return compile_source(source).Vyper.deploy({"from": alice})


@pytest.fixture(scope="session")
def meta_implementations(
    pool_type,
    meta_usd,
    meta_usd_rebase,
    meta_btc,
    meta_btc_rebase,
    meta_sidechain,
    meta_sidechain_rebase,
    meta_rai
):
    if pool_type == 4:
        return [meta_usd, meta_usd_rebase]
    elif pool_type == 5:
        return [meta_btc, meta_btc_rebase]
    elif pool_type == 7:
        return [meta_rai, meta_rai]
    else:
        return [meta_sidechain, meta_sidechain_rebase]


# Factories


@pytest.fixture(scope="session")
def factory(alice, frank, Factory, address_provider, pytestconfig):
    # if factory_bytecode := pytestconfig.cache.get("factory_bytecode", False):
    #     tx = alice.transfer(data=factory_bytecode)
    #     return Factory.at(tx.contract_address)

    source = Factory._build["source"]
    new_source = source.replace(
        "0x0000000022D53366457F9d5E68Ec105046FC4383", address_provider.address
    )
    NewFactory = compile_source(new_source).Vyper
    # pytestconfig.cache.set("factory_bytecode", NewFactory.deploy.encode_input(frank))
    return NewFactory.deploy(frank, {"from": alice})


# Mock contracts
@pytest.fixture(scope="session")
def lending_pool(alice, AaveLendingPoolMock):
    return AaveLendingPoolMock.deploy({"from": alice})


@pytest.fixture(scope="module")
def swap(
    alice,
    base_pool,
    factory,
    plain_implementations,
    meta_implementation_idx,
    coins,
    project,
    plain_pool_size,
    pool_type,
    is_meta_pool,
    web3,
    redemption_price_snap
):
    if not is_meta_pool:
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
    else:
        tx = factory.deploy_metapool(
            base_pool,
            "Test Meta Pool",
            "TMP",
            coins[0],
            200,
            4000000,
            meta_implementation_idx,
            {"from": alice},
        )
        key = convert.to_address(HexBytes(web3.eth.get_code(tx.return_value))[10:30].hex())
        instance = Contract.from_abi("Meta Instance", tx.return_value, meta_contracts[key])
        instance._build["language"] = "Vyper"
        state._add_contract(instance)

        if pool_type == 7: # setting rate feed
            instance.initialize_rate_feed(redemption_price_snap, 1000000000, {"from": alice})

        return instance


@pytest.fixture(scope="module")
def owner_proxy(alice, OwnerProxy):
    return OwnerProxy.deploy(alice, alice, alice, {"from": alice})


@pytest.fixture(scope="module")
def gauge(alice, factory, swap, LiquidityGauge, set_gauge_implementation):
    tx = factory.deploy_gauge(swap, {"from": alice})
    return LiquidityGauge.at(tx.return_value)


@pytest.fixture(scope="module")
def meta_gauge(swap, GaugeExtension):
    return Contract.from_abi("Meta Liquidity Gauge", swap.rewards_receiver(), GaugeExtension.abi)


@pytest.fixture(scope="module")
def zap(alice, base_coins, base_pool, lp_token, DepositZap):
    source = DepositZap._build["source"]

    source = source.replace("69", str(len(base_coins)), 1)

    base_coin_addrs = [coin.address for coin in base_coins]
    source = source.replace(
        f"= [{', '.join([ZERO_ADDRESS] * 3)}]", f"= [{', '.join(base_coin_addrs)}]"
    )

    for token in [base_pool, lp_token]:
        source = source.replace(f"= {ZERO_ADDRESS}", f"= {token.address}", 1)

    return compile_source(source).Vyper.deploy({"from": alice})


@pytest.fixture(scope="module")
def redemption_price_snap(RedemptionPriceSnapMock, alice):
    return RedemptionPriceSnapMock.deploy({"from": alice})