import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("min_amount", (0, 1))
def test_remove_liquidity(alice, swap, coins, min_amount, initial_amounts):
    swap.remove_liquidity(
        swap.balanceOf(alice), [i * min_amount for i in initial_amounts], {"from": alice}
    )

    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            assert alice.balance() == amount
            assert swap.balance() == 0
            continue

        assert coin.balanceOf(alice) == amount
        assert coin.balanceOf(swap) == 0

    assert swap.balanceOf(alice) == 0
    assert swap.totalSupply() == 0


def test_remove_partial(alice, swap, coins, initial_amounts, plain_pool_size):
    initial_amount = swap.balanceOf(alice)
    withdraw_amount = initial_amount // 2
    swap.remove_liquidity(withdraw_amount, [0] * plain_pool_size, {"from": alice})

    for coin, amount in zip(coins, initial_amounts):
        if coin == ETH_ADDRESS:
            assert swap.balance() + alice.balance() == amount
            continue

        assert coin.balanceOf(swap) + coin.balanceOf(alice) == amount

    assert swap.balanceOf(alice) == initial_amount - withdraw_amount
    assert swap.totalSupply() == initial_amount - withdraw_amount


@pytest.mark.parametrize("idx", range(2))
def test_below_min_amount(alice, swap, initial_amounts, idx):
    min_amount = initial_amounts.copy()
    min_amount[idx] += 1

    with brownie.reverts():
        swap.remove_liquidity(swap.balanceOf(alice), min_amount, {"from": alice})


def test_amount_exceeds_balance(alice, swap, plain_pool_size):
    with brownie.reverts():
        swap.remove_liquidity(swap.balanceOf(alice) + 1, [0] * plain_pool_size, {"from": alice})


def test_event(alice, bob, swap, coins, plain_pool_size):
    swap.transfer(bob, 10 ** 18, {"from": alice})
    tx = swap.remove_liquidity(10 ** 18, [0] * plain_pool_size, {"from": bob})

    event = tx.events["RemoveLiquidity"]
    assert event["provider"] == bob
    assert event["token_supply"] == swap.totalSupply()
    for coin, amount in zip(coins, event["token_amounts"]):
        if coin == ETH_ADDRESS:
            assert bob.balance() - 1_000_000 * 10 ** 18 == amount
            continue
        assert coin.balanceOf(bob) == amount
