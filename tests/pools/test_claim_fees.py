import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(charlie, base_lp_token, add_initial_liquidity, mint_bob, approve_bob):
    distributor = "0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc"
    base_lp_token.transfer(charlie, base_lp_token.balanceOf(distributor), {'from': distributor})


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(alice, bob, swap, wrapped_coins, initial_amounts, sending, receiving):
    for send, recv in [(sending, receiving), (receiving, sending)]:
        swap.exchange(send, recv, initial_amounts[send], 0, {'from': bob})

    for i in (sending, receiving):
        admin_fee = wrapped_coins[i].balanceOf(swap) - swap.balances(i)
        assert admin_fee + swap.balances(i) == wrapped_coins[i].balanceOf(swap)

        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice, bob, swap, wrapped_coins, sending, receiving, initial_amounts, base_lp_token
):
    assert base_lp_token.balanceOf("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc") == 0

    swap.exchange(sending, receiving, initial_amounts[sending], 0, {'from': bob})

    admin_balance = swap.admin_balances(receiving)

    assert admin_balance > 0
    assert swap.admin_balances(sending) == 0

    swap.withdraw_admin_fees({'from': alice})

    assert base_lp_token.balanceOf("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc") > 0
    assert swap.balances(receiving) == wrapped_coins[receiving].balanceOf(swap)


def test_no_fees(bob, swap, base_lp_token):
    swap.withdraw_admin_fees({'from': bob})

    assert base_lp_token.balanceOf("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc") == 0
