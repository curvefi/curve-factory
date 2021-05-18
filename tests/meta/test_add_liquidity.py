import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_min_amount_too_high(bob, swap, wrapped_decimals, wrapped_coins, base_pool):
    amounts = [10**i for i in wrapped_decimals]

    ideal_amount = 10**18 + base_pool.get_virtual_price()
    with brownie.reverts():
        swap.add_liquidity(amounts, ideal_amount, {'from': bob})


def test_send_eth(bob, swap, wrapped_coins, initial_amounts):
    with brownie.reverts():
        swap.add_liquidity(initial_amounts, 0, {'from': bob, 'value': 1})
