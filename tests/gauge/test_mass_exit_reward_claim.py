import math

import pytest

REWARD = 10 ** 20
WEEK = 7 * 86400


@pytest.fixture(autouse=True)
def initial_setup(
    add_initial_liquidity,
    alice,
    accounts,
    chain,
    coin_reward,
    swap,
    gauge,
    gauge_controller,
):
    # gauge setup
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(gauge, 0, 0, {"from": alice})

    # deposit into gauge
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})

    for acct in accounts[:10]:
        gauge.deposit(10 ** 18, acct, {"from": alice})

    # add rewards
    gauge.add_reward(coin_reward, alice, {"from": alice})

    # fund rewards
    coin_reward._mint_for_testing(alice, REWARD, {"from": alice})
    coin_reward.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit_reward_token(coin_reward, REWARD, {"from": alice})

    # sleep half way through the reward period
    chain.sleep(WEEK)


def test_mass_withdraw_claim_rewards(accounts, gauge, coin_reward):
    for account in accounts[:10]:
        gauge.withdraw(gauge.balanceOf(account), {"from": account})
        assert gauge.claimed_reward(account, coin_reward) == 0

    for account in accounts[:10]:
        gauge.claim_rewards({"from": account})
        assert math.isclose(coin_reward.balanceOf(account), REWARD / 10)
