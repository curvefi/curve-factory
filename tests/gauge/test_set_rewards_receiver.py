import pytest
from pytest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(autouse=True)
def initial_setup(
    alice, add_initial_liquidity, bob, chain, gauge, coin_reward, coin_a, coin_b, swap
):

    for coin in [coin_reward, coin_a, coin_b]:
        gauge.add_reward(coin, alice, {"from": alice})
        coin._mint_for_testing(alice, REWARD, {"from": alice})
        coin.approve(gauge, 2 ** 256 - 1, {"from": alice})
        gauge.deposit_reward_token(coin, REWARD, {"from": alice})

    # Deposit
    swap.transfer(bob, LP_AMOUNT, {"from": alice})
    swap.approve(gauge, LP_AMOUNT, {"from": bob})
    gauge.deposit(LP_AMOUNT, {"from": bob})

    chain.sleep(WEEK)


def test_claim_one_lp(alice, bob, chain, gauge, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge.set_rewards_receiver(alice, {"from": bob})

    gauge.withdraw(LP_AMOUNT, {"from": bob})
    gauge.claim_rewards({"from": bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(alice)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s
