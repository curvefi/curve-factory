import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


def test_twap_cumulative_price_is_initially_0(swap, coins):

    # this was the time since the last call to _updated
    # which after a deployemnt means this should be 0
    initial_time = swap.block_timestamp_last()

    # get the cumulative price of coins since contract was deployed
    # also should be 0 after a deployment
    twap_cumulative_price = swap.get_price_cumulative_last()

    # assert the last blocktime when _updated was called was 0
    assert initial_time == 0

    # for each coin
    for i, coin in enumerate(coins):
        # assert the cumulative price since deployment is 0
        # accurate since we just deployed and only called view functions
        assert twap_cumulative_price[i] == 0


def test_twap_cumulative_price_remains_0_after_providing_initial_liquidity(
    alice, swap, decimals, eth_amount
):

    # amount of 1 coin in the appropriate magnitude
    amounts = [10 ** i for i in decimals]

    # add liquidity of 1 coin
    swap.add_liquidity(amounts, 0, {"from": alice, "value": eth_amount(amounts[0])})

    # get the cumulative price since last
    # should be something like
    # 0 + (balance of coin prior to add_liqudity * elapsed time)
    # so [0, 0]
    twap = swap.get_price_cumulative_last()

    # for each coin we deposited
    for i, _ in enumerate(amounts):
        # assert the cumulative price is still 0
        # since we provided initial liqudity
        assert twap[i] == 0


def test_twap_cumulative_price_increases_with_subsequent_liquidity_provisions(
    alice, swap, chain, coins, decimals, eth_amount
):
    # initial liquidity amount to deposit
    deposit_amounts = [10 ** i for i in decimals]

    # deposit our initial liquidity
    # this won't affect the cumulative price of coins
    # but will set the block_timestamp_last since _update is called
    swap.add_liquidity(deposit_amounts, 0, {"from": alice, "value": eth_amount(deposit_amounts[0])})

    # the block timestamp when we added initial liquidity
    start = swap.block_timestamp_last()

    # let a second go by
    chain.sleep(1)

    # add liqudity again this will affect the cumulative price
    swap.add_liquidity(deposit_amounts, 0, {"from": alice, "value": eth_amount(deposit_amounts[0])})

    # get the updated values for cumulative price and block timestamp
    # since we added liquidity again we _update was called and
    # these should now have a value
    updated_cumulative_price = swap.get_price_cumulative_last()
    updated_block_timestamp = swap.block_timestamp_last()

    time_elapsed = updated_block_timestamp - start

    # for each value we deposited
    for i, amount in enumerate(deposit_amounts):
        # prior cumulative price +
        # (balance prior to last _update call * time elapsed between _update calls)
        assert updated_cumulative_price[i] == 0 + (amount * time_elapsed)

    # let a bunch of time elapse
    chain.sleep(1_000_000)

    # add some more liquidity
    swap.add_liquidity(deposit_amounts, 0, {"from": alice, "value": eth_amount(deposit_amounts[0])})

    # get our updated cumulative price
    # = prev_cumu_price + (amount prior to last _update call * time elapsed)
    old_cumu_price = updated_cumulative_price
    updated_cumulative_price = swap.get_price_cumulative_last()
    # get the new block time stamp
    old_block_timestamp = updated_block_timestamp
    updated_block_timestamp = swap.block_timestamp_last()
    # time that has elapsed
    time_elapsed = updated_block_timestamp - old_block_timestamp

    for i, coin in enumerate(coins):
        # amount deposited each time
        amount = deposit_amounts[i]
        # = prev_cumu_price + (amount prior to last _update call * time elapsed)
        # 2 because, inital liquidity provision + second call
        expected_cumu_price = old_cumu_price[i] + (amount * 2 * time_elapsed)
        assert updated_cumulative_price[i] == expected_cumu_price
