import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("min_amount", (0, 1))
def test_remove_liquidity(alice, swap, wrapped_coins, min_amount, initial_amounts):
    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity(
        swap.balanceOf(alice),
        [i * min_amount for i in initial_amounts],
        {'from': alice}
    )

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        assert twap[i] == twap_control[i] + (balance * elapsed)


def test_remove_partial(alice, swap, wrapped_coins, initial_amounts):
    initial_amount = swap.balanceOf(alice)
    withdraw_amount = initial_amount // 2
    twap_control = swap.get_price_cumulative_last()
    start = swap.block_timestamp_last()
    balances_before = swap.get_balances()

    swap.remove_liquidity(withdraw_amount, [0, 0], {'from': alice})

    twap = swap.get_price_cumulative_last()
    after = swap.block_timestamp_last()
    elapsed = after - start

    for i, balance in enumerate(balances_before):
        assert twap[i] == twap_control[i] + (balance * elapsed)
