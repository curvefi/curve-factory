import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("min_amount", [0, 10 ** 18])
def test_initial(alice, swap, coins, min_amount, decimals, initial_amounts, eth_amount):
    amounts = [10 ** i for i in decimals]

    swap.add_liquidity(
        amounts,
        len(coins) * min_amount,
        {"from": alice, "value": eth_amount(amounts[0])},
    )

    for coin, amount, initial in zip(coins, amounts, initial_amounts):
        if coin == ETH_ADDRESS:
            assert alice.balance() == initial - amount
            assert swap.balance() == amount
            continue

        assert coin.balanceOf(alice) == initial - amount
        assert coin.balanceOf(swap) == amount


@pytest.mark.parametrize("idx", range(2))
def test_initial_liquidity_missing_coin(alice, swap, idx, decimals, eth_amount):
    amounts = [10 ** i for i in decimals]
    amounts[idx] = 0
    with brownie.reverts():
        swap.add_liquidity(amounts, 0, {"from": alice, "value": eth_amount(amounts[0])})
