import pytest


pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "set_fee_receiver", "mint_bob", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice, bob, fee_receiver, swap, wrapped_coins, sending, receiving, initial_amounts, base_lp_token
):
    for coin in wrapped_coins:
        assert coin.balanceOf(fee_receiver) == 0

    swap.exchange(sending, receiving, initial_amounts[sending], 0, {'from': bob})

    admin_balance = swap.admin_balances(receiving)

    assert admin_balance > 0
    assert swap.admin_balances(sending) == 0

    swap.withdraw_admin_fees({'from': alice})

    assert wrapped_coins[receiving].balanceOf(fee_receiver) > 0
    assert swap.balances(receiving) == wrapped_coins[receiving].balanceOf(swap)
