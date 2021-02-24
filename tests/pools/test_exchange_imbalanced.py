import pytest
from pytest import approx

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")

@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
@pytest.mark.parametrize("min_amount", [0, 0])
def test_min_dy(bob, swap, wrapped_coins, sending, receiving, wrapped_decimals, min_amount):

    amounts = [10**i for i in wrapped_decimals]
    amounts[sending] = 0
    amounts[receiving] = amounts[receiving] * 10**8

    for i, amount in enumerate(amounts):
        wrapped_coins[i]._mint_for_testing(bob, amount, {'from': bob})

    swap.add_liquidity(amounts, min_amount, {'from': bob})

    amount = 10**wrapped_decimals[sending]
    wrapped_coins[sending]._mint_for_testing(bob, amount, {'from': bob})

    min_dy_sending = swap.get_dy(sending, receiving, amount)
    min_dy_receiving = swap.get_dy(receiving, sending, amount)

    assert min_dy_sending > min_dy_receiving
