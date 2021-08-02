from math import isclose

from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_no_approval_needed(alice, bob, gauge, swap):
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(100_000, bob, {"from": alice})

    assert gauge.balanceOf(bob) == 100_000


def test_deposit_for_and_claim_rewards(
    alice, bob, chain, gauge, swap, reward_contract, coin_reward
):
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(LP_AMOUNT, bob, {"from": alice})

    coin_reward._mint_for_testing(reward_contract, REWARD)
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})

    gauge.set_rewards(
        reward_contract,
        "0xa694fc3a2e1a7d4d3d18b9120000000000000000000000000000000000000000",
        [coin_reward] + [ZERO_ADDRESS] * 7,
        {"from": alice},
    )

    chain.mine(timedelta=WEEK)

    # alice deposits for bob and claims rewards for him
    gauge.deposit(LP_AMOUNT, bob, True, {"from": alice})

    assert isclose(REWARD, coin_reward.balanceOf(bob), rel_tol=0.001)
