import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

pytestmark = pytest.mark.usefixtures("lock_crv")

DAY = 86400


@pytest.fixture
def alice_vecrv_balance(alice, voting_escrow, lock_crv):
    return voting_escrow.balanceOf(alice)


@pytest.fixture
def lock_bob(alice, bob, crv, voting_escrow, chain):
    lock_amt = crv.balanceOf(alice) // 2
    crv.transfer(bob, lock_amt, {"from": alice})
    crv.approve(voting_escrow, lock_amt, {"from": bob})
    voting_escrow.create_lock(lock_amt, chain.time() + DAY * 365 * 4, {"from": bob})


@pytest.fixture(autouse=True)
def delegate_bob(alice, bob, boost_delegation, chain, alice_vecrv_balance):
    boost_delegation.delegate_boost(
        alice,
        ETH_ADDRESS,
        bob,
        10000,
        chain.time() + DAY * 31,
        chain.time() + DAY * 365,
        {"from": alice},
    )


def test_delegation_count(alice, boost_delegation):
    assert boost_delegation.delegation_count(alice) == 1


def test_operator_delegates(alice, bob, boost_delegation, chain, lock_bob):
    boost_delegation.set_operator(alice, {"from": bob})

    boost_delegation.delegate_boost(
        bob,
        ETH_ADDRESS,
        alice,
        10000,
        chain.time() + DAY * 31,
        chain.time() + DAY * 365,
        {"from": alice},
    )

    assert boost_delegation.delegation_count(bob) == 1


def test_delegation_data(alice, history, bob, boost_delegation):
    data = boost_delegation.get_delegation_data(bob, ETH_ADDRESS, 0)
    delegation_tx_time = history[-1].timestamp
    expected = (alice, 10_000, delegation_tx_time + DAY * 31, delegation_tx_time + DAY * 365)
    assert data[:2] == expected[:2]
    assert abs(data[2] - expected[2]) <= 1
    assert abs(data[3] - expected[3]) <= 1


def test_delegation_to_data(alice, history, bob, boost_delegation):
    data = boost_delegation.get_delegated_to(alice, ETH_ADDRESS)
    delegation_tx_time = history[-1].timestamp
    expected = (bob, 10_000, delegation_tx_time + DAY * 31, delegation_tx_time + DAY * 365)
    assert data[:2] == expected[:2]
    assert abs(data[2] - expected[2]) <= 1
    assert abs(data[3] - expected[3]) <= 1


def test_event_emitted(alice, bob, history):
    tx = history[-1]
    expected = dict(
        delegator=alice.address,
        gauge=ETH_ADDRESS,
        receiver=bob.address,
        pct=10_000,
        cancel_time=tx.timestamp + DAY * 31,
        expire_time=tx.timestamp + DAY * 365,
    )

    assert "NewDelegation" in tx.events
    assert dict(tx.events["NewDelegation"]) == expected


def test_killed_guard(alice, bob, boost_delegation, chain, lock_bob):
    boost_delegation.set_killed(True, {"from": alice})

    with brownie.reverts("Is killed"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 10_000, chain.time() + 1, chain.time() + DAY, {"from": bob}
        )


def test_call_guard_operator(alice, bob, boost_delegation, chain):
    with brownie.reverts("Only owner or operator"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 10_000, chain.time() + 1, chain.time() + DAY, {"from": alice}
        )


def test_call_guard_self(bob, boost_delegation, chain):
    with brownie.reverts("Cannot delegate to self"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, bob, 10_000, chain.time() + 1, chain.time() + DAY, {"from": bob}
        )


def test_pct_minimum_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Percent too low"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 99, chain.time() + 1, chain.time() + DAY, {"from": bob}
        )


def test_pct_maximum_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Percent too high"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 10_001, chain.time() + 1, chain.time() + DAY, {"from": bob}
        )


def test_expire_time_max_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Expiry time too high"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 10_000, chain.time() + 1, 2 ** 40 + 1, {"from": bob}
        )


def test_expire_time_min_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Already expired"):
        boost_delegation.delegate_boost(
            bob, ETH_ADDRESS, alice, 10_000, chain.time() + 1, chain.time() - 1, {"from": bob}
        )


def test_cancel_time_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Cancel time after expiry time"):
        boost_delegation.delegate_boost(
            bob,
            ETH_ADDRESS,
            alice,
            10_000,
            chain.time() + DAY * 31,
            chain.time() + DAY * 30,
            {"from": bob},
        )


def test_insufficient_vecrv_balance(bob, charlie, boost_delegation, chain):
    with brownie.reverts("Insufficient veCRV to delegate"):
        boost_delegation.delegate_boost(
            charlie,
            ETH_ADDRESS,
            bob,
            10_000,
            chain.time() + DAY * 31,
            chain.time() + DAY * 365,
            {"from": charlie},
        )


def test_existing_delegation_non_expired(alice, bob, boost_delegation, chain):
    with brownie.reverts("Existing delegation has not expired"):
        boost_delegation.delegate_boost(
            alice,
            ETH_ADDRESS,
            bob,
            10_000,
            chain.time() + DAY * 31,
            chain.time() + DAY * 365,
            {"from": alice},
        )


def test_delegating_global_while_per_pool_active_guard(alice, bob, boost_delegation, chain):
    with brownie.reverts("Cannot delegate globally while per-gauge is active"):
        boost_delegation.delegate_boost(
            alice,
            ZERO_ADDRESS,
            bob,
            10_000,
            chain.time() + DAY * 31,
            chain.time() + DAY * 365,
            {"from": alice},
        )


def test_delegating_per_gauge_while_global_active_guard(
    alice, bob, boost_delegation, chain, lock_bob
):
    boost_delegation.delegate_boost(
        bob,
        ZERO_ADDRESS,
        alice,
        10_000,
        chain.time() + DAY * 31,
        chain.time() + DAY * 365,
        {"from": bob},
    )
    with brownie.reverts("Cannot delegate per-gauge while global is active"):
        boost_delegation.delegate_boost(
            bob,
            ETH_ADDRESS,
            alice,
            10_000,
            chain.time() + DAY * 31,
            chain.time() + DAY * 365,
            {"from": bob},
        )
