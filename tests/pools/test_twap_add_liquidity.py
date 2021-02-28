import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")

def test_twap(
    chain, alice, swap, wrapped_coins, wrapped_decimals, initial_amounts, base_pool
):
    amounts = [10**i for i in wrapped_decimals]

    twap = swap.get_price_cumulative_last()
    initial = swap.block_timestamp_last()

    assert initial == 0

    for i, coin in enumerate(wrapped_coins):
        assert twap[i] == 0

    swap.add_liquidity(amounts, 0, {'from': alice})

    twap = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()

    for i, amount in enumerate(amounts):
        assert twap[i] == 0

    chain.sleep(1)

    swap.add_liquidity(amounts, 0, {'from': alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start
    before = after

    ptwap = twap

    for i, amount in enumerate(amounts):
        assert twap[i] == amount * (elapsed)

    chain.sleep(1000000)

    swap.add_liquidity(amounts, 0, {'from': alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, coin in enumerate(wrapped_coins):
        assert twap[i] == ptwap[i] + ((coin.balanceOf(swap) - amounts[i]) * (after - before))
