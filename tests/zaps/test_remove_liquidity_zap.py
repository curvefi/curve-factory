import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


@pytest.fixture(autouse=True)
def setup(add_initial_liquidity, approve_zap, alice, bob, swap):
    swap.transfer(bob, swap.balanceOf(alice), {"from": alice})


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_lp_token_balances(bob, zap, swap, underlying_coins, divisor):
    initial_balance = swap.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(swap, withdraw_amount, min_amounts, {"from": bob})

    # bob is the only LP, total supply is affected in the same way as his balance
    assert swap.balanceOf(bob) == initial_balance - withdraw_amount
    assert swap.totalSupply() == initial_balance - withdraw_amount


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_wrapped_balances(
    bob,
    swap,
    zap,
    underlying_coins,
    coins,
    initial_amounts,
    divisor,
):
    initial_balance = swap.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(swap, withdraw_amount, min_amounts, {"from": bob})

    for coin, initial in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        assert abs(coin.balanceOf(swap) - (initial - (initial // divisor))) <= 1


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_underlying_balances(
    bob,
    swap,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    divisor,
):
    initial_balance = swap.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(swap, withdraw_amount, min_amounts, {"from": bob})

    for coin in underlying_coins[1:]:
        assert coin.balanceOf(zap) == 0
        assert coin.balanceOf(swap) == 0
        assert coin.balanceOf(bob) > 0


@pytest.mark.parametrize("idx", range(4))
def test_below_min_amount(alice, swap, zap, initial_amounts_underlying, idx):
    min_amount = initial_amounts_underlying.copy()
    min_amount[idx] += 1

    amount = 2000000 * 10 ** 18
    with brownie.reverts():
        zap.remove_liquidity(swap, amount, min_amount, {"from": alice})


def test_amount_exceeds_balance(alice, swap, zap, underlying_coins):
    amount = (2000000 * 10 ** 18) + 1
    with brownie.reverts():
        zap.remove_liquidity(swap, amount, [0, 0, 0, 0], {"from": alice})
