import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(bob, swap, plain_coins, initial_amounts, sending, receiving):
    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap.exchange(send, recv, initial_amounts[send], 0, {"from": bob})

    for i in (sending, receiving):
        admin_fee = plain_coins[i].balanceOf(swap) - swap.balances(i)
        assert admin_fee + swap.balances(i) == plain_coins[i].balanceOf(swap)

        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice,
    bob,
    swap,
    plain_coins,
    sending,
    receiving,
    initial_amounts,
):

    swap.exchange(sending, receiving, initial_amounts[sending], 0, {"from": bob})

    admin_balance = swap.admin_balances(receiving)

    assert admin_balance > 0
    assert swap.admin_balances(sending) == 0

    swap.withdraw_admin_fees({"from": alice})

    assert swap.balances(receiving) == plain_coins[receiving].balanceOf(swap)


# def test_no_fees(bob, fee_receiver, swap, base_lp_token):
#     swap.withdraw_admin_fees({"from": bob})

#     assert base_lp_token.balanceOf(fee_receiver) == 0
