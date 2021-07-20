import itertools

import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob", "mint_bob")


def test_number_go_up(bob, swap, initial_amounts, wrapped_coins):
    virtual_price = swap.get_virtual_price()

    for i, amount in enumerate(initial_amounts):
        amounts = [0, 0]
        amounts[i] = amount
        swap.add_liquidity(amounts, 0, {"from": bob})

        new_virtual_price = swap.get_virtual_price()
        assert new_virtual_price > virtual_price
        virtual_price = new_virtual_price


@pytest.mark.parametrize("idx", range(2))
def test_remove_one_coin(alice, swap, idx):
    amount = swap.balanceOf(alice) // 10

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    assert swap.get_virtual_price() > virtual_price


@pytest.mark.parametrize("idx", range(2))
def test_remove_imbalance(alice, swap, wrapped_coins, idx, initial_amounts):
    amounts = [i // 2 for i in initial_amounts]
    amounts[idx] = 0

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_imbalance(amounts, 2000000 * 10 ** 18, {"from": alice})

    assert swap.get_virtual_price() > virtual_price


def test_remove(alice, swap, wrapped_coins, initial_amounts):
    withdraw_amount = sum(initial_amounts) // 2

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity(withdraw_amount, [0, 0], {"from": alice})

    assert swap.get_virtual_price() >= virtual_price


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(bob, swap, sending, receiving, wrapped_coins, wrapped_decimals):
    virtual_price = swap.get_virtual_price()

    amount = 10 ** wrapped_decimals[sending]
    swap.exchange(sending, receiving, amount, 0, {"from": bob})

    assert swap.get_virtual_price() > virtual_price


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(4), 2))
def test_exchange_underlying(bob, swap, sending, receiving, underlying_coins, underlying_decimals):
    virtual_price = swap.get_virtual_price()

    amount = 10 ** underlying_decimals[sending]
    swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})

    assert swap.get_virtual_price() > virtual_price
