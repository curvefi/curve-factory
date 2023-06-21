from math import isclose

import pytest

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


def test_no_approval_needed(alice, bob, gauge, swap):
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(100_000, bob, {"from": alice})

    assert gauge.balanceOf(bob) == 100_000


def test_deposit_for_and_claim_rewards(alice, bob, chain, gauge, swap, coin_reward):
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(LP_AMOUNT, bob, {"from": alice})

    gauge.add_reward(coin_reward, alice, {"from": alice})

    coin_reward._mint_for_testing(alice, REWARD, {"from": alice})
    coin_reward.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit_reward_token(coin_reward, REWARD, {"from": alice})

    chain.mine(timedelta=WEEK)

    # alice deposits for bob and claims rewards for him
    gauge.deposit(LP_AMOUNT, bob, True, {"from": alice})

    assert isclose(REWARD, coin_reward.balanceOf(bob), rel_tol=0.001)
