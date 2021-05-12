import pytest
from pytest import approx

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_min_dy(bob, swap, wrapped_coins, sending, receiving, wrapped_decimals):
    amount = 10**wrapped_decimals[sending]
    wrapped_coins[sending]._mint_for_testing(bob, amount, {'from': bob})

    min_dy = swap.get_dy(sending, receiving, amount)
    swap.exchange(sending, receiving, amount, min_dy-1, {'from': bob})

    received = wrapped_coins[receiving].balanceOf(bob)
    assert abs(received - min_dy) <= 1
