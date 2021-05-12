import pytest
from pytest import approx

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(
    bob,
    swap,
    wrapped_coins,
    sending,
    receiving,
    wrapped_decimals,
    base_pool,
):

    amount = 10**wrapped_decimals[sending]
    if sending == 0:
        amount = amount * base_pool.get_virtual_price() // 10**18
    else:
        amount = amount * 10**18 // base_pool.get_virtual_price()
    wrapped_coins[sending]._mint_for_testing(bob, amount, {'from': bob})

    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.exchange(sending, receiving, amount, 0, {'from': bob})


    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        assert twap[i] == twap_control[i] + (balance * elapsed)
