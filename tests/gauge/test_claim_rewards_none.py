from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(alice, bob, chain, gauge, swap, reward_contract, coin_reward):
    # Fund
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(reward_contract, REWARD)
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})

    gauge.set_rewards(
        reward_contract,
        "0xa694fc3a2e1a7d4d3d18b9120000000000000000000000000000000000000000",
        [coin_reward] + [ZERO_ADDRESS] * 7,
        {"from": alice},
    )

    chain.sleep(WEEK)

    gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(alice, bob, chain, gauge, swap, reward_contract, coin_reward):
    # Deposit
    swap.transfer(bob, LP_AMOUNT, {"from": alice})
    swap.approve(gauge, LP_AMOUNT, {"from": bob})
    gauge.deposit(LP_AMOUNT, {"from": bob})

    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0
