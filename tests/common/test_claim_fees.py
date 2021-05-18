import pytest


pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "set_fee_receiver", "mint_bob", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(alice, bob, swap, wrapped_coins, initial_amounts, sending, receiving):
    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap.exchange(send, recv, initial_amounts[send], 0, {'from': bob})

    for i in (sending, receiving):
        admin_fee = wrapped_coins[i].balanceOf(swap) - swap.balances(i)
        assert admin_fee + swap.balances(i) == wrapped_coins[i].balanceOf(swap)

        assert admin_fee > 0
