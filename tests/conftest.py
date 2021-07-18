import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import ERC20, MintableForkToken

pytest_plugins = ["fixtures.accounts", "fixtures.deployments"]


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


@pytest.fixture(scope="module")
def rebase_coin(alice, ATokenMock, AaveLendingPoolMock, ERC20Mock):
    aave_lending_pool_mock = AaveLendingPoolMock.deploy({"from": alice})
    erc20_mock = ERC20Mock.deploy("ERC20MOCK", "ERC", 18, {"from": alice})
    yield ATokenMock.deploy(
        "Rebase Mock", "MOK", 18, erc20_mock, aave_lending_pool_mock, {"from": alice}
    )


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
        [implementation_btc, implementation_rebase_btc] + [ZERO_ADDRESS] * 8,
        {"from": alice},
    )

    yield pool


@pytest.fixture(scope="module", params=[0, 1])
def is_rebase(request):
    yield request.param


@pytest.fixture(scope="module")
def wrapped_coins(is_rebase, coin, rebase_coin, base_lp_token):
    if is_rebase:
        yield [rebase_coin, base_lp_token]
    else:
        yield [coin, base_lp_token]


@pytest.fixture(scope="module")
def underlying_coins(coin, is_rebase, rebase_coin):
    BASE_COINS = [
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    ]
    if is_rebase:
        yield [rebase_coin] + [MintableForkToken(i) for i in BASE_COINS]
    else:
        yield [coin] + [MintableForkToken(i) for i in BASE_COINS]


@pytest.fixture(scope="module")
def plain_coins():
    yield [ERC20(decimals=7), ERC20(decimals=9), ZERO_ADDRESS, ZERO_ADDRESS]


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


@pytest.fixture()
def add_initial_liquidity(
    alice, mint_alice, approve_alice, underlying_coins, swap, initial_amounts
):
    # mint (10**7 * precision) of each coin in the pool
    _add_liquidity(alice, swap, underlying_coins, initial_amounts)


@pytest.fixture()
def mint_bob(bob, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(bob, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_bob(bob, swap, underlying_coins, wrapped_coins):
    _approve(bob, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def mint_alice(alice, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(alice, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_alice(alice, swap, underlying_coins, wrapped_coins):
    _approve(alice, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def approve_zap(alice, bob, zap, swap, underlying_coins, initial_amounts_underlying):
    for underlying, amount in zip(underlying_coins, initial_amounts_underlying):
        if underlying == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            continue
        underlying.approve(zap, 2 ** 256 - 1, {"from": alice})
        underlying.approve(zap, 2 ** 256 - 1, {"from": bob})

    swap.approve(zap, 2 ** 256 - 1, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": bob})


# Added for rebase tokens


@pytest.fixture(scope="module")
def wrapped_rebase_coins(rebase_coin, base_lp_token):
    yield [rebase_coin, base_lp_token]


@pytest.fixture(scope="module")
def wrapped_rebase_decimals(wrapped_rebase_coins):
    yield [i.decimals() for i in wrapped_rebase_coins]


@pytest.fixture(scope="module")
def wrapped_rebase_amounts(base_pool, wrapped_coins, wrapped_decimals):
    wrapped_amounts = [10 ** i * 1000000 for i in wrapped_decimals]
    wrapped_amounts[1] = wrapped_amounts[1] * 10 ** 18 // base_pool.get_virtual_price()
    yield wrapped_amounts


@pytest.fixture()
def mint_and_deposit(wrapped_rebase_coins, wrapped_rebase_amounts, alice, swap_rebase):
    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap_rebase, amount, {"from": alice})
    swap_rebase.add_liquidity(wrapped_rebase_amounts, 0, {"from": alice})
