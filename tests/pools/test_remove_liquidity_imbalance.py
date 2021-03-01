import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("divisor", [2, 5, 10])
def test_remove_balanced(alice, swap, wrapped_coins, divisor, initial_amounts):
    initial_balance = swap.balanceOf(alice)
    amounts = [i // divisor for i in initial_amounts]
    swap.remove_liquidity_imbalance(amounts, initial_balance, {'from': alice})

    for i, coin in enumerate(wrapped_coins):
        assert coin.balanceOf(alice) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    assert swap.balanceOf(alice) / initial_balance == 1 - 1 / divisor


@pytest.mark.parametrize("idx", range(2))
def test_remove_one(alice, swap, wrapped_coins, idx, initial_amounts):
    amounts = [i//2 for i in initial_amounts]
    amounts[idx] = 0

    swap.remove_liquidity_imbalance(amounts, 2000000 * 10**18, {'from': alice})

    for i, coin in enumerate(wrapped_coins):
        assert coin.balanceOf(alice) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    actual_balance = swap.balanceOf(alice)
    actual_total_supply = swap.totalSupply()
    ideal_balance = 1500000 * 10 ** 18

    assert actual_balance == actual_total_supply
    assert ideal_balance * 0.9994 < actual_balance < ideal_balance


@pytest.mark.parametrize("divisor", [1, 2, 10])
def test_exceed_max_burn(alice, swap, wrapped_coins, divisor, initial_amounts):
    amounts = [i // divisor for i in initial_amounts]
    max_burn = 2000000 * 10**18 // divisor

    with brownie.reverts():
        swap.remove_liquidity_imbalance(amounts, max_burn-1, {'from': alice})


def test_cannot_remove_zero(alice, swap, wrapped_coins):
    with brownie.reverts():
        swap.remove_liquidity_imbalance([0, 0], 0, {'from': alice})


def test_no_totalsupply(alice, swap):
    swap.remove_liquidity(swap.totalSupply(), [0, 0], {'from': alice})
    with brownie.reverts():
        swap.remove_liquidity_imbalance([0, 0], 0, {'from': alice})


def test_event(alice, bob, swap, wrapped_coins, initial_amounts):
    swap.transfer(bob, swap.balanceOf(alice), {'from': alice})
    amounts = [i // 5 for i in initial_amounts]
    max_burn = 2000000 * 10**18

    tx = swap.remove_liquidity_imbalance(amounts, max_burn, {'from': bob})

    event = tx.events["RemoveLiquidityImbalance"]
    assert event['provider'] == bob
    assert event['token_supply'] == swap.totalSupply()
    for coin, amount in zip(wrapped_coins, event['token_amounts']):
        assert coin.balanceOf(bob) == amount
