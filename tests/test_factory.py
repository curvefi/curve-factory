import brownie
import itertools
import pytest

from brownie import ZERO_ADDRESS
from brownie_tokens import ERC20


@pytest.fixture(scope="module", autouse=True)
def setup(swap, bob, add_initial_liquidity, mint_bob, approve_bob, coin):
    amount = 10**coin.decimals()
    swap.exchange(0, 1, amount, 0, {'from': bob})
    swap.exchange(1, 0, 10**18, 0, {'from': bob})


@pytest.mark.parametrize('sending,receiving', [(0, 1), (1, 0)])
def test_find_pool_for_coins(factory, swap, wrapped_coins, sending, receiving):
    assert factory.find_pool_for_coins(wrapped_coins[sending], wrapped_coins[receiving]) == swap


@pytest.mark.parametrize('idx', range(1, 4))
def test_find_pool_for_coins_underlying(factory, swap, underlying_coins, idx):
    assert factory.find_pool_for_coins(underlying_coins[0], underlying_coins[idx]) == swap
    assert factory.find_pool_for_coins(underlying_coins[idx], underlying_coins[0]) == swap


@pytest.mark.parametrize('sending,receiving', itertools.permutations(range(1, 4), 2))
def test_find_pool_underlying_base_pool_only(factory, underlying_coins, sending, receiving):
    assert factory.find_pool_for_coins(underlying_coins[sending], underlying_coins[receiving]) == ZERO_ADDRESS


def test_factory(factory, swap):
    assert factory.get_n_coins(swap) == [2, 4]


def test_get_coins(factory, swap, wrapped_coins):
    assert factory.get_coins(swap) == wrapped_coins


def test_get_underlying_coins(factory, swap, underlying_coins):
    assert factory.get_underlying_coins(swap) == underlying_coins + [ZERO_ADDRESS] * 4


def test_get_decimals(factory, swap, wrapped_decimals):
    assert factory.get_decimals(swap) == wrapped_decimals


def test_get_underlying_decimals(factory, swap, underlying_decimals):
    assert factory.get_underlying_decimals(swap) == underlying_decimals + [0] * 4


def test_get_rates(factory, swap, base_pool):
    assert factory.get_rates(swap) == [10**18, base_pool.get_virtual_price()]


def test_get_balances(factory, swap):
    assert factory.get_balances(swap) == [swap.balances(0), swap.balances(1)]


def get_underlying_balances(factory, swap, base_pool):
    pass


def test_get_A(factory, swap):
    assert factory.get_A(swap) == swap.A()


def test_get_fees(factory, swap):
    assert factory.get_fees(swap) == [swap.fee(), swap.admin_fee()]


def test_get_admin_balances(factory, swap):
    assert factory.get_admin_balances(swap) == [swap.admin_balances(0), swap.admin_balances(1)]


@pytest.mark.parametrize('sending,receiving', itertools.permutations(range(1, 4), 2))
def test_get_coin_indices_underlying(factory, swap, sending, receiving, underlying_coins):
    i, j, is_underlying = factory.get_coin_indices(swap, underlying_coins[sending], underlying_coins[receiving])
    assert i == sending
    assert j == receiving
    assert is_underlying


@pytest.mark.parametrize('sending,receiving', [(0, 1), (1, 0)])
def test_get_coin_indices(factory, swap, sending, receiving, wrapped_coins):
    i, j, is_underlying = factory.get_coin_indices(swap, wrapped_coins[sending], wrapped_coins[receiving])
    assert i == sending
    assert j == receiving
    assert not is_underlying


@pytest.mark.parametrize('idx', range(1, 4))
def test_get_coin_indices_reverts(factory, swap, base_lp_token, underlying_coins, idx):
    with brownie.reverts():
        factory.get_coin_indices(swap, base_lp_token, underlying_coins[idx])


def test_add_base_pool(factory, alice, bob):
    factory.add_base_pool("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714", bob, {'from': alice})
    assert factory.base_pool_count() == 2
    assert factory.base_pool_list(1) == "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714"


def test_add_base_pool_already_exists(factory, base_pool, alice, bob):
    with brownie.reverts("dev: pool exists"):
        factory.add_base_pool(base_pool, bob, {'from': alice})


def test_add_base_pool_only_admin(factory, base_pool, bob):
    with brownie.reverts("dev: admin-only function"):
        factory.add_base_pool("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714", bob, {'from': bob})


def test_deploy_metapool(StableSwapMeta, factory, base_pool, alice, bob):
    coin = ERC20(decimals=7)

    tx = factory.deploy_metapool(base_pool, "Name", "SYM", coin, 12345, 50000000, {'from': bob})
    assert tx.return_value == tx.new_contracts[0]
    swap = StableSwapMeta.at(tx.return_value)

    assert swap.coins(0) == coin
    assert swap.A() == 12345
    assert swap.fee() == 50000000
    assert swap.admin() == alice

    assert factory.pool_count() == 2
    assert factory.pool_list(1) == swap
    assert factory.get_decimals(swap) == [7, 18]
