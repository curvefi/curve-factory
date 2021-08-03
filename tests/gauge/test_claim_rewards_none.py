import pytest

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


def test_claim_no_deposit(alice, bob, chain, gauge, swap, coin_reward):
    # Fund
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(alice, REWARD, {"from": alice})
    coin_reward.approve(gauge, REWARD, {"from": alice})
    gauge.add_reward(coin_reward, alice, {"from": alice})
    gauge.deposit_reward_token(coin_reward, REWARD, {"from": alice})

    chain.sleep(WEEK)

    gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(alice, bob, chain, gauge, swap, coin_reward):
    # Deposit
    swap.transfer(bob, LP_AMOUNT, {"from": alice})
    swap.approve(gauge, LP_AMOUNT, {"from": bob})
    gauge.deposit(LP_AMOUNT, {"from": bob})

    gauge.add_reward(coin_reward, alice, {"from": alice})

    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0
