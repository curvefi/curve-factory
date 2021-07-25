import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS, accounts

SWAP_AMOUNT = 1e6


@pytest.fixture(autouse=True)
def setup(alice, factory, bob, swap, coins, charlie, add_initial_liquidity, eth_amount, decimals):
    amounts = [0] * len(coins)
    for idx, coin in enumerate(coins[:2]):
        amount = 1e6 * 10 ** decimals[idx]
        if coin == ETH_ADDRESS:
            accounts[-1].transfer(alice, amount)
            continue
        amounts[idx] = amount
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap, 2 ** 256 - 1, {"from": alice})

    swap.add_liquidity(amounts, 0, {"from": alice, "value": eth_amount(amounts[0])})

    factory.set_fee_receiver(ZERO_ADDRESS, charlie)

    amount = SWAP_AMOUNT * 10 ** 18

    if coins[0] == ETH_ADDRESS:
        accounts[-1].transfer(bob, amount)
    else:
        coins[0]._mint_for_testing(bob, amount, {"from": bob})
        coins[0].approve(swap, amount, {"from": bob})
    swap.exchange(0, 1, amount, 0, {"from": bob, "value": eth_amount(amount)})


def test_withdraw_admin_fees(bob, coins, swap, charlie):
    fees = []
    for i, coin in enumerate(coins[:2]):
        if coin == ETH_ADDRESS:
            assert charlie.balance() == 0
        else:
            assert coin.balanceOf(charlie) == 0
        fees.append(swap.admin_balances(i))

    swap.withdraw_admin_fees({"from": bob})
    for i, coin in enumerate(coins[:2]):
        if coin == ETH_ADDRESS:
            assert charlie.balance() == fees[i]
            continue

        assert coin.balanceOf(charlie) == fees[i]
