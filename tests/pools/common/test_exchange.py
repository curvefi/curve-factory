import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")

# TODO: fix for metapool
# @pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
# def test_exchange(
#     bob,
#     swap,
#     plain_coins,
#     sending,
#     receiving,
#     decimals,
#     base_pool,
# ):

#     amount = 10 ** decimals[sending]
#     if sending == 0:
#         amount = amount * base_pool.get_virtual_price() // 10 ** 18
#     else:
#         amount = amount * 10 ** 18 // base_pool.get_virtual_price()
#     plain_coins[sending]._mint_for_testing(bob, amount, {"from": bob})

#     swap.exchange(sending, receiving, amount, 0, {"from": bob})

#     assert plain_coins[sending].balanceOf(bob) == 0

#     received = plain_coins[receiving].balanceOf(bob)
#     assert (
#         1 - max(1e-4, 1 / received) - 0.0004
#         < received / 10 ** decimals[receiving]
#         < 1 - 0.0004
#     )

#     expected_admin_fee = 10 ** decimals[receiving] * 0.0004 * 0.5
#     admin_fee = swap.admin_balances(receiving)

#     assert expected_admin_fee / admin_fee == approx(
#         1, rel=max(1e-3, 1 / (expected_admin_fee - 1.1))
#     )


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_min_dy(bob, swap, plain_coins, sending, receiving, decimals):
    amount = 10 ** decimals[sending]
    plain_coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    min_dy = swap.get_dy(sending, receiving, amount)
    swap.exchange(sending, receiving, amount, min_dy - 1, {"from": bob})

    received = plain_coins[receiving].balanceOf(bob)
    assert abs(received - min_dy) <= 1
