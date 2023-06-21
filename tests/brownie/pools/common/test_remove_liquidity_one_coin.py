import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(2))
def test_amount_received(alice, swap, coins, decimals, idx):
    decimals = decimals[idx]
    wrapped = coins[idx]

    swap.remove_liquidity_one_coin(10 ** 18, idx, 0, {"from": alice})

    ideal = 10 ** decimals

    if wrapped == ETH_ADDRESS:
        assert ideal * 0.99 <= alice.balance() <= ideal
    else:
        assert ideal * 0.99 <= wrapped.balanceOf(alice) <= ideal


@pytest.mark.parametrize("idx", range(2))
@pytest.mark.parametrize("divisor", [1, 5, 42])
def test_lp_token_balance(alice, swap, idx, divisor):
    initial_amount = swap.balanceOf(alice)
    amount = initial_amount // divisor

    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    assert swap.balanceOf(alice) + amount == initial_amount


@pytest.mark.parametrize("idx", range(2))
def test_expected_vs_actual(alice, swap, coins, idx):
    amount = swap.balanceOf(alice) // 10

    expected = swap.calc_withdraw_one_coin(amount, idx)
    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    if coins[idx] == ETH_ADDRESS:
        assert alice.balance() == expected
    else:
        assert coins[idx].balanceOf(alice) == expected


@pytest.mark.parametrize("idx", range(2))
def test_below_min_amount(alice, swap, idx):
    amount = swap.balanceOf(alice)

    expected = swap.calc_withdraw_one_coin(amount, idx)
    with brownie.reverts():
        swap.remove_liquidity_one_coin(amount, idx, expected + 1, {"from": alice})


@pytest.mark.parametrize("idx", range(2))
def test_amount_exceeds_balance(bob, swap, idx):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, idx, 0, {"from": bob})


def test_below_zero(alice, swap):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, -1, 0, {"from": alice})


def test_above_n_coins(alice, swap, plain_pool_size):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, plain_pool_size, 0, {"from": alice})


@pytest.mark.parametrize("idx", range(2))
def test_event(alice, bob, swap, idx, coins):
    swap.transfer(bob, 10 ** 18, {"from": alice})

    tx = swap.remove_liquidity_one_coin(10 ** 18, idx, 0, {"from": bob})

    event = tx.events["RemoveLiquidityOne"]
    assert event["provider"] == bob
    assert event["token_amount"] == 10 ** 18

    coin = coins[idx]
    if coin == ETH_ADDRESS:
        assert bob.balance() - 1_000_000 * 10 ** 18 == event["coin_amount"]
    else:
        assert coin.balanceOf(bob) == event["coin_amount"]
