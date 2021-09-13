import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


@pytest.mark.parametrize("idx", range(4))
@pytest.mark.parametrize("divisor", [10, 50, 100])
def test_remove_one(alice, bob, zap, underlying_coins, coins, swap, idx, divisor):
    underlying = underlying_coins[idx]
    wrapped = coins[min(idx, 1)]

    initial_amount = swap.balanceOf(alice)
    amount = initial_amount // divisor

    swap.transfer(bob, initial_amount, {"from": alice})
    zap.remove_liquidity_one_coin(swap, amount, idx, 0, {"from": bob})

    assert underlying.balanceOf(zap) == 0
    assert wrapped.balanceOf(zap) == 0
    assert swap.balanceOf(zap) == 0

    if wrapped != underlying:
        assert wrapped.balanceOf(bob) == 0

    assert swap.balanceOf(bob) == initial_amount - amount
    assert 0 < underlying.balanceOf(bob) <= amount


@pytest.mark.parametrize("idx", range(4))
def test_amount_exceeds_balance(bob, zap, swap, idx):
    with brownie.reverts():
        zap.remove_liquidity_one_coin(swap, 1, idx, 0, {"from": bob})
