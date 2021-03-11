import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob")


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_min_dy(bob, swap, wrapped_coins, sending, receiving, wrapped_decimals):

    amounts = [10 ** i for i in wrapped_decimals]
    scaler = amounts.copy()  # used to scale token amounts when decimals are different

    amounts[sending] = 0
    amounts[receiving] = amounts[receiving] * 10 ** 8

    for i, amount in enumerate(amounts):
        wrapped_coins[i]._mint_for_testing(bob, amount, {"from": bob})

    swap.add_liquidity(amounts, 0, {"from": bob})

    wrapped_coins[sending]._mint_for_testing(bob, scaler[sending], {"from": bob})

    # we need to scale these appropriately for tokens with different decimal values
    min_dy_sending = (
        swap.get_dy(sending, receiving, scaler[sending]) / scaler[receiving]
    )
    min_dy_receiving = (
        swap.get_dy(receiving, sending, scaler[receiving]) / scaler[sending]
    )

    assert min_dy_sending > min_dy_receiving
