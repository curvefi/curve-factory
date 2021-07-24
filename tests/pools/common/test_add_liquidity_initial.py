import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("min_amount", [0, 10 ** 18])
def test_initial(alice, swap, plain_coins, min_amount, decimals, initial_amounts):
    amounts = [10 ** i for i in decimals]

    swap.add_liquidity(amounts, len(plain_coins) * min_amount, {"from": alice})

    for coin, amount, initial in zip(plain_coins, amounts, initial_amounts):
        assert coin.balanceOf(alice) == initial - amount
        assert coin.balanceOf(swap) == amount


@pytest.mark.parametrize("idx", range(2))
def test_initial_liquidity_missing_coin(alice, swap, idx, decimals):
    amounts = [10 ** i for i in decimals]
    amounts[idx] = 0
    with brownie.reverts():
        swap.add_liquidity(amounts, 0, {"from": alice})
