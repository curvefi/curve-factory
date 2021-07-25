import pytest


@pytest.fixture(autouse=True)
def setup(add_initial_liquidity):
    pass


def test_get_balances(initial_amounts, swap, plain_pool_size):
    balances = swap.get_balances()
    assert len(balances) == plain_pool_size
    assert balances[0] == initial_amounts[0]
    assert balances[1] == initial_amounts[1]


def test_admin_balances_do_not_change(alice, swap, coins, initial_amounts):
    n_coins = len(coins)
    for i in range(n_coins):
        assert swap.admin_balances(i) == 0

    for i, coin in enumerate(coins):
        coin._mint_for_testing(swap, initial_amounts[i], {"from": alice})

    for i in range(n_coins):
        assert swap.admin_balances(i) == 0


def test_balances(swap, coins, initial_amounts):
    for i in range(len(coins)):
        assert swap.balances(i) == initial_amounts[i]


def test_virtual_price_increases_with_balances(alice, swap, coins, initial_amounts):
    virtual_price = swap.get_virtual_price()

    for i, coin in enumerate(coins):
        coin._mint_for_testing(swap, initial_amounts[i], {"from": alice})

    assert swap.get_virtual_price() // 2 == virtual_price


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(
    alice,
    swap,
    coins,
    initial_amounts,
    sending,
    receiving,
):
    for coin in coins:
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})

    for coin, amount in zip(coins, initial_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})

    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap.exchange(send, recv, initial_amounts[send], 0, {"from": alice})

    for i in (sending, receiving):
        admin_fee = swap.admin_balances(i)
        assert coins[i].balanceOf(swap) - admin_fee == swap.balances(i)
        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice,
    swap,
    coins,
    sending,
    receiving,
    initial_amounts,
):

    for coin in coins:
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})

    for coin, amount in zip(coins, initial_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})

    swap.exchange(sending, receiving, initial_amounts[sending], 0, {"from": alice})

    admin_balance = swap.admin_balances(receiving)

    assert admin_balance > 0
    assert swap.admin_balances(sending) == 0

    swap.withdraw_admin_fees({"from": alice})

    assert swap.balances(receiving) == coins[receiving].balanceOf(swap)


def test_no_fees(bob, fee_receiver, coins, swap):
    swap.withdraw_admin_fees({"from": bob})

    for coin in coins:
        assert coin.balanceOf(fee_receiver) == 0
