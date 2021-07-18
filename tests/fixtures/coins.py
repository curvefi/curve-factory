import pytest
from brownie import ZERO_ADDRESS
from brownie_tokens import ERC20, MintableForkToken


@pytest.fixture(scope="module")
def rebase_coin(alice, ATokenMock, AaveLendingPoolMock, ERC20Mock):
    aave_lending_pool_mock = AaveLendingPoolMock.deploy({"from": alice})
    erc20_mock = ERC20Mock.deploy("ERC20MOCK", "ERC", 18, {"from": alice})
    yield ATokenMock.deploy(
        "Rebase Mock", "MOK", 18, erc20_mock, aave_lending_pool_mock, {"from": alice}
    )


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
def wrapped_rebase_coins(rebase_coin, base_lp_token):
    yield [rebase_coin, base_lp_token]


@pytest.fixture(scope="module")
def wrapped_rebase_decimals(wrapped_rebase_coins):
    yield [i.decimals() for i in wrapped_rebase_coins]
