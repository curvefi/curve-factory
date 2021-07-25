import pytest
from brownie import ZERO_ADDRESS

SWAP_AMOUNT = 1e6


@pytest.fixture(autouse=True)
def setup(alice, factory, bob, swap, plain_coins, charlie, add_initial_liquidity):
    amounts = [0] * len(plain_coins)
    for idx, coin in enumerate(plain_coins[:2]):
        amount = 1e6 * 10 ** coin.decimals()
        amounts[idx] = amount
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})

    swap.add_liquidity(amounts, 0, {"from": alice})

    factory.set_fee_receiver(ZERO_ADDRESS, charlie)

    amount = SWAP_AMOUNT * 10 ** coin.decimals()
    plain_coins[0]._mint_for_testing(bob, amount, {"from": bob})
    plain_coins[0].approve(swap, amount, {"from": bob})
    swap.exchange(0, 1, amount, 0, {"from": bob})


def test_withdraw_admin_fees(bob, plain_coins, swap, charlie):
    fees = []
    for i, coin in enumerate(plain_coins[:2]):
        assert coin.balanceOf(charlie) == 0
        fees.append(swap.admin_balances(i))
    swap.withdraw_admin_fees({"from": bob})
    for i, coin in enumerate(plain_coins[:2]):
        assert coin.balanceOf(charlie) == fees[i]
