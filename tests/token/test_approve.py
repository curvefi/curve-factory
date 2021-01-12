#!/usr/bin/python3

import brownie
import pytest


pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(swap, alice, accounts, idx):
    assert swap.allowance(alice, accounts[idx]) == 0


def test_approve(swap, alice, bob):
    swap.approve(bob, 10**19, {'from': alice})

    assert swap.allowance(alice, bob) == 10**19


def test_modify_approve_zero_nonzero(swap, alice, bob):
    swap.approve(bob, 10**19, {'from': alice})
    swap.approve(bob, 0, {'from': alice})
    swap.approve(bob, 12345678, {'from': alice})

    assert swap.allowance(alice, bob) == 12345678


def test_revoke_approve(swap, alice, bob):
    swap.approve(bob, 10**19, {'from': alice})
    swap.approve(bob, 0, {'from': alice})

    assert swap.allowance(alice, bob) == 0


def test_approve_self(swap, alice, bob):
    swap.approve(alice, 10**19, {'from': alice})

    assert swap.allowance(alice, alice) == 10**19


def test_only_affects_target(swap, alice, bob):
    swap.approve(bob, 10**19, {'from': alice})

    assert swap.allowance(bob, alice) == 0


def test_returns_true(swap, alice, bob):
    tx = swap.approve(bob, 10**19, {'from': alice})

    assert tx.return_value is True


def test_approval_event_fires(alice, bob, swap):
    tx = swap.approve(bob, 10**19, {'from': alice})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [alice, bob, 10**19]


def test_infinite_approval(swap, alice, bob):
    swap.approve(bob, 2**256-1, {'from': alice})
    swap.transferFrom(alice, bob, 10**18, {'from': bob})

    assert swap.allowance(alice, bob) == 2**256-1
