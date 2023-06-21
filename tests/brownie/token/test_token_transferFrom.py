#!/usr/bin/python3
import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


def test_sender_balance_decreases(alice, bob, charlie, swap):
    sender_balance = swap.balanceOf(alice)
    amount = sender_balance // 4

    swap.approve(bob, amount, {"from": alice})
    swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert swap.balanceOf(alice) == sender_balance - amount


def test_receiver_balance_increases(alice, bob, charlie, swap):
    receiver_balance = swap.balanceOf(charlie)
    amount = swap.balanceOf(alice) // 4

    swap.approve(bob, amount, {"from": alice})
    swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert swap.balanceOf(charlie) == receiver_balance + amount


def test_caller_balance_not_affected(alice, bob, charlie, swap):
    caller_balance = swap.balanceOf(bob)
    amount = swap.balanceOf(alice)

    swap.approve(bob, amount, {"from": alice})
    swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert swap.balanceOf(bob) == caller_balance


def test_caller_approval_affected(alice, bob, charlie, swap):
    approval_amount = swap.balanceOf(alice)
    transfer_amount = approval_amount // 4

    swap.approve(bob, approval_amount, {"from": alice})
    swap.transferFrom(alice, charlie, transfer_amount, {"from": bob})

    assert swap.allowance(alice, bob) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(alice, bob, charlie, swap):
    approval_amount = swap.balanceOf(alice)
    transfer_amount = approval_amount // 4

    swap.approve(bob, approval_amount, {"from": alice})
    swap.approve(charlie, approval_amount, {"from": alice})
    swap.transferFrom(alice, charlie, transfer_amount, {"from": bob})

    assert swap.allowance(alice, charlie) == approval_amount


def test_total_supply_not_affected(alice, bob, charlie, swap):
    total_supply = swap.totalSupply()
    amount = swap.balanceOf(alice)

    swap.approve(bob, amount, {"from": alice})
    swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert swap.totalSupply() == total_supply


def test_returns_true(alice, bob, charlie, swap):
    amount = swap.balanceOf(alice)
    swap.approve(bob, amount, {"from": alice})
    tx = swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert tx.return_value is True


def test_transfer_full_balance(alice, bob, charlie, swap):
    amount = swap.balanceOf(alice)
    receiver_balance = swap.balanceOf(charlie)

    swap.approve(bob, amount, {"from": alice})
    swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert swap.balanceOf(alice) == 0
    assert swap.balanceOf(charlie) == receiver_balance + amount


def test_transfer_zero_tokens(alice, bob, charlie, swap):
    sender_balance = swap.balanceOf(alice)
    receiver_balance = swap.balanceOf(charlie)

    swap.approve(bob, sender_balance, {"from": alice})
    swap.transferFrom(alice, charlie, 0, {"from": bob})

    assert swap.balanceOf(alice) == sender_balance
    assert swap.balanceOf(charlie) == receiver_balance


def test_transfer_zero_tokens_without_approval(alice, bob, charlie, swap):
    sender_balance = swap.balanceOf(alice)
    receiver_balance = swap.balanceOf(charlie)

    swap.transferFrom(alice, charlie, 0, {"from": bob})

    assert swap.balanceOf(alice) == sender_balance
    assert swap.balanceOf(charlie) == receiver_balance


def test_insufficient_balance(alice, bob, charlie, swap):
    balance = swap.balanceOf(alice)

    swap.approve(bob, balance + 1, {"from": alice})
    with brownie.reverts():
        swap.transferFrom(alice, charlie, balance + 1, {"from": bob})


def test_insufficient_approval(alice, bob, charlie, swap):
    balance = swap.balanceOf(alice)

    swap.approve(bob, balance - 1, {"from": alice})
    with brownie.reverts():
        swap.transferFrom(alice, charlie, balance, {"from": bob})


def test_no_approval(alice, bob, charlie, swap):
    balance = swap.balanceOf(alice)

    with brownie.reverts():
        swap.transferFrom(alice, charlie, balance, {"from": bob})


def test_revoked_approval(alice, bob, charlie, swap):
    balance = swap.balanceOf(alice)

    swap.approve(bob, balance, {"from": alice})
    swap.approve(bob, 0, {"from": alice})

    with brownie.reverts():
        swap.transferFrom(alice, charlie, balance, {"from": bob})


def test_transfer_to_self(alice, bob, swap):
    sender_balance = swap.balanceOf(alice)
    amount = sender_balance // 4

    swap.approve(alice, sender_balance, {"from": alice})
    swap.transferFrom(alice, alice, amount, {"from": alice})

    assert swap.balanceOf(alice) == sender_balance
    assert swap.allowance(alice, alice) == sender_balance - amount


def test_transfer_to_self_no_approval(alice, bob, swap):
    amount = swap.balanceOf(alice)

    with brownie.reverts():
        swap.transferFrom(alice, alice, amount, {"from": alice})


def test_transfer_event_fires(alice, bob, charlie, swap):
    amount = swap.balanceOf(alice)

    swap.approve(bob, amount, {"from": alice})
    tx = swap.transferFrom(alice, charlie, amount, {"from": bob})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [alice, charlie, amount]
