import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("divisor", [2, 5, 10])
def test_remove_balanced(alice, swap, divisor, initial_amounts):
    initial_balance = swap.balanceOf(alice)
    amounts = [i // divisor for i in initial_amounts]
    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity_imbalance(amounts, initial_balance, {"from": alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        if i == len(twap):
            break
        assert twap[i] == twap_control[i] + (balance * elapsed)


@pytest.mark.parametrize("idx", range(2))
def test_remove_one(alice, swap, idx, initial_amounts):
    amounts = [i // 2 for i in initial_amounts]
    amounts[idx] = 0

    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity_imbalance(amounts, 2000000 * 10 ** 18, {"from": alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        if i == len(twap):
            break
        assert twap[i] == twap_control[i] + (balance * elapsed)
