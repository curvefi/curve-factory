#!/usr/bin/python3
import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


def test_sender_balance_decreases(alice, bob, swap):
    sender_balance = swap.balanceOf(alice)
    amount = sender_balance // 4

    swap.transfer(bob, amount, {"from": alice})

    assert swap.balanceOf(alice) == sender_balance - amount


def test_receiver_balance_increases(alice, bob, swap):
    receiver_balance = swap.balanceOf(bob)
    amount = swap.balanceOf(alice) // 4

    swap.transfer(bob, amount, {"from": alice})

    assert swap.balanceOf(bob) == receiver_balance + amount


def test_total_supply_not_affected(alice, bob, swap):
    total_supply = swap.totalSupply()
    amount = swap.balanceOf(alice)

    swap.transfer(bob, amount, {"from": alice})

    assert swap.totalSupply() == total_supply


def test_returns_true(alice, bob, swap):
    amount = swap.balanceOf(alice)
    tx = swap.transfer(bob, amount, {"from": alice})

    assert tx.return_value is True


def test_transfer_full_balance(alice, bob, swap):
    amount = swap.balanceOf(alice)
    receiver_balance = swap.balanceOf(bob)

    swap.transfer(bob, amount, {"from": alice})

    assert swap.balanceOf(alice) == 0
    assert swap.balanceOf(bob) == receiver_balance + amount


def test_transfer_zero_tokens(alice, bob, swap):
    sender_balance = swap.balanceOf(alice)
    receiver_balance = swap.balanceOf(bob)

    swap.transfer(bob, 0, {"from": alice})

    assert swap.balanceOf(alice) == sender_balance
    assert swap.balanceOf(bob) == receiver_balance


def test_transfer_to_self(alice, bob, swap):
    sender_balance = swap.balanceOf(alice)
    amount = sender_balance // 4

    swap.transfer(alice, amount, {"from": alice})

    assert swap.balanceOf(alice) == sender_balance


def test_insufficient_balance(alice, bob, swap):
    balance = swap.balanceOf(alice)

    with brownie.reverts():
        swap.transfer(bob, balance + 1, {"from": alice})


def test_transfer_event_fires(alice, bob, swap):
    amount = swap.balanceOf(alice)
    tx = swap.transfer(bob, amount, {"from": alice})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [alice, bob, amount]
