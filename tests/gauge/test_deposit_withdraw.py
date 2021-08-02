import brownie
import pytest


@pytest.fixture(autouse=True)
def deposit_setup(alice, add_initial_liquidity, gauge, swap):
    swap.approve(gauge, 2 ** 256 - 1, {"from": alice})


def test_deposit(alice, gauge, swap):
    balance = swap.balanceOf(alice)
    gauge.deposit(100000, {"from": alice})

    assert swap.balanceOf(gauge) == 100000
    assert swap.balanceOf(alice) == balance - 100000
    assert gauge.totalSupply() == 100000
    assert gauge.balanceOf(alice) == 100000


def test_deposit_zero(alice, gauge, swap):
    balance = swap.balanceOf(alice)
    gauge.deposit(0, {"from": alice})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(alice) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(alice) == 0


def test_deposit_insufficient_balance(bob, gauge):
    with brownie.reverts():
        gauge.deposit(100000, {"from": bob})


def test_withdraw(alice, gauge, swap):
    balance = swap.balanceOf(alice)

    gauge.deposit(100000, {"from": alice})
    gauge.withdraw(100000, {"from": alice})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(alice) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(alice) == 0


def test_withdraw_zero(alice, gauge, swap):
    balance = swap.balanceOf(alice)
    gauge.deposit(100000, {"from": alice})
    gauge.withdraw(0, {"from": alice})

    assert swap.balanceOf(gauge) == 100000
    assert swap.balanceOf(alice) == balance - 100000
    assert gauge.totalSupply() == 100000
    assert gauge.balanceOf(alice) == 100000


def test_withdraw_new_epoch(alice, chain, gauge, swap):
    balance = swap.balanceOf(alice)

    gauge.deposit(100000, {"from": alice})
    chain.sleep(86400 * 400)
    gauge.withdraw(100000, {"from": alice})

    assert swap.balanceOf(gauge) == 0
    assert swap.balanceOf(alice) == balance
    assert gauge.totalSupply() == 0
    assert gauge.balanceOf(alice) == 0
