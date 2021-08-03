#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(autouse=True)
def setup(alice, add_initial_liquidity, gauge_controller, gauge, swap):

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(gauge, 0, 0, {"from": alice})

    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(10 ** 18, {"from": alice})


def test_sender_balance_decreases(alice, bob, charlie, gauge):
    sender_balance = gauge.balanceOf(alice)
    amount = sender_balance // 4

    gauge.approve(bob, amount, {"from": alice})
    gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert gauge.balanceOf(alice) == sender_balance - amount


def test_receiver_balance_increases(alice, bob, charlie, gauge):
    receiver_balance = gauge.balanceOf(charlie)
    amount = gauge.balanceOf(alice) // 4

    gauge.approve(bob, amount, {"from": alice})
    gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert gauge.balanceOf(charlie) == receiver_balance + amount


def test_caller_balance_not_affected(alice, bob, charlie, gauge):
    caller_balance = gauge.balanceOf(bob)
    amount = gauge.balanceOf(alice)

    gauge.approve(bob, amount, {"from": alice})
    gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert gauge.balanceOf(bob) == caller_balance


def test_caller_approval_affected(alice, bob, charlie, gauge):
    approval_amount = gauge.balanceOf(alice)
    transfer_amount = approval_amount // 4

    gauge.approve(bob, approval_amount, {"from": alice})
    gauge.transferFrom(alice, charlie, transfer_amount, {"from": bob})

    assert gauge.allowance(alice, bob) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(alice, bob, charlie, gauge):
    approval_amount = gauge.balanceOf(alice)
    transfer_amount = approval_amount // 4

    gauge.approve(bob, approval_amount, {"from": alice})
    gauge.approve(charlie, approval_amount, {"from": alice})
    gauge.transferFrom(alice, charlie, transfer_amount, {"from": bob})

    assert gauge.allowance(alice, charlie) == approval_amount


def test_total_supply_not_affected(alice, bob, charlie, gauge):
    total_supply = gauge.totalSupply()
    amount = gauge.balanceOf(alice)

    gauge.approve(bob, amount, {"from": alice})
    gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert gauge.totalSupply() == total_supply


def test_returns_true(alice, bob, charlie, gauge):
    amount = gauge.balanceOf(alice)
    gauge.approve(bob, amount, {"from": alice})
    tx = gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert tx.return_value is True


def test_transfer_full_balance(alice, bob, charlie, gauge):
    amount = gauge.balanceOf(alice)
    receiver_balance = gauge.balanceOf(charlie)

    gauge.approve(bob, amount, {"from": alice})
    gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert gauge.balanceOf(alice) == 0
    assert gauge.balanceOf(charlie) == receiver_balance + amount


def test_transfer_zero_tokens(alice, bob, charlie, gauge):
    sender_balance = gauge.balanceOf(alice)
    receiver_balance = gauge.balanceOf(charlie)

    gauge.approve(bob, sender_balance, {"from": alice})
    gauge.transferFrom(alice, charlie, 0, {"from": bob})

    assert gauge.balanceOf(alice) == sender_balance
    assert gauge.balanceOf(charlie) == receiver_balance


def test_transfer_zero_tokens_without_approval(alice, bob, charlie, gauge):
    sender_balance = gauge.balanceOf(alice)
    receiver_balance = gauge.balanceOf(charlie)

    gauge.transferFrom(alice, charlie, 0, {"from": bob})

    assert gauge.balanceOf(alice) == sender_balance
    assert gauge.balanceOf(charlie) == receiver_balance


def test_insufficient_balance(alice, bob, charlie, gauge):
    balance = gauge.balanceOf(alice)

    gauge.approve(bob, balance + 1, {"from": alice})
    with brownie.reverts():
        gauge.transferFrom(alice, charlie, balance + 1, {"from": bob})


def test_insufficient_approval(alice, bob, charlie, gauge):
    balance = gauge.balanceOf(alice)

    gauge.approve(bob, balance - 1, {"from": alice})
    with brownie.reverts():
        gauge.transferFrom(alice, charlie, balance, {"from": bob})


def test_no_approval(alice, bob, charlie, gauge):
    balance = gauge.balanceOf(alice)

    with brownie.reverts():
        gauge.transferFrom(alice, charlie, balance, {"from": bob})


def test_infinite_approval(alice, bob, charlie, gauge):
    gauge.approve(bob, 2 ** 256 - 1, {"from": alice})
    gauge.transferFrom(alice, charlie, 10000, {"from": bob})

    assert gauge.allowance(alice, bob) == 2 ** 256 - 1


def test_revoked_approval(alice, bob, charlie, gauge):
    balance = gauge.balanceOf(alice)

    gauge.approve(bob, balance, {"from": alice})
    gauge.approve(bob, 0, {"from": alice})

    with brownie.reverts():
        gauge.transferFrom(alice, charlie, balance, {"from": bob})


def test_transfer_to_self(alice, gauge):
    sender_balance = gauge.balanceOf(alice)
    amount = sender_balance // 4

    gauge.approve(alice, sender_balance, {"from": alice})
    gauge.transferFrom(alice, alice, amount, {"from": alice})

    assert gauge.balanceOf(alice) == sender_balance
    assert gauge.allowance(alice, alice) == sender_balance - amount


def test_transfer_to_self_no_approval(alice, gauge):
    amount = gauge.balanceOf(alice)

    with brownie.reverts():
        gauge.transferFrom(alice, alice, amount, {"from": alice})


def test_transfer_event_fires(alice, bob, charlie, gauge):
    amount = gauge.balanceOf(alice)

    gauge.approve(bob, amount, {"from": alice})
    tx = gauge.transferFrom(alice, charlie, amount, {"from": bob})

    assert tx.events["Transfer"].values() == [alice, charlie, amount]
