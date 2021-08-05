import math

import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

DAY = 86400


@pytest.fixture(autouse=True)
def fund_vecrv_accounts(alice, bob, charlie, chain, dave, crv, voting_escrow, lock_crv):
    alice_balance = crv.balanceOf(alice)
    for receiver in [bob, charlie]:
        crv.transfer(receiver, alice_balance // 2, {"from": alice})
        crv.approve(voting_escrow, 2 ** 256 - 1, {"from": receiver})
        voting_escrow.create_lock(
            alice_balance // 2, chain.time() + DAY * 365 * 4, {"from": receiver}
        )


@pytest.fixture(params=[ZERO_ADDRESS, ETH_ADDRESS])
def delegation_data(alice, bob, charlie, chain, dave, request):
    # [user, recipient, gauge, percentage, cancel_time, unlock_time]
    return [
        [charlie, request.param, dave, 1_000, chain.time() + DAY * 7, chain.time() + DAY * 31],
        [bob, request.param, dave, 5_000, chain.time() + DAY * 14, chain.time() + DAY * 180],
        [alice, request.param, dave, 10_000, chain.time() + DAY * 31, chain.time() + DAY * 365],
    ]


def test_receive_multiple_delegations(boost_delegation, voting_escrow, delegation_data, dave):
    adjusted_vecrv_balance = 0
    for data in delegation_data:
        boost_delegation.delegate_boost(*data, {"from": data[0]})
        adjusted_vecrv_balance += voting_escrow.balanceOf(data[0]) * data[3] // 10_000

    assert math.isclose(
        boost_delegation.get_adjusted_vecrv_balance(dave, delegation_data[0][1]),
        adjusted_vecrv_balance,
        rel_tol=0.001,
    )

    for idx, data in enumerate(delegation_data):
        # since we aren't removing it'll be ordered to same
        delegation_data = boost_delegation.get_delegation_data(data[2], data[1], idx)
        assert delegation_data == [data[0]] + data[3:]


@pytest.mark.parametrize("num_expired", [1, 2, 3])
def test_receive_multiple_delegations_expire(
    boost_delegation, chain, delegation_data, dave, num_expired, voting_escrow
):
    expiration_times = [DAY * i for i in [31, 180, 365]]

    for data in delegation_data:
        boost_delegation.delegate_boost(*data, {"from": data[0]})

    chain.mine(timedelta=expiration_times[num_expired - 1])

    adjusted_vecrv_balance = 0
    for idx, data in enumerate(delegation_data):
        multiplier = 0 if idx < num_expired else 1
        adjusted_vecrv_balance += multiplier * voting_escrow.balanceOf(data[0]) * data[3] // 10_000

    assert (
        boost_delegation.get_adjusted_vecrv_balance(dave, delegation_data[0][1])
        == adjusted_vecrv_balance
    )

    boost_delegation.update_delegation_records(dave, delegation_data[0][1], {"from": dave})

    for idx, data in enumerate(delegation_data[num_expired:][::-1]):
        on_chain_delegation_data = boost_delegation.get_delegation_data(data[2], data[1], idx)
        assert on_chain_delegation_data == [data[0]] + data[3:]
