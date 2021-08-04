import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

DAY = 86400


@pytest.fixture(params=[ZERO_ADDRESS, ETH_ADDRESS], ids=["GlobalDelegation", "GaugeDelegation"])
def delegated_gauge(request):
    return request.param


@pytest.fixture(autouse=True)
def setup(alice, chain, bob, boost_delegation, lock_crv, delegated_gauge):
    boost_delegation.delegate_boost(
        alice,
        delegated_gauge,
        bob,
        10_000,
        chain.time() + DAY * 30,
        chain.time() + DAY * 365,
        {"from": alice},
    )


def test_update_clears_expired_delegations(alice, bob, boost_delegation, chain, delegated_gauge):
    chain.sleep(DAY * 366)

    boost_delegation.update_delegation_records(bob, delegated_gauge, {"from": bob})

    assert boost_delegation.delegation_count(alice) == 0
    assert boost_delegation.get_delegated_to(alice, delegated_gauge) == [ZERO_ADDRESS, 0, 0, 0]
    assert boost_delegation.get_delegation_data(bob, delegated_gauge, 0) == [ZERO_ADDRESS, 0, 0, 0]


def test_update_clears_only_expired_delegations(
    alice, bob, charlie, chain, boost_delegation, delegated_gauge
):

    chain.sleep(DAY * 366)

    other_gauge = ZERO_ADDRESS if delegated_gauge == ZERO_ADDRESS else charlie

    boost_delegation.delegate_boost(
        alice,
        other_gauge,
        bob,
        10_000,
        chain.time() + DAY * 30,
        chain.time() + DAY * 365,
        {"from": alice},
    )

    boost_delegation.update_delegation_records(bob, delegated_gauge, {"from": charlie})

    assert boost_delegation.get_delegated_to(alice, other_gauge)[:2] == [bob, 10_000]
    assert boost_delegation.get_delegation_data(bob, other_gauge, 0)[:2] == [alice, 10_000]

    if other_gauge == ZERO_ADDRESS:
        # ZERO_ADDRESS -> ZERO_ADDRESS
        return

    assert boost_delegation.delegation_count(alice) == 1
    assert boost_delegation.get_delegated_to(alice, delegated_gauge) == [ZERO_ADDRESS, 0, 0, 0]
    assert boost_delegation.get_delegation_data(bob, delegated_gauge, 0) == [ZERO_ADDRESS, 0, 0, 0]


def test_update_is_a_noop_before_expiration(
    alice, bob, charlie, chain, boost_delegation, delegated_gauge
):
    chain.sleep(DAY * 183)

    boost_delegation.update_delegation_records(bob, delegated_gauge, {"from": charlie})

    assert boost_delegation.delegation_count(alice) == 1
    assert boost_delegation.get_delegated_to(alice, delegated_gauge)[:2] == [bob, 10_000]
    assert boost_delegation.get_delegation_data(bob, delegated_gauge, 0)[:2] == [alice, 10_000]
