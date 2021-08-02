import brownie
import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module", autouse=True)
def initial_setup(gauge, swap, alice):
    swap.approve(gauge, LP_AMOUNT, {"from": alice})
    gauge.deposit(LP_AMOUNT, {"from": alice})


def test_set_rewards_with_deposit(alice, coin_reward, reward_contract, swap, gauge):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"

    gauge.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert swap.balanceOf(reward_contract) == LP_AMOUNT
    assert gauge.reward_contract() == reward_contract
    assert gauge.reward_tokens(0) == coin_reward
    assert gauge.reward_tokens(1) == ZERO_ADDRESS


def test_set_rewards_no_deposit(alice, coin_reward, reward_contract, swap, gauge):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert swap.balanceOf(gauge) == LP_AMOUNT
    assert gauge.reward_contract() == reward_contract
    assert gauge.reward_tokens(0) == coin_reward
    assert gauge.reward_tokens(1) == ZERO_ADDRESS


def test_multiple_reward_tokens(alice, coin_reward, coin_a, coin_b, reward_contract, gauge):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    reward_tokens = [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5

    gauge.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})

    assert reward_tokens == [gauge.reward_tokens(i) for i in range(8)]


def test_modify_reward_tokens_less(alice, coin_reward, coin_a, coin_b, reward_contract, gauge):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge.set_rewards(
        reward_contract, sigs, [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5, {"from": alice}
    )

    reward_tokens = [coin_reward] + [ZERO_ADDRESS] * 7
    with brownie.reverts("dev: cannot modify existing reward token"):
        gauge.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})


def test_modify_reward_tokens_different(alice, coin_reward, coin_a, coin_b, reward_contract, gauge):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge.set_rewards(
        reward_contract, sigs, [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5, {"from": alice}
    )

    reward_tokens = [coin_reward, coin_b, coin_a] + [ZERO_ADDRESS] * 5
    with brownie.reverts("dev: cannot modify existing reward token"):
        gauge.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})


def test_modify_reward_tokens_more(alice, coin_reward, coin_a, coin_b, reward_contract, gauge):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge.set_rewards(reward_contract, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    reward_tokens = [coin_a, coin_reward, coin_b] + [ZERO_ADDRESS] * 5
    gauge.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})

    assert reward_tokens == [gauge.reward_tokens(i) for i in range(8)]


def test_not_a_contract(alice, coin_reward, gauge):
    with brownie.reverts("dev: not a contract"):
        gauge.set_rewards(alice, "0x00", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})


def test_deposit_no_withdraw(alice, coin_reward, reward_contract, gauge):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed withdraw"):
        gauge.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_withdraw_no_deposit(alice, coin_reward, reward_contract, gauge):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{'00' * 4}{sigs[1]}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: withdraw without deposit"):
        gauge.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_bad_deposit_sig(alice, coin_reward, reward_contract, gauge):
    sigs = [
        "12345678",
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed deposit"):
        gauge.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_bad_withdraw_sig(alice, coin_reward, reward_contract, gauge):
    sigs = [
        reward_contract.stake.signature[2:],
        "12345678",
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed withdraw"):
        gauge.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_no_reward_token(alice, reward_contract, gauge):
    with brownie.reverts("dev: no reward token"):
        gauge.set_rewards(reward_contract, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})


def test_bad_claim_sig(alice, coin_reward, reward_contract, gauge):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{'00' * 4}{'00' * 20}"

    with brownie.reverts("dev: bad claim sig"):
        gauge.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )
