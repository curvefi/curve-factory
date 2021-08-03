import pytest
from pytest import approx

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(
    bob,
    swap,
    coins,
    sending,
    receiving,
    decimals,
    base_pool,
):

    amount = 10 ** decimals[sending]
    if sending == 0:
        amount = amount * base_pool.get_virtual_price() // 10 ** 18
    else:
        amount = amount * 10 ** 18 // base_pool.get_virtual_price()
    coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    swap.exchange(sending, receiving, amount, 0, {"from": bob})

    assert coins[sending].balanceOf(bob) == 0

    received = coins[receiving].balanceOf(bob)
    assert 1 - max(1e-4, 1 / received) - 0.0004 < received / 10 ** decimals[receiving] < 1 - 0.0004

    expected_admin_fee = 10 ** decimals[receiving] * 0.0004 * 0.5
    admin_fee = swap.admin_balances(receiving)

    assert expected_admin_fee / admin_fee == approx(
        1, rel=max(1e-3, 1 / (expected_admin_fee - 1.1))
    )
