
import itertools

from brownie import chain
from brownie_tokens import MintableForkToken

# BTC metapools function is near-identical to USD pools
# so we do not run the entire test suite against them


def test_btc_swaps(alice, bob, fee_receiver, swap_btc, factory, coin):
    # add liquidity
    wrapped_coins = [coin, MintableForkToken(swap_btc.coins(1))]
    underlying_coins = [coin] + [MintableForkToken(i) for i in factory.get_underlying_coins(swap_btc)[1:4]]

    amounts = [100 * 10**i.decimals() for i in wrapped_coins]
    for coin, amount in zip(wrapped_coins, amounts):
        coin._mint_for_testing(alice, amount)
        coin.approve(swap_btc, 2**256-1, {'from': alice})

    swap_btc.add_liquidity(amounts, 0, {'from': alice})
    chain.sleep(3600)

    # perform swaps between each coin
    for send, recv in itertools.permutations(range(2), 2):
        amount = 10**wrapped_coins[send].decimals()

        wrapped_coins[send]._mint_for_testing(bob, amount, {'from': bob})
        wrapped_coins[send].approve(swap_btc, amount, {'from': bob})

        swap_btc.exchange(send, recv, amount, 0, {'from': bob})
        chain.sleep(3600)

    # perform swaps between each underlying coin

    for send, recv in itertools.permutations(range(4), 2):
        amount = 10**underlying_coins[send].decimals()

        underlying_coins[send]._mint_for_testing(bob, amount, {'from': bob})
        underlying_coins[send].approve(swap_btc, amount, {'from': bob})

        swap_btc.exchange_underlying(send, recv, amount, 0, {'from': bob})
        chain.sleep(3600)

    # remove liquidity balanced
    swap_btc.remove_liquidity(10**18, [0, 0], {'from': alice})
    chain.sleep(3600)

    # remove liquidity imbalanced
    for idx in range(2):
        amounts = [10**wrapped_coins[i].decimals() for i in range(2)]
        amounts[idx] = 0
        swap_btc.remove_liquidity_imbalance(amounts, 2**256-1, {'from': alice})
        chain.sleep(3600)

    for idx in range(2):
        swap_btc.remove_liquidity_one_coin(10**wrapped_coins[idx].decimals(), idx, 0, {'from': alice})
        chain.sleep(3600)

    admin_fee = swap_btc.admin_balances(1)
    swap_btc.withdraw_admin_fees({'from': alice})

    for idx in range(2):
        assert swap_btc.admin_balances(idx) == 0

    assert wrapped_coins[1].balanceOf(fee_receiver) > admin_fee > 0


def test_zap_gas(DepositZapBTC, alice, bob, swap_btc, factory, coin):
    zap = DepositZapBTC.deploy({'from': alice})
    underlying_coins = [coin] + [MintableForkToken(i) for i in factory.get_underlying_coins(swap_btc)[1:4]]
    amounts = [100 * 10**i.decimals() for i in underlying_coins]
    for coin, amount in zip(underlying_coins, amounts):
        coin._mint_for_testing(alice, amount)
        coin.approve(zap, 2**256-1, {'from': alice})

    # add liquidity balanced
    zap.add_liquidity(swap_btc, [i//2 for i in amounts], 0, {'from': alice})
    chain.sleep(3600)

    # add liquidity imbalanced
    for idx in range(4):
        amounts = [10**i.decimals() for i in underlying_coins]
        amounts[idx] = 0
        zap.add_liquidity(swap_btc, amounts, 0, {'from': alice})
        chain.sleep(3600)

    # remove liquidity balanced
    swap_btc.approve(zap, 2**256-1, {'from': alice})
    zap.remove_liquidity(swap_btc, 10**18, [0, 0, 0, 0], {'from': alice})
    chain.sleep(3600)

    amounts = [10**i.decimals() for i in underlying_coins]
    zap.remove_liquidity_imbalance(swap_btc, amounts, swap_btc.balanceOf(alice), {'from': alice})
    chain.sleep(3600)

    # remove liquidity imbalanced
    for idx in range(4):
        amounts = [10**i.decimals() for i in underlying_coins]
        amounts[idx] = 0
        zap.remove_liquidity_imbalance(swap_btc, amounts, swap_btc.balanceOf(alice), {'from': alice})
        chain.sleep(3600)

    for idx in range(4):
        zap.remove_liquidity_one_coin(swap_btc, 10**underlying_coins[idx].decimals(), idx, 0, {'from': alice})
        chain.sleep(3600)
