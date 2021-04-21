import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("min_amount", [0, 2 * 10**18])
def test_initial(
    alice, swap, wrapped_coins, min_amount, wrapped_decimals, initial_amounts, base_pool
):
    amounts = [10**i for i in wrapped_decimals]

    swap.add_liquidity(amounts, min_amount, {'from': alice})

    for coin, amount, initial in zip(wrapped_coins, amounts, initial_amounts):
        assert coin.balanceOf(alice) == initial - amount
        assert coin.balanceOf(swap) == amount

    ideal = 10**18 + base_pool.get_virtual_price()
    assert 0.9999 < swap.balanceOf(alice) / ideal < 1
    assert swap.balanceOf(alice) == swap.totalSupply()


@pytest.mark.parametrize("idx", range(2))
def test_initial_liquidity_missing_coin(alice, swap, rebase_coin, idx, wrapped_decimals):
    amounts = [10**i for i in wrapped_decimals]
    amounts[idx] = 0
    with brownie.reverts():
        swap.add_liquidity(amounts, 0, {'from': alice})
