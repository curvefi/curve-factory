import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import MintableForkToken


@pytest.fixture(scope="module")
def implementation_usd(MetaUSD, alice):
    yield MetaUSD.deploy({"from": alice})


@pytest.fixture(scope="module")
def implementation_btc(MetaBTC, alice):
    yield MetaBTC.deploy({"from": alice})


@pytest.fixture(scope="module")
def implementation_plain(Plain2Basic, alice):
    yield Plain2Basic.deploy({"from": alice})


@pytest.fixture(scope="module")
def implementation_rebase_btc(MetaBTCBalances, alice):
    yield MetaBTCBalances.deploy({"from": alice})


@pytest.fixture(scope="module")
def implementation_rebase_usd(MetaUSDBalances, alice):
    yield MetaUSDBalances.deploy({"from": alice})


@pytest.fixture(scope="module")
def factory(
    Factory,
    alice,
    fee_receiver,
    base_pool,
    implementation_usd,
    implementation_rebase_usd,
    implementation_plain,
):
    contract = Factory.deploy({"from": alice})
    contract.add_base_pool(
        base_pool,
        fee_receiver,
        0,
        [implementation_usd, implementation_rebase_usd] + [ZERO_ADDRESS] * 8,
        {"from": alice},
    )
    contract.set_plain_implementations(
        2, [implementation_plain] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    yield contract


@pytest.fixture()
def new_factory(Factory, alice, fee_receiver, base_pool, implementation_usd):
    contract = Factory.deploy({"from": alice})
    yield contract


@pytest.fixture(scope="module")
def swap_plain(Plain2Basic, alice, factory, plain_coins):
    tx = factory.deploy_plain_pool(
        "Test Plain", "PLN", plain_coins, 200, 4000000, 0, {"from": alice}
    )
    yield Plain2Basic.at(tx.return_value)


@pytest.fixture(scope="module")
def swap(MetaUSD, MetaUSDBalances, is_rebase, alice, rebase_coin, base_pool, factory, coin):
    if is_rebase:
        tx = factory.deploy_metapool(
            base_pool, "Test Swap", "TST", rebase_coin, 200, 4000000, 1, {"from": alice}
        )
        yield MetaUSDBalances.at(tx.return_value)
    else:
        tx = factory.deploy_metapool(
            base_pool, "Test Swap", "TST", coin, 200, 4000000, 0, {"from": alice}
        )
        yield MetaUSD.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_btc(MetaBTC, alice, base_pool_btc, factory, coin):
    tx = factory.deploy_metapool(
        base_pool_btc, "Test Swap BTC", "TSTB", coin, 200, 4000000, 0, {"from": alice}
    )
    yield MetaBTC.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_rebase(MetaUSDBalances, alice, base_pool, factory, rebase_coin):
    tx = factory.deploy_metapool(
        base_pool, "Test Swap", "TST", rebase_coin, 200, 4000000, 1, {"from": alice}
    )
    yield MetaUSDBalances.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_rebase_btc(MetaBTCBalances, alice, base_pool, factory, rebase_coin):
    tx = factory.deploy_metapool(
        base_pool, "Test Swap", "TST", rebase_coin, 200, 4000000, 1, {"from": alice}
    )
    yield MetaBTCBalances.at(tx.return_value)


@pytest.fixture(scope="module")
def zap(DepositZapUSD, alice):
    yield DepositZapUSD.deploy({"from": alice})


@pytest.fixture(scope="module")
def base_pool():
    pool = Contract("0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7")

    # ensure the base pool is balanced so our tests are deterministic
    max_balance = max([pool.balances(0), pool.balances(1) * 10 ** 12, pool.balances(2) * 10 ** 12])
    ideal_balances = [max_balance, max_balance // 10 ** 12, max_balance // 10 ** 12]
    for i, amount in enumerate(ideal_balances):
        balance = pool.balances(i)
        if balance < amount:
            MintableForkToken(pool.coins(i))._mint_for_testing(pool, amount - balance)
    pool.donate_admin_fees({"from": pool.owner()})

    yield pool


@pytest.fixture(scope="module")
def base_pool_btc(alice, fee_receiver, implementation_btc, factory, implementation_rebase_btc):
    pool = Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")
    factory.add_base_pool(
        pool,
        fee_receiver,
        2,
        [implementation_btc, implementation_rebase_btc] + [ZERO_ADDRESS] * 8,
        {"from": alice},
    )

    yield pool


@pytest.fixture(scope="module")
def owner_proxy(alice, OwnerProxy):
    return OwnerProxy.deploy(alice, alice, alice, {"from": alice})
