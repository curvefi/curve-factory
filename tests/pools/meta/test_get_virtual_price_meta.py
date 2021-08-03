import itertools

import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "approve_bob_underlying", "mint_bob_underlying"
)


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(4), 2))
def test_exchange_underlying(bob, swap, sending, receiving, underlying_decimals):  # noqa
    virtual_price = swap.get_virtual_price()

    amount = 10 ** underlying_decimals[sending]
    swap.exchange_underlying(sending, receiving, amount, 0, {"from": bob})

    assert swap.get_virtual_price() > virtual_price
