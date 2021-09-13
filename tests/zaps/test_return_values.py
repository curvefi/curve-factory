import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


def test_remove_liquidity(alice, bob, zap, swap, underlying_coins):
    swap.transfer(bob, swap.balanceOf(alice), {"from": alice})
    tx = zap.remove_liquidity(swap, (2000000 * 10 ** 18) // 3, [0, 0, 0, 0], {"from": bob})
    for coin, expected_amount in zip(underlying_coins, tx.return_value):
        assert coin.balanceOf(bob) == expected_amount


def test_remove_imbalance(alice, bob, zap, initial_amounts_underlying, swap, underlying_coins):
    amounts = [i // 2 for i in initial_amounts_underlying]
    amounts[0] = 0

    initial_balance = swap.balanceOf(alice)
    swap.transfer(bob, initial_balance, {"from": alice})
    tx = zap.remove_liquidity_imbalance(swap, amounts, initial_balance, {"from": bob})

    assert initial_balance - tx.return_value == swap.balanceOf(bob)


def test_remove_one(alice, bob, zap, underlying_coins, coins, swap):
    swap.transfer(bob, swap.balanceOf(alice), {"from": alice})
    tx = zap.remove_liquidity_one_coin(swap, 10 ** 18, 1, 0, {"from": bob})

    assert tx.return_value == underlying_coins[1].balanceOf(bob)


def test_add_liquidity(bob, zap, initial_amounts_underlying, swap, mint_bob_underlying):
    tx = zap.add_liquidity(swap, initial_amounts_underlying, 0, {"from": bob})
    assert swap.balanceOf(bob) == tx.return_value
