import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_bob_underlying", "approve_zap")


def test_lp_token_balances(bob, zap, swap, initial_amounts_underlying):
    zap.add_liquidity(swap, initial_amounts_underlying, 0, {"from": bob})

    assert 0.9999 < swap.balanceOf(bob) / (2000000 * 10 ** 18) <= 1
    assert swap.totalSupply() == swap.balanceOf(bob)


def test_underlying_balances(bob, zap, swap, underlying_coins, coins, initial_amounts_underlying):
    zap.add_liquidity(swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        assert coin.balanceOf(zap) == 0
        if coin in coins:
            assert coin.balanceOf(swap) == amount
        else:
            assert coin.balanceOf(swap) == 0


def test_wrapped_balances(bob, zap, swap, coins, initial_amounts_underlying, initial_amounts):
    zap.add_liquidity(swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        assert 0.9999 < coin.balanceOf(swap) / amount <= 1


@pytest.mark.parametrize("idx", range(4))
def test_initial_liquidity_missing_coin(alice, zap, swap, idx, underlying_decimals):
    amounts = [10 ** i for i in underlying_decimals]
    amounts[idx] = 0

    with brownie.reverts():
        zap.add_liquidity(swap, amounts, 0, {"from": alice})
