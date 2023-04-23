import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("min_amount", [0, 10 ** 18])
def test_initial_liquidity_fail(alice, error_swap, coins, min_amount, decimals, initial_amounts, eth_amount):
    amounts = [10 ** i for i in decimals]

    with brownie.reverts() as e:
        error_swap.add_liquidity(
            amounts,
            len(coins) * min_amount,
            {"from": alice, "value": eth_amount(amounts[0])},
        )

        assert str(e) == 'VirtualMachineError'
