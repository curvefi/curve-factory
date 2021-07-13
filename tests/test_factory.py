import itertools

import brownie
import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import ERC20


@pytest.fixture(autouse=True)
def setup(
    swap,
    bob,
    alice,
    add_initial_liquidity,
    mint_bob,
    swap_plain,
    plain_coins,
    approve_bob,
    coin,
    swap_btc,
):
    amount = 10 ** coin.decimals()
    swap.exchange(0, 1, amount, 0, {"from": bob})
    swap.exchange(1, 0, 10 ** 18, 0, {"from": bob})

    # add initial liquidity to plain pool
    amounts = []
    for coin in plain_coins[:2]:
        amount = 1e6 * 10 ** coin.decimals()
        amounts.append(amount)
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap_plain, 2 ** 256 - 1, {"from": alice})

    swap_plain.add_liquidity(amounts, 0, {"from": alice})

    amount = 10 ** coin.decimals()
    plain_coins[0]._mint_for_testing(bob, amount, {"from": bob})
    plain_coins[0].approve(swap_plain, amount, {"from": bob})
    swap_plain.exchange(0, 1, amount, 0, {"from": bob})


@pytest.fixture()
def new_factory_setup(
    new_factory,
    implementation_plain,
    alice,
    base_pool,
    fee_receiver,
    implementation_usd,
    implementation_btc,
):
    new_factory.set_plain_implementations(
        2, [implementation_plain] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    new_factory.add_base_pool(
        base_pool, fee_receiver, [implementation_usd] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    pool = Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")
    new_factory.add_base_pool(
        pool, fee_receiver, [implementation_btc] + [ZERO_ADDRESS] * 9, {"from": alice}
    )


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_find_pool_for_coins(
    factory, is_rebase, swap, swap_plain, plain_coins, wrapped_coins, sending, receiving
):
    if is_rebase:
        pytest.skip()
    assert factory.find_pool_for_coins(wrapped_coins[sending], wrapped_coins[receiving]) == swap
    assert factory.find_pool_for_coins(plain_coins[sending], plain_coins[receiving]) == swap_plain


@pytest.mark.parametrize("idx", range(1, 4))
def test_find_pool_for_coins_underlying(factory, is_rebase, swap, underlying_coins, idx):
    if is_rebase:
        pytest.skip()
    assert factory.find_pool_for_coins(underlying_coins[0], underlying_coins[idx]) == swap
    assert factory.find_pool_for_coins(underlying_coins[idx], underlying_coins[0]) == swap


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(1, 4), 2))
def test_find_pool_underlying_base_pool_only(factory, underlying_coins, sending, receiving):
    assert (
        factory.find_pool_for_coins(underlying_coins[sending], underlying_coins[receiving])
        == ZERO_ADDRESS
    )


def test_factory(factory, swap):
    assert factory.get_meta_n_coins(swap) == [2, 4]


def test_get_coins(factory, swap, wrapped_coins, plain_coins, swap_plain):
    coins = factory.get_coins(swap)
    assert coins == wrapped_coins + [ZERO_ADDRESS] * 2
    coins = factory.get_coins(swap_plain)
    assert coins == plain_coins


def test_get_underlying_coins(factory, swap, underlying_coins):
    assert factory.get_underlying_coins(swap) == underlying_coins + [ZERO_ADDRESS] * 4


def test_get_decimals(factory, swap, wrapped_decimals, swap_plain, plain_decimals):
    decimals = factory.get_decimals(swap)
    assert decimals == wrapped_decimals + [0] * (len(decimals) - len(wrapped_decimals))
    decimals = factory.get_decimals(swap_plain)
    assert decimals == plain_decimals


def test_get_underlying_decimals(factory, swap, underlying_decimals):
    assert factory.get_underlying_decimals(swap) == underlying_decimals + [0] * 4


def test_get_metapool_rates(factory, swap, base_pool):
    assert factory.get_metapool_rates(swap) == [10 ** 18, base_pool.get_virtual_price()]


def test_get_balances(factory, swap, swap_plain):
    assert factory.get_balances(swap) == [swap.balances(0), swap.balances(1), 0, 0]
    assert factory.get_balances(swap_plain) == [
        swap_plain.balances(0),
        swap_plain.balances(1),
        0,
        0,
    ]


def test_get_underlying_balances(factory, swap, is_rebase, base_pool, base_lp_token, swap_plain):
    if is_rebase:
        pytest.skip()
    base_total_supply = base_lp_token.totalSupply()
    underlying_pct = swap.balances(1) / base_total_supply
    balances = factory.get_underlying_balances(swap)
    assert pytest.approx(balances[0]) == swap.balances(0)
    assert pytest.approx(balances[1]) == base_pool.balances(0) * underlying_pct
    assert pytest.approx(balances[2]) == base_pool.balances(1) * underlying_pct
    assert pytest.approx(balances[3]) == base_pool.balances(2) * underlying_pct
    assert balances[4:] == [0] * 4

    with brownie.reverts("dev: pool is not a metapool"):
        factory.get_underlying_balances(swap_plain)


def test_get_A(factory, swap):
    assert factory.get_A(swap) == swap.A()


def test_get_fees(factory, swap):
    assert factory.get_fees(swap) == [swap.fee(), swap.admin_fee()]


def test_get_admin_balances(factory, swap, swap_plain):
    assert factory.get_admin_balances(swap) == [
        swap.admin_balances(0),
        swap.admin_balances(1),
        0,
        0,
    ]
    assert factory.get_admin_balances(swap_plain) == [
        swap_plain.admin_balances(0),
        swap_plain.admin_balances(1),
        0,
        0,
    ]


@pytest.mark.parametrize("sending,receiving", itertools.permutations(range(1, 4), 2))
def test_get_coin_indices_underlying(factory, swap, sending, receiving, underlying_coins):
    i, j, is_underlying = factory.get_coin_indices(
        swap, underlying_coins[sending], underlying_coins[receiving]
    )
    assert i == sending
    assert j == receiving
    assert is_underlying


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_get_coin_indices(factory, swap, sending, receiving, wrapped_coins):
    i, j, is_underlying = factory.get_coin_indices(
        swap, wrapped_coins[sending], wrapped_coins[receiving]
    )
    assert i == sending
    assert j == receiving
    assert not is_underlying


@pytest.mark.parametrize("idx", range(1, 4))
def test_get_coin_indices_reverts(factory, swap, base_lp_token, underlying_coins, idx):
    with brownie.reverts():
        factory.get_coin_indices(swap, base_lp_token, underlying_coins[idx])


def test_add_base_pool(factory, alice, fee_receiver, implementation_usd):
    susd_pool = "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD"
    factory.add_base_pool(
        susd_pool, fee_receiver, [implementation_usd] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    assert factory.base_pool_count() == 3
    assert factory.base_pool_list(2) == susd_pool
    assert factory.fee_receiver(susd_pool) == fee_receiver


def test_add_base_pool_already_exists(factory, base_pool, alice, fee_receiver, implementation_usd):
    with brownie.reverts("dev: pool exists"):
        factory.add_base_pool(
            base_pool, fee_receiver, [implementation_usd] + [ZERO_ADDRESS] * 9, {"from": alice}
        )


def test_add_base_pool_only_admin(factory, base_pool, bob, fee_receiver, implementation_usd):
    with brownie.reverts("dev: admin-only function"):
        factory.add_base_pool(
            "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD",
            fee_receiver,
            [implementation_usd] + [ZERO_ADDRESS] * 9,
            {"from": bob},
        )


def test_deploy_metapool(MetaUSD, new_factory, new_factory_setup, base_pool, bob):
    coin = ERC20(decimals=7)

    tx = new_factory.deploy_metapool(
        base_pool, "Name", "SYM", coin, 12345, 50000000, 0, {"from": bob}
    )
    assert tx.return_value == tx.new_contracts[0]
    swap = MetaUSD.at(tx.return_value)

    assert swap.coins(0) == coin
    assert swap.A() == 12345
    assert swap.fee() == 50000000

    assert new_factory.pool_count() == 1
    assert new_factory.pool_list(0) == swap
    assert new_factory.get_decimals(swap) == [7, 18, 0, 0]


def test_add_existing_metapools(
    factory, new_factory, fee_receiver, implementation_usd, base_pool, alice
):
    assert new_factory.pool_count() == 0
    # add existing USD pools to new factory
    new_factory.add_base_pool(
        base_pool, fee_receiver, [implementation_usd] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    new_factory.add_existing_metapools(
        ["0x5a6A4D54456819380173272A5E8E9B9904BdF41B", "0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c"]
        + [ZERO_ADDRESS] * 8
    )
    assert new_factory.pool_count() == 2
    assert new_factory.pool_list(0) == "0x5a6A4D54456819380173272A5E8E9B9904BdF41B"
    assert new_factory.pool_list(1) == "0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c"
    assert (
        new_factory.get_implementation_address("0x5a6A4D54456819380173272A5E8E9B9904BdF41B")
        == "0x5F890841f657d90E081bAbdB532A05996Af79Fe6"
    )


def test_add_existing_metapools_unknown_pool(swap, new_factory):
    with brownie.reverts("dev: pool not in old factory"):
        new_factory.add_existing_metapools([swap] + [ZERO_ADDRESS] * 9)


def test_add_existing_metapools_duplicate_pool(
    new_factory, base_pool, implementation_usd, fee_receiver, alice
):
    new_factory.add_base_pool(
        base_pool, fee_receiver, [implementation_usd] + [ZERO_ADDRESS] * 9, {"from": alice}
    )
    new_factory.add_existing_metapools(
        ["0x5a6A4D54456819380173272A5E8E9B9904BdF41B"] + [ZERO_ADDRESS] * 9
    )
    with brownie.reverts("dev: pool already exists"):
        new_factory.add_existing_metapools(
            ["0x5a6A4D54456819380173272A5E8E9B9904BdF41B"] + [ZERO_ADDRESS] * 9
        )


def test_deploy_plain_pool(Plain2Basic, is_rebase, new_factory_setup, new_factory, bob):
    if is_rebase:
        pytest.skip()

    coins = [ERC20(decimals=7), ERC20(decimals=9), ZERO_ADDRESS, ZERO_ADDRESS]

    tx = new_factory.deploy_plain_pool(
        "Test Plain", "TST", coins, 12345, 50000000, 0, {"from": bob}
    )
    assert tx.return_value == tx.new_contracts[0]
    swap = Plain2Basic.at(tx.return_value)

    assert swap.coins(0) == coins[0]
    assert swap.coins(1) == coins[1]

    assert swap.A() == 12345
    assert swap.fee() == 50000000

    assert new_factory.pool_count() == 1
    assert new_factory.pool_list(0) == swap
    assert new_factory.get_decimals(swap) == [7, 9, 0, 0]


def test_pool_count(new_factory, new_factory_setup, bob, base_pool):

    coins = [ERC20(decimals=7), ERC20(decimals=9), ZERO_ADDRESS, ZERO_ADDRESS]

    tx = new_factory.deploy_plain_pool(
        "Test Plain", "TST", coins, 12345, 50000000, 0, {"from": bob}
    )
    assert tx.return_value == tx.new_contracts[0]
    assert new_factory.pool_count() == 1

    coin = ERC20(decimals=7)
    tx = new_factory.deploy_metapool(
        base_pool, "Name", "SYM", coin, 12345, 50000000, 0, {"from": bob}
    )
    assert tx.return_value == tx.new_contracts[0]
    assert new_factory.pool_count() == 2

    coin = ERC20(decimals=7)
    pool = Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")
    tx = new_factory.deploy_metapool(pool, "Name", "SYM", coin, 123456, 50000000, 0, {"from": bob})
    assert new_factory.pool_count() == 3


def test_deploy_plain_pool_revert(base_pool, new_factory, new_factory_setup, bob):
    coin = ERC20(decimals=7)
    new_factory.deploy_metapool(base_pool, "Name", "SYM", coin, 12345, 50000000, 0, {"from": bob})
    existing_coin = base_pool.coins(0)
    assert new_factory.base_pool_assets(existing_coin)
    coins = [existing_coin, ERC20(decimals=9), ZERO_ADDRESS, ZERO_ADDRESS]
    # should revert because a metapool already exists for one of the coins
    with brownie.reverts("Invalid asset, deploy a metapool"):
        new_factory.deploy_plain_pool("Test Plain", "TST", coins, 12345, 50000000, 0, {"from": bob})
