import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, gauge, swap):
    swap.approve(gauge, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, gauge, swap):
    balance = swap.balanceOf(accounts[0])
    gauge.deposit(100000, {"from": accounts[0]})

    assert swap.balanceOf(gauge) == 100000
    assert swap.balanceOf(accounts[0]) == balance - 100000
    assert gauge.totalSupply() == 100000
    assert gauge.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, gauge, swap):
    balance = swap.balanceOf(accounts[0])
    gauge.deposit(0, {"from": accounts[0]})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(accounts[0]) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, gauge, swap):
    with brownie.reverts():
        gauge.deposit(100000, {"from": accounts[1]})


def test_withdraw(accounts, gauge, swap):
    balance = swap.balanceOf(accounts[0])

    gauge.deposit(100000, {"from": accounts[0]})
    gauge.withdraw(100000, {"from": accounts[0]})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(accounts[0]) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, gauge, swap):
    balance = swap.balanceOf(accounts[0])
    gauge.deposit(100000, {"from": accounts[0]})
    gauge.withdraw(0, {"from": accounts[0]})

    assert swap.balanceOf(gauge) == 100000
    assert swap.balanceOf(accounts[0]) == balance - 100000
    assert gauge.totalSupply() == 100000
    assert gauge.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(accounts, chain, gauge, swap):
    balance = swap.balanceOf(accounts[0])

    gauge.deposit(100000, {"from": accounts[0]})
    chain.sleep(86400 * 400)
    gauge.withdraw(100000, {"from": accounts[0]})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(accounts[0]) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(accounts[0]) == 0
