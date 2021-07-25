import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(2))
def test_amount_received(alice, swap, idx):
    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity_one_coin(10 ** 18, idx, 0, {"from": alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        if i == len(twap):
            break
        assert twap[i] == twap_control[i] + (balance * elapsed)


@pytest.mark.parametrize("idx", range(2))
@pytest.mark.parametrize("divisor", [1, 5, 42])
def test_lp_token_balance(alice, swap, idx, divisor):
    initial_amount = swap.balanceOf(alice)
    amount = initial_amount // divisor

    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        if i == len(twap):
            break
        assert twap[i] == twap_control[i] + (balance * elapsed)
