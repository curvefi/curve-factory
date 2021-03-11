import pytest
from brownie import Contract
from brownie_tokens import ERC20, MintableForkToken


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


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def dave(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def fee_receiver(accounts):
    yield accounts[4]


@pytest.fixture(scope="module")
def implementation_usd(MetaImplementationUSD, alice):
    yield MetaImplementationUSD.deploy({"from": alice})


@pytest.fixture(scope="module")
def implementation_btc(MetaImplementationBTC, alice):
    yield MetaImplementationBTC.deploy({"from": alice})


@pytest.fixture(scope="module")
def factory(Factory, alice, fee_receiver, base_pool, implementation_usd):
    contract = Factory.deploy({"from": alice})
    contract.add_base_pool(base_pool, implementation_usd, fee_receiver, {"from": alice})
    yield contract


@pytest.fixture(scope="module")
def swap(MetaImplementationUSD, alice, base_pool, factory, coin):
    tx = factory.deploy_metapool(
        base_pool, "Test Swap", "TST", coin, 200, 4000000, {"from": alice}
    )
    yield MetaImplementationUSD.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_btc(MetaImplementationBTC, alice, base_pool_btc, factory, coin):
    tx = factory.deploy_metapool(
        base_pool_btc, "Test Swap BTC", "TSTB", coin, 200, 4000000, {"from": alice}
    )
    yield MetaImplementationBTC.at(tx.return_value)


@pytest.fixture(scope="module")
def zap(DepositZapUSD, alice):
    yield DepositZapUSD.deploy({"from": alice})


@pytest.fixture(scope="module")
def base_pool():
    pool = Contract("0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7")

    # ensure the base pool is balanced so our tests are deterministic
    max_balance = max(
        [pool.balances(0), pool.balances(1) * 10 ** 12, pool.balances(2) * 10 ** 12]
    )
    ideal_balances = [max_balance, max_balance // 10 ** 12, max_balance // 10 ** 12]
    for i, amount in enumerate(ideal_balances):
        balance = pool.balances(i)
        if balance < amount:
            MintableForkToken(pool.coins(i))._mint_for_testing(pool, amount - balance)
    pool.donate_admin_fees({"from": pool.owner()})

    yield pool


@pytest.fixture(scope="module")
def base_pool_btc(alice, fee_receiver, implementation_btc, factory):
    pool = Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")
    factory.add_base_pool(pool, implementation_btc, fee_receiver, {"from": alice})

    yield pool


@pytest.fixture(scope="module")
def wrapped_coins(coin, base_lp_token):
    yield [coin, base_lp_token]


@pytest.fixture(scope="module")
def underlying_coins(coin):
    BASE_COINS = [
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    ]
    yield [coin] + [MintableForkToken(i) for i in BASE_COINS]


@pytest.fixture(scope="module")
def base_lp_token():
    yield MintableForkToken("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")


@pytest.fixture(scope="module")
def coin(pytestconfig):
    yield ERC20(
        decimals=pytestconfig.getoption("decimals"),
        success=eval(pytestconfig.getoption("return_value")),
    )


@pytest.fixture(scope="module")
def wrapped_decimals(wrapped_coins):
    yield [i.decimals() for i in wrapped_coins]


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


@pytest.fixture(scope="module")
def add_initial_liquidity(
    alice, mint_alice, approve_alice, underlying_coins, swap, initial_amounts
):
    # mint (10**7 * precision) of each coin in the pool
    _add_liquidity(alice, swap, underlying_coins, initial_amounts)


@pytest.fixture(scope="module")
def mint_bob(
    bob, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying
):
    _mint(
        bob,
        wrapped_coins,
        initial_amounts,
        underlying_coins,
        initial_amounts_underlying,
    )


@pytest.fixture(scope="module")
def approve_bob(bob, swap, underlying_coins, wrapped_coins):
    _approve(bob, swap, underlying_coins, wrapped_coins)


@pytest.fixture(scope="module")
def mint_alice(
    alice, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying
):
    _mint(
        alice,
        wrapped_coins,
        initial_amounts,
        underlying_coins,
        initial_amounts_underlying,
    )


@pytest.fixture(scope="module")
def approve_alice(alice, swap, underlying_coins, wrapped_coins):
    _approve(alice, swap, underlying_coins, wrapped_coins)


@pytest.fixture(scope="module")
def approve_zap(alice, bob, zap, swap, underlying_coins, initial_amounts_underlying):
    for underlying, amount in zip(underlying_coins, initial_amounts_underlying):
        if underlying == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            continue
        underlying.approve(zap, 2 ** 256 - 1, {"from": alice})
        underlying.approve(zap, 2 ** 256 - 1, {"from": bob})

    swap.approve(zap, 2 ** 256 - 1, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": bob})
