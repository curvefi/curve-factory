import math

import brownie
import pytest
from pytest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(autouse=True)
def initial_setup(add_initial_liquidity, alice, bob, gauge, coin_reward, coin_a, coin_b, swap):

    # Deposit
    swap.transfer(bob, LP_AMOUNT, {"from": alice})
    swap.approve(gauge, LP_AMOUNT, {"from": bob})
    gauge.deposit(LP_AMOUNT, {"from": bob})

    for coin in [coin_reward, coin_a, coin_b]:
        coin._mint_for_testing(alice, REWARD, {"from": alice})
        coin.approve(gauge, 2 ** 256 - 1, {"from": alice})
        gauge.add_reward(coin, alice, {"from": alice})
        gauge.deposit_reward_token(coin, REWARD, {"from": alice})


def test_claim_one_lp(bob, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_updates_claimed_reward(bob, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s
        assert gauge.claimed_reward(bob, coin) == reward


def test_claim_for_other(bob, charlie, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards(bob, {"from": charlie})

    assert coin_a.balanceOf(charlie) == 0

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)
    gauge.claim_rewards(charlie, {"from": bob})

    assert coin_a.balanceOf(bob) == 0
    assert coin_a.balanceOf(charlie) == 0

    assert coin_b.balanceOf(bob) == 0
    assert coin_b.balanceOf(charlie) == 0


@pytest.mark.no_call_coverage
def test_claim_two_lp(alice, bob, chain, gauge, swap, coin_a, coin_b):

    chain.sleep(86400)
    # Deposit
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    for acct in (alice, bob):
        gauge.claim_rewards({"from": acct})

    for coin in (coin_a, coin_b):
        # Calculate rewards
        assert coin.balanceOf(bob) > coin.balanceOf(alice) > 0
        assert math.isclose((coin.balanceOf(gauge) / REWARD), 0, abs_tol=10 ** -9)


def test_claim_set_alt_receiver(bob, charlie, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge.claim_rewards(bob, charlie, {"from": bob})

    assert coin_a.balanceOf(bob) == 0
    assert coin_b.balanceOf(bob) == 0

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(charlie)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_changing_receiver_reverts(bob, charlie, chain, gauge):
    chain.sleep(WEEK)

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    with brownie.reverts("dev: cannot redirect when claiming for another user"):
        gauge.claim_rewards(bob, charlie, {"from": charlie})
