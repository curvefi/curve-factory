from brownie import ZERO_ADDRESS


def test_set_operator_to_someone_else(alice, bob, boost_delegation):
    boost_delegation.set_operator(bob, {"from": alice})

    assert boost_delegation.operator_of(alice) == bob


def test_unset_operator(alice, bob, boost_delegation):
    boost_delegation.set_operator(bob, {"from": alice})
    boost_delegation.set_operator(ZERO_ADDRESS, {"from": alice})

    assert boost_delegation.operator_of(alice) == ZERO_ADDRESS
