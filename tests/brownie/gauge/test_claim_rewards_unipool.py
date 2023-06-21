import pytest
from pytest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(autouse=True)
def initial_setup(
    add_initial_liquidity,
    alice,
    bob,
    coin_reward,
    swap,
    gauge,
    gauge_controller,
):
    # gauge setup
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(gauge, 0, 0, {"from": alice})

    # deposit into gauge
    swap.transfer(bob, LP_AMOUNT, {"from": alice})
    swap.approve(gauge, LP_AMOUNT, {"from": bob})
    gauge.deposit(LP_AMOUNT, {"from": bob})

    # add rewards
    gauge.add_reward(coin_reward, alice, {"from": alice})

    # fund rewards
    coin_reward._mint_for_testing(alice, REWARD, {"from": alice})
    coin_reward.approve(gauge, REWARD, {"from": alice})
    gauge.deposit_reward_token(coin_reward, REWARD, {"from": alice})


def test_claim_one_lp(bob, chain, gauge, coin_reward):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other(bob, charlie, chain, gauge, coin_reward):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards(bob, {"from": charlie})

    assert coin_reward.balanceOf(charlie) == 0

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge, coin_reward):
    chain.sleep(WEEK)
    gauge.claim_rewards(charlie, {"from": bob})

    assert coin_reward.balanceOf(bob) == 0
    assert coin_reward.balanceOf(charlie) == 0


def test_claim_two_lp(alice, bob, chain, gauge, swap, coin_reward):

    # Deposit
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    # Calculate rewards
    claimable_rewards = [
        gauge.claimable_reward.call(acc, coin_reward, {"from": acc}) for acc in (alice, bob)
    ]

    # Claim rewards
    rewards = []
    for acct in (alice, bob):
        gauge.claim_rewards({"from": acct})
        rewards += [coin_reward.balanceOf(acct)]

    # Calculation == results
    assert tuple(claimable_rewards) == tuple(rewards)

    # Approximately equal apart from what caused by 1 s ganache-cli jitter
    assert sum(rewards) <= REWARD
    assert approx(sum(rewards), REWARD, 1.001 / WEEK)  # ganache-cli jitter of 1 s
    assert approx(rewards[0], rewards[1], 2.002 * WEEK)
