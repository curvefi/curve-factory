import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_add_liquidity(bob, charlie, swap, initial_amounts, eth_amount):
    swap.add_liquidity(
        initial_amounts, 0, charlie, {"from": bob, "value": eth_amount(initial_amounts[0])}
    )

    assert swap.balanceOf(bob) == 0
    assert swap.balanceOf(charlie) > 0


def test_exchange(alice, charlie, swap, coins):
    coins[1]._mint_for_testing(alice, 10 ** 18, {"from": alice})

    swap.exchange(1, 0, 10 ** 18, 0, charlie, {"from": alice})
    if coins[0] == ETH_ADDRESS:
        assert charlie.balance() > 0
        assert alice.balance() == 0
    else:
        assert coins[0].balanceOf(charlie) > 0
        assert coins[0].balanceOf(alice) == 0


def test_remove_liquidity(alice, swap, charlie, coins, initial_amounts, plain_pool_size):
    initial_amount = swap.balanceOf(alice)
    withdraw_amount = initial_amount // 4
    charlie_pre_bal = charlie.balance()
    swap.remove_liquidity(withdraw_amount, [0] * plain_pool_size, charlie, {"from": alice})

    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            assert swap.balance() + charlie.balance() - charlie_pre_bal == amount
            continue

        assert coin.balanceOf(swap) + coin.balanceOf(charlie) == amount

    assert swap.balanceOf(alice) == initial_amount - withdraw_amount
    assert swap.totalSupply() == initial_amount - withdraw_amount


def test_remove_imbalanced(alice, charlie, swap, coins, initial_amounts):
    initial_balance = swap.balanceOf(alice)
    amounts = [i // 4 for i in initial_amounts]
    charlie_pre_bal = charlie.balance()
    swap.remove_liquidity_imbalance(amounts, initial_balance, charlie, {"from": alice})

    for i, coin in enumerate(coins):
        if coin == ETH_ADDRESS:
            assert charlie.balance() - charlie_pre_bal == amounts[i]
            assert swap.balance() == initial_amounts[i] - amounts[i]
            continue

        assert coin.balanceOf(charlie) == amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] - amounts[i]

    assert swap.balanceOf(alice) / initial_balance == 0.75


def test_remove_one_coin(alice, charlie, swap, coins, is_eth_pool):
    wrapped = coins[0]
    swap.remove_liquidity_one_coin(10 ** 18, 0, 0, charlie, {"from": alice})

    if is_eth_pool:
        assert charlie.balance() > 0
        assert alice.balance() == 0
    else:
        assert wrapped.balanceOf(charlie) > 0
        assert wrapped.balanceOf(alice) == 0

    assert swap.balanceOf(charlie) == 0
    assert swap.balanceOf(alice) > 0
