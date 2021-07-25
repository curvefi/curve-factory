import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("divisor", [2, 5, 10])
def test_remove_balanced(alice, swap, plain_coins, divisor, initial_amounts):
    initial_balance = swap.balanceOf(alice)
    amounts = [i // divisor for i in initial_amounts]
    swap.remove_liquidity_imbalance(amounts, initial_balance, {"from": alice})

    for i, coin in enumerate(plain_coins):
        assert coin.balanceOf(alice) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    assert swap.balanceOf(alice) / initial_balance == 1 - 1 / divisor


@pytest.mark.parametrize("idx", range(2))
def test_remove_one(alice, swap, plain_coins, plain_pool_size, idx, initial_amounts):
    amounts = [0] * plain_pool_size
    amounts[idx] = initial_amounts[idx] // 2

    lp_balance = plain_pool_size * 1_000_000 * 10 ** 18
    swap.remove_liquidity_imbalance(amounts, lp_balance, {"from": alice})

    for i, coin in enumerate(plain_coins):
        assert coin.balanceOf(alice) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    actual_balance = swap.balanceOf(alice)
    actual_total_supply = swap.totalSupply()
    ideal_balance = (2 * plain_pool_size - 1) * lp_balance / (2 * plain_pool_size)

    assert actual_balance == actual_total_supply
    assert ideal_balance * 0.9994 < actual_balance < ideal_balance


@pytest.mark.parametrize("divisor", [1, 2, 10])
def test_exceed_max_burn(alice, swap, plain_pool_size, divisor, initial_amounts):
    amounts = [i // divisor for i in initial_amounts]
    max_burn = plain_pool_size * 1_000_000 * 10 ** 18 // divisor

    with brownie.reverts():
        swap.remove_liquidity_imbalance(amounts, max_burn - 1, {"from": alice})


def test_cannot_remove_zero(alice, swap, plain_pool_size):
    with brownie.reverts():
        swap.remove_liquidity_imbalance([0] * plain_pool_size, 0, {"from": alice})


def test_no_totalsupply(alice, swap, plain_pool_size):
    swap.remove_liquidity(swap.totalSupply(), [0] * plain_pool_size, {"from": alice})
    with brownie.reverts():
        swap.remove_liquidity_imbalance([0] * plain_pool_size, 0, {"from": alice})


def test_event(alice, bob, swap, plain_coins, plain_pool_size, initial_amounts):
    swap.transfer(bob, swap.balanceOf(alice), {"from": alice})
    amounts = [i // 5 for i in initial_amounts]
    max_burn = plain_pool_size * 1_000_000 * 10 ** 18

    tx = swap.remove_liquidity_imbalance(amounts, max_burn, {"from": bob})

    event = tx.events["RemoveLiquidityImbalance"]
    assert event["provider"] == bob
    assert event["token_supply"] == swap.totalSupply()
    for coin, amount in zip(plain_coins, event["token_amounts"]):
        assert coin.balanceOf(bob) == amount
