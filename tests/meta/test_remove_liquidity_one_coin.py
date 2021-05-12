import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(2))
def test_amount_received(chain, alice, swap, wrapped_coins, wrapped_decimals, base_pool, idx):
    decimals = wrapped_decimals[idx]
    wrapped = wrapped_coins[idx]

    swap.remove_liquidity_one_coin(10**18, idx, 0, {'from': alice})

    ideal = 10**decimals
    if idx == 1:
        ideal = 10**36 // base_pool.get_virtual_price()

    assert ideal*0.99 <= wrapped.balanceOf(alice) <= ideal
