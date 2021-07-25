import pytest
from brownie_tokens import ERC20


@pytest.fixture(scope="session")
def return_type(request):
    return request.param


@pytest.fixture(scope="session")
def _plain_coins(alice):
    return_true_revert = [ERC20(deployer=alice) for _ in range(4)]
    return_true_false = [ERC20(fail=False, deployer=alice) for _ in range(4)]
    return_none_revert = [ERC20(success=None) for _ in range(4)]
    return [return_true_revert, return_true_false, return_none_revert]


@pytest.fixture(scope="session")
def plain_coins(_plain_coins, plain_pool_size, return_type):
    return _plain_coins[return_type][:plain_pool_size]


@pytest.fixture(scope="session")
def decimals(plain_coins):
    return [coin.decimals() for coin in plain_coins]
