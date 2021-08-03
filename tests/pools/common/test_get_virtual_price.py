import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_bob", "mint_bob")


def test_number_go_up(bob, swap, initial_amounts, plain_pool_size, eth_amount):
    virtual_price = swap.get_virtual_price()

    for i, amount in enumerate(initial_amounts):
        amounts = [0] * plain_pool_size
        amounts[i] = amount
        swap.add_liquidity(amounts, 0, {"from": bob, "value": eth_amount(amounts[0])})

        new_virtual_price = swap.get_virtual_price()
        assert new_virtual_price > virtual_price
        virtual_price = new_virtual_price


@pytest.mark.parametrize("idx", range(2))
def test_remove_one_coin(alice, swap, idx):
    amount = swap.balanceOf(alice) // 10

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    assert swap.get_virtual_price() > virtual_price


@pytest.mark.parametrize("idx", range(2))
def test_remove_imbalance(alice, swap, idx, initial_amounts, plain_pool_size):
    amounts = [i // 2 for i in initial_amounts]
    amounts[idx] = 0

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_imbalance(
        amounts, plain_pool_size * 1_000_000 * 10 ** 18, {"from": alice}
    )

    assert swap.get_virtual_price() > virtual_price


def test_remove(alice, swap, plain_pool_size, initial_amounts):
    withdraw_amount = sum(initial_amounts) // 2

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity(withdraw_amount, [0] * plain_pool_size, {"from": alice})

    assert swap.get_virtual_price() >= virtual_price


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(bob, swap, sending, receiving, decimals, eth_amount):
    virtual_price = swap.get_virtual_price()

    amount = 10 ** decimals[sending]
    swap.exchange(
        sending,
        receiving,
        amount,
        0,
        {"from": bob, "value": eth_amount(amount) if sending == 0 else 0},
    )

    assert swap.get_virtual_price() > virtual_price
