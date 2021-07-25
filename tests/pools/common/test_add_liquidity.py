import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_add_liquidity(bob, swap, coins, initial_amounts, eth_amount):
    swap.add_liquidity(initial_amounts, 0, {"from": bob, "value": eth_amount(initial_amounts[0])})

    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            bob.balance() == 0
            swap.balance() == amount * 2
            continue

        assert coin.balanceOf(bob) == 0
        assert coin.balanceOf(swap) == amount * 2

    ideal = len(coins) * 1_000_000 * 10 ** 18
    assert abs(swap.balanceOf(bob) - ideal) <= 1
    assert abs(swap.totalSupply() - ideal * 2) <= 2


@pytest.mark.parametrize("idx", range(2))
def test_add_one_coin(bob, swap, coins, initial_amounts, idx, eth_amount):
    amounts = [0] * len(coins)
    amounts[idx] = initial_amounts[idx]

    swap.add_liquidity(amounts, 0, {"from": bob, "value": eth_amount(amounts[0])})

    for i, coin in enumerate(coins):
        if coin == ETH_ADDRESS:
            bob.balance() == initial_amounts[0] - amounts[0]
            swap.balance() == initial_amounts[0] + amounts[0]
            continue

        assert coin.balanceOf(bob) == initial_amounts[i] - amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] + amounts[i]

    difference = abs(swap.balanceOf(bob) - (10 ** 18 * 1_000_000))
    assert difference / (10 ** 18 * 1_000_000) < 0.01


def test_insufficient_balance(charlie, swap, decimals):
    amounts = [(10 ** i) for i in decimals]

    with brownie.reverts():  # invalid approval or balance
        swap.add_liquidity(amounts, 0, {"from": charlie})


def test_min_amount_too_high(bob, swap, initial_amounts, plain_pool_size, eth_amount):
    with brownie.reverts():
        swap.add_liquidity(
            initial_amounts,
            plain_pool_size * 1_000_000 * 10 ** 18 + 1,
            {"from": bob, "value": eth_amount(initial_amounts[0])},
        )


def test_event(bob, swap, initial_amounts, eth_amount):
    tx = swap.add_liquidity(
        initial_amounts, 0, {"from": bob, "value": eth_amount(initial_amounts[0])}
    )

    event = tx.events["AddLiquidity"]
    assert event["provider"] == bob
    assert event["token_amounts"] == initial_amounts
    assert event["token_supply"] == swap.totalSupply()


def test_send_eth(bob, swap, initial_amounts):
    with brownie.reverts():
        swap.add_liquidity(initial_amounts, 0, {"from": bob, "value": 1})
