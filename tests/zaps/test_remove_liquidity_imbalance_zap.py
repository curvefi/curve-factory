import pytest


@pytest.fixture(autouse=True)
def setup(alice, bob, swap, add_initial_liquidity, approve_zap):
    swap.transfer(bob, swap.balanceOf(alice), {"from": alice})


@pytest.mark.parametrize("divisor", [2, 7, 31337])
def test_lp_token_balances(bob, zap, swap, divisor, initial_amounts_underlying):
    amounts = [i // divisor for i in initial_amounts_underlying]
    max_burn = int(((2000000 * 10 ** 18) // divisor) * 1.1)

    initial_balance = swap.balanceOf(bob)
    zap.remove_liquidity_imbalance(swap, amounts, max_burn, {"from": bob})

    # bob is the only LP, total supply is affected in the same way as his balance
    assert swap.balanceOf(bob) < initial_balance
    assert swap.balanceOf(bob) >= initial_balance - max_burn

    assert swap.balanceOf(zap) == 0
    assert swap.balanceOf(bob) == swap.totalSupply()


@pytest.mark.parametrize("divisor", [2, 7, 31337])
def test_wrapped_balances(
    bob,
    swap,
    zap,
    underlying_coins,
    coins,
    initial_amounts,
    initial_amounts_underlying,
    divisor,
):
    amounts = [i // divisor for i in initial_amounts_underlying]
    zap.remove_liquidity_imbalance(swap, amounts, swap.balanceOf(bob), {"from": bob})

    for coin, initial in zip(coins[1:], initial_amounts[1:]):
        assert coin.balanceOf(zap) == 0
        assert coin.balanceOf(bob) == 0


@pytest.mark.parametrize("divisor", [2, 7, 31337])
@pytest.mark.parametrize("is_inclusive", [True, False])
@pytest.mark.parametrize("idx", range(4))
def test_underlying_balances(
    bob,
    swap,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    divisor,
    idx,
    is_inclusive,
):
    if is_inclusive:
        amounts = [i // divisor for i in initial_amounts_underlying]
        amounts[idx] = 0
    else:
        amounts = [0] * len(initial_amounts_underlying)
        amounts[idx] = initial_amounts_underlying[idx] // divisor
    zap.remove_liquidity_imbalance(swap, amounts, swap.balanceOf(bob), {"from": bob})

    for coin, amount, initial in zip(underlying_coins, amounts, initial_amounts_underlying):
        if coin not in coins:
            assert coin.balanceOf(swap) == 0
        else:
            assert coin.balanceOf(swap) == initial - amount
        assert coin.balanceOf(zap) == 0

        if amount:
            assert 0.9 < coin.balanceOf(bob) / amount <= 1
        else:
            assert coin.balanceOf(bob) == 0
