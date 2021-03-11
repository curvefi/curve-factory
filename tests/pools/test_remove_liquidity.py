import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("min_amount", (0, 1))
def test_remove_liquidity(alice, swap, wrapped_coins, min_amount, initial_amounts):
    swap.remove_liquidity(
        swap.balanceOf(alice),
        [i * min_amount for i in initial_amounts],
        {"from": alice},
    )

    for coin, amount in zip(wrapped_coins, initial_amounts):
        assert coin.balanceOf(alice) == amount
        assert coin.balanceOf(swap) == 0

    assert swap.balanceOf(alice) == 0
    assert swap.totalSupply() == 0


def test_remove_partial(alice, swap, wrapped_coins, initial_amounts):
    initial_amount = swap.balanceOf(alice)
    withdraw_amount = initial_amount // 2
    swap.remove_liquidity(withdraw_amount, [0, 0], {"from": alice})

    for coin, amount in zip(wrapped_coins, initial_amounts):
        assert coin.balanceOf(swap) + coin.balanceOf(alice) == amount

    assert swap.balanceOf(alice) == initial_amount - withdraw_amount
    assert swap.totalSupply() == initial_amount - withdraw_amount


@pytest.mark.parametrize("idx", range(2))
def test_below_min_amount(alice, swap, initial_amounts, idx):
    min_amount = initial_amounts.copy()
    min_amount[idx] += 1

    with brownie.reverts():
        swap.remove_liquidity(swap.balanceOf(alice), min_amount, {"from": alice})


def test_amount_exceeds_balance(alice, swap):
    with brownie.reverts():
        swap.remove_liquidity(swap.balanceOf(alice) + 1, [0, 0], {"from": alice})


def test_event(alice, bob, swap, wrapped_coins):
    swap.transfer(bob, 10 ** 18, {"from": alice})
    tx = swap.remove_liquidity(10 ** 18, [0, 0], {"from": bob})

    event = tx.events["RemoveLiquidity"]
    assert event["provider"] == bob
    assert event["token_supply"] == swap.totalSupply()
    for coin, amount in zip(wrapped_coins, event["token_amounts"]):
        assert coin.balanceOf(bob) == amount
