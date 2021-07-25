import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_add_liquidity(bob, charlie, swap, initial_amounts):
    swap.add_liquidity(initial_amounts, 0, charlie, {"from": bob})

    assert swap.balanceOf(bob) == 0
    assert swap.balanceOf(charlie) > 0


def test_exchange(alice, charlie, swap, plain_coins):
    plain_coins[1]._mint_for_testing(alice, 10 ** 18)

    swap.exchange(1, 0, 10 ** 18, 0, charlie, {"from": alice})
    assert plain_coins[0].balanceOf(charlie) > 0
    assert plain_coins[0].balanceOf(alice) == 0


# TODO: fix for metapools
# def test_exchange_underlying(alice, charlie, swap, underlying_coins):
#     underlying_coins[1]._mint_for_testing(alice, 10 ** 18)

#     swap.exchange_underlying(1, 0, 10 ** 18, 0, charlie, {"from": alice})
#     assert underlying_coins[0].balanceOf(charlie) > 0
#     assert underlying_coins[0].balanceOf(alice) == 0


def test_remove_liquidity(alice, swap, charlie, plain_coins, initial_amounts, plain_pool_size):
    initial_amount = swap.balanceOf(alice)
    withdraw_amount = initial_amount // 4
    swap.remove_liquidity(withdraw_amount, [0] * plain_pool_size, charlie, {"from": alice})

    for coin, amount in zip(plain_coins, initial_amounts):
        assert coin.balanceOf(swap) + coin.balanceOf(charlie) == amount

    assert swap.balanceOf(alice) == initial_amount - withdraw_amount
    assert swap.totalSupply() == initial_amount - withdraw_amount


def test_remove_imbalanced(alice, charlie, swap, plain_coins, initial_amounts):
    initial_balance = swap.balanceOf(alice)
    amounts = [i // 4 for i in initial_amounts]
    swap.remove_liquidity_imbalance(amounts, initial_balance, charlie, {"from": alice})

    for i, coin in enumerate(plain_coins):
        assert coin.balanceOf(charlie) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    assert swap.balanceOf(alice) / initial_balance == 0.75


def test_remove_one_coin(alice, charlie, swap, plain_coins):
    wrapped = plain_coins[0]
    swap.remove_liquidity_one_coin(10 ** 18, 0, 0, charlie, {"from": alice})

    assert wrapped.balanceOf(charlie) > 0
    assert swap.balanceOf(charlie) == 0

    assert wrapped.balanceOf(alice) == 0
    assert swap.balanceOf(alice) > 0
