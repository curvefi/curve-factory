#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, gauge, token, swap):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(gauge, 0, 0, {"from": accounts[0]})

    swap.approve(gauge, 2 ** 256 - 1, {"from": accounts[0]})
    gauge.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, gauge):
    sender_balance = gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, gauge):
    receiver_balance = gauge.balanceOf(accounts[1])
    amount = gauge.balanceOf(accounts[0]) // 4

    gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, gauge):
    total_supply = gauge.totalSupply()
    amount = gauge.balanceOf(accounts[0])

    gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge.totalSupply() == total_supply


def test_returns_true(accounts, gauge):
    amount = gauge.balanceOf(accounts[0])
    tx = gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, gauge):
    amount = gauge.balanceOf(accounts[0])
    receiver_balance = gauge.balanceOf(accounts[1])

    gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge.balanceOf(accounts[0]) == 0
    assert gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, gauge):
    sender_balance = gauge.balanceOf(accounts[0])
    receiver_balance = gauge.balanceOf(accounts[1])

    gauge.transfer(accounts[1], 0, {"from": accounts[0]})

    assert gauge.balanceOf(accounts[0]) == sender_balance
    assert gauge.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, gauge):
    sender_balance = gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge.transfer(accounts[0], amount, {"from": accounts[0]})

    assert gauge.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, gauge):
    balance = gauge.balanceOf(accounts[0])

    with brownie.reverts():
        gauge.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, gauge):
    amount = gauge.balanceOf(accounts[0])
    tx = gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
