import math

import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie_tokens import ERC20

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob", "mint_bob")


REWARD = 10 ** 20


def test_rewards_are_forwarded(alice, swap, base_gauge, meta_gauge, coin_reward):
    # checkpointing happens when liquidity updates
    # add_liquidity, remove_liquidity, remove_liquidity_*
    # currently alice has all the liquidity, so 100% of the rewards

    base_gauge.set_rewards(ZERO_ADDRESS, "0x0", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})
    coin_reward._mint_for_testing(base_gauge, REWARD, {"from": alice})

    assert coin_reward.balanceOf(alice) == 0

    swap.remove_liquidity(10 ** 18, [0, 0], {"from": alice})

    assert coin_reward.balanceOf(meta_gauge) == REWARD


def test_base_rewards_are_distributed_instantly(alice, swap, base_gauge, meta_gauge, coin_reward):
    # base rewards aren't distributed over the course of a week, instead they are instantly
    # distributed amongst the LPs in the pool. This is because the base_gauge already has some form
    # of delay, adding a second delay would not make much sense.

    base_gauge.set_rewards(ZERO_ADDRESS, "0x0", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})
    coin_reward._mint_for_testing(base_gauge, REWARD, {"from": alice})

    assert coin_reward.balanceOf(alice) == 0

    swap.remove_liquidity(10 ** 18, [0, 0], {"from": alice})

    meta_gauge.claim_rewards({"from": alice})
    assert coin_reward.balanceOf(alice) == REWARD


def test_base_rewards_and_additional_rewards_are_distributed(
    alice, chain, base_gauge, meta_gauge, coin_reward
):
    # base rewards aren't distributed over the course of a week, instead they are instantly
    # distributed amongst the LPs in the pool. This is because the base_gauge already has some form
    # of delay, adding a second delay would not make much sense.
    dummy_reward = ERC20()
    dummy_reward._mint_for_testing(alice, REWARD, {"from": alice})
    dummy_reward.approve(meta_gauge, 2 ** 256 - 1, {"from": alice})

    base_gauge.set_rewards(ZERO_ADDRESS, "0x0", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})
    coin_reward._mint_for_testing(base_gauge, REWARD, {"from": alice})

    assert coin_reward.balanceOf(alice) == 0

    meta_gauge.add_reward(dummy_reward, alice, {"from": alice})
    meta_gauge.deposit_reward_token(dummy_reward, REWARD, {"from": alice})

    chain.sleep(86400)

    meta_gauge.claim_rewards({"from": alice})

    assert coin_reward.balanceOf(alice) == REWARD
    assert math.isclose(dummy_reward.balanceOf(alice), REWARD // 7, rel_tol=0.0001)


def test_only_deployer_or_factory_admin_can_add_rewards(bob, meta_gauge, coin_reward):
    with brownie.reverts():
        meta_gauge.add_reward(coin_reward, bob, {"from": bob})


def test_duplicate_rewards(alice, chain, base_gauge, meta_gauge, coin_reward):
    # duplicate rewards get treated as base rewards
    # base rewards aren't distributed over the course of a week, instead they are instantly
    # distributed amongst the LPs in the pool. This is because the base_gauge already has some form
    # of delay, adding a second delay would not make much sense.

    base_gauge.set_rewards(ZERO_ADDRESS, "0x0", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})
    coin_reward._mint_for_testing(base_gauge, REWARD, {"from": alice})

    assert coin_reward.balanceOf(alice) == 0

    coin_reward._mint_for_testing(alice, REWARD, {"from": alice})
    coin_reward.approve(meta_gauge, REWARD, {"from": alice})

    meta_gauge.add_reward(coin_reward, alice, {"from": alice})
    meta_gauge.deposit_reward_token(coin_reward, REWARD, {"from": alice})

    chain.sleep(86400)

    meta_gauge.claim_rewards({"from": alice})

    assert coin_reward.balanceOf(alice) == REWARD * 2
