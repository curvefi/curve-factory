import pytest


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


def test_balances(alice, mint_and_deposit, swap_rebase, wrapped_rebase_coins, wrapped_rebase_amounts):
    for i in range(len(wrapped_rebase_coins)):
        assert swap_rebase.balances(i) == wrapped_rebase_amounts[i]


def test_virtual_price_increases_with_balances(alice, mint_and_deposit, swap_rebase, wrapped_rebase_coins, wrapped_rebase_amounts):
    virtual_price = swap_rebase.get_virtual_price()

    for i, coin in enumerate(wrapped_rebase_coins):
        coin._mint_for_testing(swap_rebase, wrapped_rebase_amounts[i], {"from": alice})

    assert swap_rebase.get_virtual_price() // 2 == virtual_price


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(alice, mint_and_deposit, swap_rebase, wrapped_rebase_coins, wrapped_rebase_amounts, sending, receiving):
    for coin in wrapped_rebase_coins:
        coin.approve(swap_rebase, 2**256-1, {'from': alice})

    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {'from': alice})

    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap_rebase.exchange(send, recv, wrapped_rebase_amounts[send], 0, {"from": alice})

    for i in (sending, receiving):
        admin_fee = swap_rebase.admin_balances(i)
        assert wrapped_rebase_coins[i].balanceOf(swap_rebase) - admin_fee == swap_rebase.balances(i)
        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice, bob, fee_receiver, mint_and_deposit, swap_rebase, wrapped_rebase_coins, sending, receiving, wrapped_rebase_amounts, base_lp_token
):
    assert base_lp_token.balanceOf(fee_receiver) == 0

    for coin in wrapped_rebase_coins:
        coin.approve(swap_rebase, 2**256-1, {'from': alice})

    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {'from': alice})

    swap_rebase.exchange(sending, receiving, wrapped_rebase_amounts[sending], 0, {"from": alice})

    admin_balance = swap_rebase.admin_balances(receiving)

    assert admin_balance > 0
    assert swap_rebase.admin_balances(sending) == 0

    swap_rebase.withdraw_admin_fees({"from": alice})

    assert base_lp_token.balanceOf(fee_receiver) > 0
    assert swap_rebase.balances(receiving) == wrapped_rebase_coins[receiving].balanceOf(swap_rebase)


def test_no_fees(bob, fee_receiver, swap_rebase, base_lp_token):
    swap_rebase.withdraw_admin_fees({"from": bob})

    assert base_lp_token.balanceOf(fee_receiver) == 0

