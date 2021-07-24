import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_add_liquidity(bob, swap, plain_coins, initial_amounts):
    swap.add_liquidity(initial_amounts, 0, {"from": bob})

    for coin, amount in zip(plain_coins, initial_amounts):
        assert coin.balanceOf(bob) == 0
        assert coin.balanceOf(swap) == amount * 2

    ideal = len(plain_coins) * 1_000_000 * 10 ** 18
    assert abs(swap.balanceOf(bob) - ideal) <= 1
    assert abs(swap.totalSupply() - ideal * 2) <= 2


@pytest.mark.parametrize("idx", range(2))
def test_add_one_coin(bob, swap, plain_coins, initial_amounts, idx):
    amounts = [0] * len(plain_coins)
    amounts[idx] = initial_amounts[idx]

    swap.add_liquidity(amounts, 0, {"from": bob})

    for i, coin in enumerate(plain_coins):
        assert coin.balanceOf(bob) == initial_amounts[i] - amounts[i]
        assert coin.balanceOf(swap) == initial_amounts[i] + amounts[i]

    difference = abs(swap.balanceOf(bob) - (10 ** 18 * 1_000_000))
    assert difference / (10 ** 18 * 1_000_000) < 0.01


def test_insufficient_balance(charlie, swap, decimals):
    amounts = [(10 ** i) for i in decimals]

    with brownie.reverts():  # invalid approval or balance
        swap.add_liquidity(amounts, 0, {"from": charlie})


def test_min_amount_too_high(bob, swap, initial_amounts, plain_pool_size):
    with brownie.reverts():
        swap.add_liquidity(
            initial_amounts, plain_pool_size * 1_000_000 * 10 ** 18 + 1, {"from": bob}
        )


def test_event(bob, swap, initial_amounts):
    tx = swap.add_liquidity(initial_amounts, 0, {"from": bob})

    event = tx.events["AddLiquidity"]
    assert event["provider"] == bob
    assert event["token_amounts"] == initial_amounts
    assert event["token_supply"] == swap.totalSupply()


# def test_send_eth(bob, swap, plain_coins, initial_amounts):
#     with brownie.reverts():
#         swap.add_liquidity(initial_amounts, 0, {"from": bob, "value": 1})
