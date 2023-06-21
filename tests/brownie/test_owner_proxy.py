import math

import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS
from brownie_tokens import ERC20


def pack_values(values) -> bytes:
    """Stolen from curvefi/curve-pool-registry"""
    assert max(values) < 256
    return sum(i << c * 8 for c, i in enumerate(values))


@pytest.fixture(autouse=True)
def setup(alice, factory, owner_proxy):
    factory.commit_transfer_ownership(owner_proxy, {"from": alice})
    owner_proxy.accept_transfer_ownership(factory, {"from": alice})


@pytest.fixture
def new_factory(Factory, alice):
    return Factory.deploy(alice, {"from": alice})


@pytest.fixture
def new_base_pool(alice, CurveTokenV3, CurvePool, registry):
    lp_token = CurveTokenV3.deploy("Test LP Token", "Tester", {"from": alice})
    base_coins = [ERC20() for _ in range(3)]
    pool = CurvePool.deploy(alice, base_coins, lp_token, 200, 3000000, 5000000000, {"from": alice})
    lp_token.set_minter(pool, {"from": alice})

    registry.add_pool_without_underlying(
        pool,
        3,
        lp_token,
        "0x0",
        pack_values([18, 18, 18]),
        pack_values([0, 0, 0]),
        True,
        False,
        "Test Base Pool",
    )
    return pool


def test_commit_ownership_transfer(factory, owner_proxy, alice, bob):
    owner_proxy.commit_transfer_ownership(factory, bob, {"from": alice})
    assert factory.future_admin() == bob


def test_only_ownership_admin_commit_ownership_transfer(factory, owner_proxy, bob):
    with brownie.reverts():
        owner_proxy.commit_transfer_ownership(factory, bob, {"from": bob})


def test_accept_transfer_ownership(new_factory, alice, owner_proxy):
    new_factory.commit_transfer_ownership(owner_proxy, {"from": alice})
    owner_proxy.accept_transfer_ownership(new_factory, {"from": alice})
    assert new_factory.admin() == owner_proxy


def test_unguarded_accept_transfer_ownership(new_factory, alice, bob, owner_proxy):
    new_factory.commit_transfer_ownership(owner_proxy, {"from": alice})
    owner_proxy.accept_transfer_ownership(new_factory, {"from": bob})
    assert new_factory.admin() == owner_proxy


def test_set_fee_receiver(factory, alice, bob, owner_proxy):
    # there is no input validation
    owner_proxy.set_fee_receiver(factory, ZERO_ADDRESS, bob, {"from": alice})
    assert factory.get_fee_receiver(ZERO_ADDRESS) == bob


def test_set_fee_receiver_guarded(factory, bob, owner_proxy):
    with brownie.reverts("Access denied"):
        owner_proxy.set_fee_receiver(factory, ZERO_ADDRESS, bob, {"from": bob})


def test_commit_new_admins(owner_proxy, alice, bob, charlie, dave):
    owner_proxy.commit_set_admins(bob, charlie, dave, {"from": alice})
    assert owner_proxy.future_ownership_admin() == bob
    assert owner_proxy.future_parameter_admin() == charlie
    assert owner_proxy.future_emergency_admin() == dave


def test_guarded_commit_new_admins(owner_proxy, bob):
    with brownie.reverts("Access denied"):
        owner_proxy.commit_set_admins(bob, bob, bob, {"from": bob})


def test_apply_set_admins(owner_proxy, alice, bob, charlie, dave):
    owner_proxy.commit_set_admins(bob, charlie, dave, {"from": alice})
    owner_proxy.apply_set_admins({"from": alice})
    assert owner_proxy.ownership_admin() == bob
    assert owner_proxy.parameter_admin() == charlie
    assert owner_proxy.emergency_admin() == dave


def test_apply_set_admins_guarded(owner_proxy, alice, bob, charlie, dave):
    owner_proxy.commit_set_admins(bob, charlie, dave, {"from": alice})
    with brownie.reverts("Access denied"):
        owner_proxy.apply_set_admins({"from": bob})


def test_ramp_A(owner_proxy, swap, alice, chain):
    future_a = swap.A() * 1.5
    future_time = chain.time() + 86400
    A_PRECISION = 100
    owner_proxy.ramp_A(swap, future_a, future_time, {"from": alice})
    assert swap.future_A() / A_PRECISION == future_a
    assert swap.future_A_time() == future_time
    chain.sleep(86400 + 1)


def test_ramp_A_guarded(owner_proxy, swap, bob):
    with brownie.reverts("Access denied"):
        owner_proxy.ramp_A(swap, 0, 0, {"from": bob})


def test_stop_ramp_A(owner_proxy, swap, chain, alice):
    future_a = swap.A() * 2
    future_time = chain.time() + 86400
    owner_proxy.ramp_A(swap, future_a, future_time, {"from": alice})

    chain.sleep(86400 // 2)
    owner_proxy.stop_ramp_A(swap, {"from": alice})

    assert math.isclose(swap.A(), 3 * future_a / 4)


def test_stop_ramp_A_guarded(owner_proxy, swap, chain, alice, bob):
    future_a = swap.A() * 2
    future_time = chain.time() + 86400
    owner_proxy.ramp_A(swap, future_a, future_time, {"from": alice})

    chain.sleep(86400 // 2)
    owner_proxy.stop_ramp_A(swap, {"from": alice})

    with brownie.reverts("Access denied"):
        owner_proxy.stop_ramp_A(swap, {"from": bob})


def test_add_base_pool(owner_proxy, factory, new_base_pool, meta_implementations, alice):

    owner_proxy.add_base_pool(
        factory,
        new_base_pool,
        alice,
        2,
        meta_implementations + [ZERO_ADDRESS] * 8,
        {"from": alice},
    )

    assert factory.base_pool_list(0) == new_base_pool


def test_add_base_pool_guarded(owner_proxy, bob):
    with brownie.reverts("Access denied"):
        owner_proxy.add_base_pool(
            ETH_ADDRESS, ETH_ADDRESS, ETH_ADDRESS, 0, [ZERO_ADDRESS] * 10, {"from": bob}
        )


def test_set_metapool_implementations(
    alice, owner_proxy, factory, new_base_pool, meta_implementations
):
    impls = meta_implementations + [ZERO_ADDRESS] * 8
    owner_proxy.add_base_pool(
        factory,
        new_base_pool,
        ETH_ADDRESS,
        2,
        [ZERO_ADDRESS] * 10,
        {"from": alice},
    )
    owner_proxy.set_metapool_implementations(factory, new_base_pool, impls, {"from": alice})
    assert factory.metapool_implementations(new_base_pool) == impls


def test_set_metapool_implementations_guarded(
    bob, owner_proxy, factory, base_pool, meta_implementations
):
    impls = meta_implementations + [ZERO_ADDRESS] * 8
    with brownie.reverts("Access denied"):
        owner_proxy.set_metapool_implementations(factory, base_pool, impls, {"from": bob})


def test_set_plain_implementation(
    alice, owner_proxy, factory, plain_implementations, plain_pool_size
):
    owner_proxy.set_plain_implementations(
        factory, plain_pool_size, plain_implementations + [ZERO_ADDRESS] * 6, {"from": alice}
    )
    assert factory.plain_implementations(plain_pool_size, 0) == plain_implementations[0]


def test_set_plain_implementation_guarded(
    bob, owner_proxy, factory, plain_implementations, plain_pool_size
):
    with brownie.reverts("Access denied"):
        owner_proxy.set_plain_implementations(
            factory, plain_pool_size, plain_implementations + [ZERO_ADDRESS] * 6, {"from": bob}
        )
