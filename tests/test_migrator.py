import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob", "approve_bob")


@pytest.fixture(scope="module")
def swap2(MetaImplementationUSD, alice, base_pool, factory, coin):
    tx = factory.deploy_metapool(
        base_pool, "Test Swap", "TST", coin, 200, 4000000, 0, {"from": alice}
    )
    yield MetaImplementationUSD.at(tx.return_value)


@pytest.fixture(scope="module")
def migrator(PoolMigrator, alice, swap):
    contract = PoolMigrator.deploy({"from": alice})
    swap.approve(contract, 2 ** 256 - 1, {"from": alice})
    yield contract


def test_migrate(alice, migrator, swap, swap2):
    balance = swap.balanceOf(alice)
    migrator.migrate_to_new_pool(swap, swap2, balance, {"from": alice})

    assert swap.balanceOf(alice) == 0
    assert swap2.balanceOf(alice) == balance

    assert swap.balanceOf(migrator) == 0
    assert swap2.balanceOf(migrator) == 0


def test_migrate_partial(alice, migrator, swap, swap2, coin):
    balance = swap.balanceOf(alice)
    migrator.migrate_to_new_pool(swap, swap2, balance // 4, {"from": alice})

    assert swap.balanceOf(alice) == balance - balance // 4
    assert abs(swap2.balanceOf(alice) - balance // 4) < 8 + (10 ** 18 - coin.decimals())

    assert swap.balanceOf(migrator) == 0
    assert swap2.balanceOf(migrator) == 0


def test_migrate_multiple(alice, migrator, swap, swap2, coin):
    balance = swap.balanceOf(alice)
    for i in range(4):
        migrator.migrate_to_new_pool(swap, swap2, balance // 4, {"from": alice})

    assert swap.balanceOf(alice) < 5
    assert abs(swap2.balanceOf(alice) - balance) < 8 + (10 ** 18 - coin.decimals())

    assert swap.balanceOf(migrator) == 0
    assert swap2.balanceOf(migrator) == 0


def test_migrate_bidirectional(alice, migrator, swap, swap2):
    balance = swap.balanceOf(alice)
    migrator.migrate_to_new_pool(swap, swap2, balance, {"from": alice})
    swap2.approve(migrator, 2 ** 256 - 1, {"from": alice})
    migrator.migrate_to_new_pool(swap2, swap, balance, {"from": alice})

    assert abs(swap.balanceOf(alice) - balance) < 4
    assert swap2.balanceOf(alice) == 0

    assert swap.balanceOf(migrator) == 0
    assert swap2.balanceOf(migrator) == 0


def test_migration_wrong_pool(alice, migrator, swap, swap_btc):
    balance = swap.balanceOf(alice)
    with brownie.reverts():
        migrator.migrate_to_new_pool(swap, swap_btc, balance, {"from": alice})


def test_insufficient_balance(alice, migrator, swap, swap2):
    balance = swap.balanceOf(alice)
    with brownie.reverts():
        migrator.migrate_to_new_pool(swap, swap2, balance + 1, {"from": alice})
