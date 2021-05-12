import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


def test_exchange_underlying(alice, charlie, swap, underlying_coins):
    underlying_coins[1]._mint_for_testing(alice, 10**18)

    swap.exchange_underlying(1, 0, 10**18, 0, charlie, {'from': alice})
    assert underlying_coins[0].balanceOf(charlie) > 0
    assert underlying_coins[0].balanceOf(alice) == 0
