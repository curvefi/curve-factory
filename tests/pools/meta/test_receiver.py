import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_alice_underlying")


def test_exchange_underlying(alice, charlie, swap, underlying_coins, underlying_decimals):
    amount = 10 ** underlying_decimals[1]
    underlying_coins[1]._mint_for_testing(alice, amount)

    swap.exchange_underlying(1, 0, amount, 0, charlie, {"from": alice})
    assert underlying_coins[0].balanceOf(charlie) > 0
    assert underlying_coins[0].balanceOf(alice) == 0
