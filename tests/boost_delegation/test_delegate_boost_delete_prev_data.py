import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

pytestmark = pytest.mark.usefixtures("lock_crv")

DAY = 86400


@pytest.mark.parametrize("gauge_to", [ZERO_ADDRESS, ETH_ADDRESS])
def test_expired_delegation_is_implicitly_deleted_delegatee(
    alice, bob, boost_delegation, chain, gauge_to
):
    boost_delegation.delegate_boost(
        alice,
        gauge_to,
        bob,
        10000,
        chain.time() + DAY * 31,  # cancel time
        chain.time() + DAY * 365,  # expire time
        {"from": alice},
    )

    chain.sleep(DAY * 366)

    tx = boost_delegation.delegate_boost(
        alice,
        gauge_to,
        bob,
        10000,
        chain.time() + DAY * 31,  # cancel time
        chain.time() + DAY * 365,  # expire time
        {"from": alice},
    )

    data = boost_delegation.get_delegation_data(bob, gauge_to, 0)
    delegation_tx_time = tx.timestamp
    expected = (alice, 10_000, delegation_tx_time + DAY * 31, delegation_tx_time + DAY * 365)

    assert data[:2] == expected[:2]
    assert abs(data[2] - expected[2]) <= 1
    assert abs(data[3] - expected[3]) <= 1
    assert boost_delegation.delegation_count(alice) == 1


@pytest.mark.parametrize("gauge_to", [ZERO_ADDRESS, ETH_ADDRESS])
def test_expired_delegation_is_implicitly_deleted_delegator(
    alice, bob, boost_delegation, chain, gauge_to
):
    boost_delegation.delegate_boost(
        alice,
        gauge_to,
        bob,
        10000,
        chain.time() + DAY * 31,  # cancel time
        chain.time() + DAY * 365,  # expire time
        {"from": alice},
    )

    chain.sleep(DAY * 366)

    tx = boost_delegation.delegate_boost(
        alice,
        gauge_to,
        bob,
        10000,
        chain.time() + DAY * 31,  # cancel time
        chain.time() + DAY * 365,  # expire time
        {"from": alice},
    )

    data = boost_delegation.get_delegated_to(alice, gauge_to)
    delegation_tx_time = tx.timestamp
    expected = (bob, 10_000, delegation_tx_time + DAY * 31, delegation_tx_time + DAY * 365)
    assert data[:2] == expected[:2]
    assert abs(data[2] - expected[2]) <= 1
    assert abs(data[3] - expected[3]) <= 1


@pytest.mark.parametrize(
    "gauge_a,gauge_b", [(ZERO_ADDRESS, ETH_ADDRESS), (ETH_ADDRESS, ZERO_ADDRESS)]
)
def test_going_from_global_to_per_pool_requires_state_update(
    alice, bob, boost_delegation, chain, gauge_a, gauge_b
):
    a_msg, b_msg = ("globally", "per-gauge") if gauge_a == ETH_ADDRESS else ("per-gauge", "global")

    boost_delegation.delegate_boost(
        alice,
        gauge_a,
        bob,
        10000,
        chain.time() + DAY * 31,  # cancel time
        chain.time() + DAY * 365,  # expire time
        {"from": alice},
    )

    chain.sleep(DAY * 366)

    with brownie.reverts(f"Cannot delegate {a_msg} while {b_msg} is active"):
        boost_delegation.delegate_boost(
            alice,
            gauge_b,
            bob,
            10000,
            chain.time() + DAY * 31,  # cancel time
            chain.time() + DAY * 365,  # expire time
            {"from": alice},
        )
