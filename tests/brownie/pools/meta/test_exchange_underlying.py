import itertools

import pytest
from pytest import approx

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob_underlying")


@pytest.mark.parametrize(
    "sending,receiving", filter(lambda k: 0 in k, itertools.permutations(range(4), 2))
)
def test_amounts(
    bob,
    swap,
    underlying_coins,
    sending,
    receiving,
    underlying_decimals,
):
    amount = 10 ** underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})
    swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})

    assert underlying_coins[sending].balanceOf(bob) == 0

    received = underlying_coins[receiving].balanceOf(bob)
    assert 0.999 <= received / 10 ** underlying_decimals[receiving] < 1


@pytest.mark.parametrize(
    "sending,receiving", filter(lambda k: 0 in k, itertools.permutations(range(4), 2))
)
def test_fees(
    bob,
    swap,
    underlying_coins,
    sending,
    receiving,
    underlying_decimals,
    decimals,
    base_pool,
):
    amount = 10000 * 10 ** underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})
    swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})

    admin_idx = min(1, receiving)
    admin_fee = swap.admin_balances(admin_idx)

    expected = 2 * 10 ** decimals[admin_idx]
    if admin_idx == 1:
        expected = expected * 10 ** 18 // base_pool.get_virtual_price()
    assert expected / admin_fee == approx(1, rel=1e-3)


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(4), 2))
def test_min_dy_underlying(bob, swap, underlying_coins, sending, receiving, underlying_decimals):
    amount = 10 ** underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {"from": bob})

    expected = swap.get_dy_underlying(sending, receiving, amount)
    tx = swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})
    received = tx.events["TokenExchangeUnderlying"]["tokens_bought"]

    assert abs(expected - received) / received < 0.00001
