import itertools as it
import math

import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

DAY = 86400


@pytest.mark.parametrize(
    "delegated_gauge,percentage", it.product([ZERO_ADDRESS, ETH_ADDRESS], range(1000, 10_000, 1000))
)
def test_delegation_adjustment(
    alice, bob, boost_delegation, chain, voting_escrow, lock_crv, delegated_gauge, percentage
):
    boost_delegation.delegate_boost(
        alice,
        delegated_gauge,
        bob,
        percentage,
        chain.time() + DAY * 30,
        chain.time() + DAY * 365,
        {"from": alice},
    )

    alice_vecrv_balance = voting_escrow.balanceOf(alice)
    ratio = percentage / 10_000

    alice_adjusted_vecrv_bal = boost_delegation.get_adjusted_vecrv_balance(alice, delegated_gauge)
    bob_adjusted_vecrv_bal = boost_delegation.get_adjusted_vecrv_balance(bob, delegated_gauge)

    assert math.isclose(alice_adjusted_vecrv_bal, (1 - ratio) * alice_vecrv_balance, rel_tol=0.0001)
    assert math.isclose(bob_adjusted_vecrv_bal, ratio * alice_vecrv_balance, rel_tol=0.0001)


@pytest.mark.parametrize("delegated_gauge", [ZERO_ADDRESS, ETH_ADDRESS])
def test_delegation_adjustment_after_expiry(
    alice, bob, boost_delegation, chain, voting_escrow, lock_crv, delegated_gauge
):
    boost_delegation.delegate_boost(
        alice,
        delegated_gauge,
        bob,
        10_000,
        chain.time() + DAY * 30,
        chain.time() + DAY * 365,
        {"from": alice},
    )

    chain.mine(timedelta=DAY * 365 + 1)

    alice_vecrv_balance = voting_escrow.balanceOf(alice)

    brownie.multicall.deploy({"from": alice})

    with brownie.multicall(block_identifier=chain.height):
        alice_adj_vecrv_bal = boost_delegation.get_adjusted_vecrv_balance(alice, delegated_gauge)
        bob_adjusted_vecrv_bal = boost_delegation.get_adjusted_vecrv_balance(bob, delegated_gauge)
        alice_vecrv_balance = voting_escrow.balanceOf(alice)

    assert alice_adj_vecrv_bal == alice_vecrv_balance
    assert bob_adjusted_vecrv_bal == 0
