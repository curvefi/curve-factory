import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(bob, swap, coins, sending, receiving, decimals, eth_amount):

    amount = 10 ** decimals[sending]
    coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.exchange(
        sending,
        receiving,
        amount,
        0,
        {"from": bob, "value": eth_amount(amount) if sending == 0 else 0},
    )

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        assert twap[i] == twap_control[i] + (balance * elapsed)
