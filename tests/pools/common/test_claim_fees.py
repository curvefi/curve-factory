import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(bob, swap, coins, initial_amounts, sending, receiving, eth_amount):
    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap.exchange(
            send,
            recv,
            initial_amounts[send],
            0,
            {"from": bob, "value": eth_amount(initial_amounts[send]) if send == 0 else 0},
        )

    for i in (sending, receiving):
        if coins[0] == ETH_ADDRESS and i == 0:
            admin_fee = swap.balance() - swap.balances(0)
            assert admin_fee + swap.balances(0) == swap.balance()
        else:
            admin_fee = coins[i].balanceOf(swap) - swap.balances(i)
            assert admin_fee + swap.balances(i) == coins[i].balanceOf(swap)

        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice, bob, swap, coins, sending, receiving, initial_amounts, eth_amount
):

    swap.exchange(
        sending,
        receiving,
        initial_amounts[sending],
        0,
        {"from": bob, "value": eth_amount(initial_amounts[sending]) if sending == 0 else 0},
    )

    admin_balance = swap.admin_balances(receiving)

    assert admin_balance > 0
    assert swap.admin_balances(sending) == 0

    swap.withdraw_admin_fees({"from": alice})

    if coins[0] == ETH_ADDRESS and receiving == 0:
        assert swap.balances(receiving) == swap.balance()
    else:
        assert swap.balances(receiving) == coins[receiving].balanceOf(swap)


def test_no_fees(bob, fee_receiver, swap, coins):
    pre_eth_balance = fee_receiver.balance()
    swap.withdraw_admin_fees({"from": bob})

    for coin in coins:
        if coin == ETH_ADDRESS:
            assert fee_receiver.balance() == pre_eth_balance
            continue
        assert coin.balanceOf(fee_receiver) == 0
