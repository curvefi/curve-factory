import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie_tokens import ERC20

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(autouse=True)
def initial_setup(gauge, swap, alice, add_initial_liquidity):
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})


def test_set_rewards_no_deposit(alice, coin_reward, swap, gauge):
    gauge.add_reward(coin_reward, alice, {"from": alice})

    assert swap.balanceOf(gauge) == LP_AMOUNT
    assert gauge.reward_tokens(0) == coin_reward
    assert gauge.reward_tokens(1) == ZERO_ADDRESS


def test_multiple_reward_tokens(alice, coin_reward, coin_a, coin_b, gauge):
    for coin in [coin_reward, coin_a, coin_b]:
        gauge.add_reward(coin, alice, {"from": alice})

    assert [coin_reward, coin_a, coin_b] == [gauge.reward_tokens(i) for i in range(3)]


def test_cant_exceed_max(alice, gauge):
    for _ in range(8):
        gauge.add_reward(ERC20(), alice, {"from": alice})
    with brownie.reverts():
        gauge.add_reward(ERC20(), alice, {"from": alice})
