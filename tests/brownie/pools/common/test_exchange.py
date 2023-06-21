import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_min_dy(bob, swap, coins, sending, receiving, decimals, eth_amount):
    amount = 10 ** decimals[sending]
    if coins[sending] != ETH_ADDRESS:
        coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    min_dy = swap.get_dy(sending, receiving, amount)
    pre_bal = bob.balance()
    swap.exchange(
        sending,
        receiving,
        amount,
        min_dy - 1,
        {"from": bob, "value": eth_amount(amount) if sending == 0 else 0},
    )

    if coins[0] == ETH_ADDRESS and receiving == 0:
        received = bob.balance() - pre_bal
    else:
        received = coins[receiving].balanceOf(bob)
    assert abs(received - min_dy) <= 1
