import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "mint_bob_underlying", "approve_bob", "approve_zap"
)


def test_add_liquidity(bob, charlie, zap, swap, initial_amounts_underlying):
    zap.add_liquidity(swap, initial_amounts_underlying, 0, charlie, {"from": bob})

    assert swap.balanceOf(charlie) > 0
    assert swap.balanceOf(bob) == 0


def test_remove_imbalanced(
    alice, charlie, dave, zap, swap, initial_amounts_underlying, underlying_coins
):
    amounts = [i // 4 for i in initial_amounts_underlying]
    initial_balance = swap.balanceOf(alice)

    swap.transfer(charlie, initial_balance, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": charlie})
    zap.remove_liquidity_imbalance(swap, amounts, initial_balance, dave, {"from": charlie})

    assert swap.balanceOf(charlie) > 0
    assert swap.balanceOf(dave) == 0
    assert swap.balanceOf(zap) == 0

    for coin in underlying_coins:
        assert coin.balanceOf(charlie) == 0
        assert coin.balanceOf(dave) > 0
        assert coin.balanceOf(zap) == 0


def test_remove_one_coin(alice, charlie, dave, zap, underlying_coins, coins, swap):
    underlying = underlying_coins[1]

    initial_balance = swap.balanceOf(alice)
    amount = initial_balance // 4

    swap.transfer(charlie, initial_balance, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": charlie})
    zap.remove_liquidity_one_coin(swap, amount, 1, 0, dave, {"from": charlie})

    assert underlying.balanceOf(zap) == 0
    assert underlying.balanceOf(charlie) == 0
    assert underlying.balanceOf(dave) > 0

    assert swap.balanceOf(zap) == 0
    assert swap.balanceOf(charlie) + amount == initial_balance
    assert swap.balanceOf(dave) == 0


def test_remove_liquidity(alice, charlie, dave, zap, swap, underlying_coins):
    initial_balance = swap.balanceOf(alice)
    withdraw_amount = initial_balance // 3

    swap.transfer(charlie, initial_balance, {"from": alice})
    swap.approve(zap, 2 ** 256 - 1, {"from": charlie})
    zap.remove_liquidity(swap, withdraw_amount, [0, 0, 0, 0], dave, {"from": charlie})

    assert swap.balanceOf(charlie) > 0
    assert swap.balanceOf(dave) == 0
    assert swap.balanceOf(zap) == 0

    for coin in underlying_coins:
        assert coin.balanceOf(charlie) == 0
        assert coin.balanceOf(dave) > 0
        assert coin.balanceOf(zap) == 0
