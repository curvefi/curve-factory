import itertools

import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize(
    "sending,receiving", filter(lambda k: 0 in k, itertools.permutations(range(4), 2))
)
def test_amounts(bob, swap, underlying_coins, sending, receiving, underlying_decimals):
    amount = 10 ** underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        assert twap[i] == twap_control[i] + (balance * elapsed)
