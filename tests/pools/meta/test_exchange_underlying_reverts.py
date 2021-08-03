import itertools

import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "approve_bob_underlying", "mint_bob_underlying"
)


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(4), 2))
def test_min_dy_too_high(bob, swap, underlying_coins, underlying_decimals, sending, receiving):
    amount = 10 ** underlying_decimals[sending]

    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    min_dy = swap.get_dy_underlying(sending, receiving, amount * 1.0001)
    with brownie.reverts():
        swap.exchange_underlying(sending, receiving, amount, min_dy, {"from": bob})


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(4), 2))
def test_insufficient_balance(
    bob, swap, underlying_coins, underlying_decimals, sending, receiving
):  # noqa
    amount = 10 ** underlying_decimals[sending]

    if (balance := underlying_coins[sending].balanceOf(bob)) > 0:
        underlying_coins[sending].transfer(ETH_ADDRESS, balance, {"from": bob})

    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})
    with brownie.reverts():
        swap.exchange_underlying(sending, receiving, amount + 1, 0, {"from": bob})


@pytest.mark.parametrize("idx", range(4))
def test_same_coin(bob, swap, idx):
    with brownie.reverts():
        swap.exchange_underlying(idx, idx, 0, 0, {"from": bob})


@pytest.mark.parametrize("idx", [-1, -(2 ** 127)])
def test_i_below_zero(bob, swap, idx):
    with brownie.reverts():
        swap.exchange_underlying(idx, 0, 0, 0, {"from": bob})


@pytest.mark.parametrize("idx", [4, 2 ** 127 - 1])
def test_i_above_n_coins(bob, swap, idx):
    with brownie.reverts():
        swap.exchange_underlying(idx, 0, 0, 0, {"from": bob})


@pytest.mark.parametrize("idx", [-1, -(2 ** 127)])
def test_j_below_zero(bob, swap, idx):
    with brownie.reverts():
        swap.exchange_underlying(0, idx, 0, 0, {"from": bob})


@pytest.mark.parametrize("idx", [4, 2 ** 127 - 1])
def test_j_above_n_coins(bob, swap, idx):
    with brownie.reverts():
        swap.exchange_underlying(0, idx, 0, 0, {"from": bob})
