import itertools as it

import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

DAY = 86400


@pytest.fixture(params=[ZERO_ADDRESS, ETH_ADDRESS], ids=["GlobalDelegation", "GaugeDelegation"])
def delegated_gauge(request):
    return request.param


@pytest.fixture(autouse=True)
def setup(alice, chain, bob, charlie, dave, boost_delegation, lock_crv, delegated_gauge):
    boost_delegation.delegate_boost(
        alice,
        delegated_gauge,
        bob,
        10_000,
        chain.time() + DAY * 30,
        chain.time() + DAY * 365,
        {"from": alice},
    )
    for user, operator in zip([alice, bob], [charlie, dave]):
        boost_delegation.set_operator(operator, {"from": user})


@pytest.mark.parametrize("is_operator", [0, 1])
def test_delegator_or_operator_cancels(
    alice, bob, chain, charlie, boost_delegation, delegated_gauge, is_operator
):
    caller = charlie if is_operator else alice
    chain.sleep(DAY * 30)  # must wait after the 30 days
    tx = boost_delegation.cancel_delegation(alice, delegated_gauge, {"from": caller})

    assert boost_delegation.get_delegated_to(alice, delegated_gauge) == [ZERO_ADDRESS, 0, 0, 0]
    assert boost_delegation.get_delegation_data(bob, delegated_gauge, 0) == [ZERO_ADDRESS, 0, 0, 0]
    assert "CancelledDelegation" in tx.events
    assert tx.events["CancelledDelegation"].values() == [alice, delegated_gauge, bob, caller]


@pytest.mark.parametrize("is_operator,timedelta", it.product([0, 1], repeat=2))
def test_delegatee_or_operator_cancels_at_anytime(
    alice, chain, bob, dave, boost_delegation, delegated_gauge, is_operator, timedelta
):
    caller = dave if is_operator else bob
    chain.sleep(DAY * int(29.5 + timedelta))  # before or after cancellable time
    tx = boost_delegation.cancel_delegation(alice, delegated_gauge, {"from": caller})

    assert boost_delegation.get_delegated_to(alice, delegated_gauge) == [ZERO_ADDRESS, 0, 0, 0]
    assert boost_delegation.get_delegation_data(bob, delegated_gauge, 0) == [ZERO_ADDRESS, 0, 0, 0]
    assert "CancelledDelegation" in tx.events
    assert tx.events["CancelledDelegation"].values() == [alice, delegated_gauge, bob, caller]


@pytest.mark.parametrize("is_operator", [0, 1])
def test_delegator_or_operator_cancel_reverts_before_allowed_time(
    alice, chain, charlie, boost_delegation, delegated_gauge, is_operator
):
    caller = charlie if is_operator else alice
    chain.sleep(DAY * 29)
    with brownie.reverts("Not yet cancellable"):
        boost_delegation.cancel_delegation(alice, delegated_gauge, {"from": caller})


def test_third_party_cannot_cancel(alice, erin, boost_delegation, delegated_gauge):
    with brownie.reverts("Only delegator or delegator's operator"):
        boost_delegation.cancel_delegation(alice, delegated_gauge, {"from": erin})
