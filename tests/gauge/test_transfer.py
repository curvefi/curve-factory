#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(autouse=True)
def setup(add_initial_liquidity, alice, gauge_controller, minter, gauge, swap):

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(gauge, 0, 0, {"from": alice})

    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})
    gauge.deposit(10 ** 18, {"from": alice})


def test_sender_balance_decreases(alice, bob, gauge):
    sender_balance = gauge.balanceOf(alice)
    amount = sender_balance // 4

    gauge.transfer(bob, amount, {"from": alice})

    assert gauge.balanceOf(alice) == sender_balance - amount


def test_receiver_balance_increases(alice, bob, gauge):
    receiver_balance = gauge.balanceOf(bob)
    amount = gauge.balanceOf(alice) // 4

    gauge.transfer(bob, amount, {"from": alice})

    assert gauge.balanceOf(bob) == receiver_balance + amount


def test_total_supply_not_affected(alice, bob, gauge):
    total_supply = gauge.totalSupply()
    amount = gauge.balanceOf(alice)

    gauge.transfer(bob, amount, {"from": alice})

    assert gauge.totalSupply() == total_supply


def test_returns_true(alice, bob, gauge):
    amount = gauge.balanceOf(alice)
    tx = gauge.transfer(bob, amount, {"from": alice})

    assert tx.return_value is True


def test_transfer_full_balance(alice, bob, gauge):
    amount = gauge.balanceOf(alice)
    receiver_balance = gauge.balanceOf(bob)

    gauge.transfer(bob, amount, {"from": alice})

    assert gauge.balanceOf(alice) == 0
    assert gauge.balanceOf(bob) == receiver_balance + amount


def test_transfer_zero_tokens(alice, bob, gauge):
    sender_balance = gauge.balanceOf(alice)
    receiver_balance = gauge.balanceOf(bob)

    gauge.transfer(bob, 0, {"from": alice})

    assert gauge.balanceOf(alice) == sender_balance
    assert gauge.balanceOf(bob) == receiver_balance


def test_transfer_to_self(alice, gauge):
    sender_balance = gauge.balanceOf(alice)
    amount = sender_balance // 4

    gauge.transfer(alice, amount, {"from": alice})

    assert gauge.balanceOf(alice) == sender_balance


def test_insufficient_balance(alice, bob, gauge):
    balance = gauge.balanceOf(alice)

    with brownie.reverts():
        gauge.transfer(bob, balance + 1, {"from": alice})


def test_transfer_event_fires(alice, bob, gauge):
    amount = gauge.balanceOf(alice)
    tx = gauge.transfer(bob, amount, {"from": alice})

    assert tx.events["Transfer"].values() == [alice, bob, amount]
