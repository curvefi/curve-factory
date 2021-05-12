import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("idx", range(2))
def test_initial_liquidity_missing_coin(alice, swap, rebase_coin, idx, wrapped_decimals):
    amounts = [10**i for i in wrapped_decimals]
    amounts[idx] = 0
    with brownie.reverts():
        swap.add_liquidity(amounts, 0, {'from': alice})
