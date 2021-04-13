import pytest

from brownie import ZERO_ADDRESS
from brownie_tokens import ERC20, MintableForkToken

#pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


@pytest.fixture(scope="module")
def wrapped_rebase_coins(rebase_coin, base_lp_token):
    yield [rebase_coin, base_lp_token]


@pytest.fixture(scope="module")
def wrapped_rebase_decimals(wrapped_rebase_coins):
    yield [i.decimals() for i in wrapped_rebase_coins]


@pytest.fixture(scope="module")
def wrapped_rebase_amounts(base_pool, wrapped_decimals):
    wrapped_amounts = [10**i * 1000000 for i in wrapped_decimals]
    wrapped_amounts[1] = wrapped_amounts[1] * 10**18 // base_pool.get_virtual_price()
    yield wrapped_amounts


@pytest.fixture(scope="module")
def mint_and_deposit(wrapped_rebase_coins, wrapped_rebase_amounts, alice, swap_rebase):
    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap_rebase, amount, {"from": alice})
    swap_rebase.add_liquidity(wrapped_rebase_amounts, 0, {"from": alice})


def test_get_balances(alice, mint_and_deposit, wrapped_rebase_coins, wrapped_rebase_decimals, wrapped_rebase_amounts, base_pool, swap_rebase):
    balances = swap_rebase.get_balances()
    assert len(balances) == 2
    assert balances[0] == wrapped_rebase_amounts[0]
    assert balances[1] == wrapped_rebase_amounts[1]


def test_admin_balances_do_not_change(alice, swap_rebase, wrapped_rebase_coins, wrapped_rebase_amounts):
    n_coins = len(wrapped_rebase_coins)
    for i in range(n_coins):
        assert swap_rebase.admin_balances(i) == 0

    for i, coin in enumerate(wrapped_rebase_coins):
        coin._mint_for_testing(swap_rebase, wrapped_rebase_amounts[i], {"from": alice})

    for i in range(n_coins):
        assert swap_rebase.admin_balances(i) == 0


def test_balances():
    pass


def test_get_virtual_price():
    pass


def test_wirthdraw_admin_fees():
    pass


def test_virtual_price_increases_with_balances(alice, mint_and_deposit, swap_rebase, wrapped_rebase_coins, wrapped_rebase_amounts):
    virtual_price = swap_rebase.get_virtual_price()

    for i, coin in enumerate(wrapped_rebase_coins):
        coin._mint_for_testing(swap_rebase, wrapped_rebase_amounts[i], {"from": alice})

    assert swap_rebase.get_virtual_price() // 2 == virtual_price
