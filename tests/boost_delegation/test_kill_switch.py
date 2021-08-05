import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

DAY = 86400


@pytest.mark.parametrize("delegated_gauge", [ZERO_ADDRESS, ETH_ADDRESS])
def test_delegation_adjustment(
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

    boost_delegation.set_killed(True, {"from": alice})

    brownie.multicall.deploy({"from": alice})

    with brownie.multicall(block_identifier=chain.height):
        alice_vecrv_balance = voting_escrow.balanceOf(alice)
        alice_adj_vecrv_bal = boost_delegation.get_adjusted_vecrv_balance(alice, delegated_gauge)
        assert alice_adj_vecrv_bal == alice_vecrv_balance
        assert boost_delegation.get_adjusted_vecrv_balance(bob, delegated_gauge) == 0
