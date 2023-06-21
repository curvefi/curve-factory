import brownie
import pytest

from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module")
def manager_proxy(alice, factory, owner_proxy, ManagerProxy):
    factory.commit_transfer_ownership(owner_proxy, {"from": alice})
    owner_proxy.accept_transfer_ownership(factory, {"from": alice})

    proxy = ManagerProxy.deploy(factory, alice, {"from": alice})
    owner_proxy.set_gauge_manager(proxy, {"from": alice})
    return proxy


def test_add_reward(alice, manager_proxy, gauge, coin_reward):
    assert gauge.reward_count() == 0
    manager_proxy.add_reward(gauge, coin_reward, alice, {"from": alice})

    assert gauge.reward_tokens(0) == coin_reward
    assert gauge.reward_data(coin_reward)["distributor"] == alice


def test_set_reward_distributor(alice, bob, manager_proxy, gauge, coin_reward):
    assert gauge.reward_count() == 0
    manager_proxy.add_reward(gauge, coin_reward, alice, {"from": alice})

    manager_proxy.set_reward_distributor(gauge, coin_reward, bob, {"from": alice})
    assert gauge.reward_data(coin_reward)["distributor"] == bob

def test_deploy_gauge(alice, manager_proxy, factory, coin_a, coin_b):
    pool = factory.deploy_plain_pool(
        "foo",
        "foo",
        [coin_a, coin_b, ZERO_ADDRESS, ZERO_ADDRESS],
        200,
        .0004 * 10 ** 10,
        0,
        0,
        {"from": alice}
    ).return_value

    gauge = manager_proxy.deploy_gauge(pool, {"from": alice}).return_value

    assert manager_proxy.gauge_manager(gauge) == alice
    assert factory.get_gauge(pool) == gauge


def test_set_gauge_manager(alice, bob, manager_proxy, gauge):
    # alice is both the ownership_admin and the manager
    tx = manager_proxy.set_gauge_manager(gauge, bob, {"from": alice})
    assert manager_proxy.gauge_manager(gauge) == bob
    assert tx.events["SetGaugeManager"].values() == [gauge, bob]

    # bob is the gague manager and can transfer managership
    manager_proxy.set_gauge_manager(gauge, alice, {"from": bob})
    assert manager_proxy.gauge_manager(gauge) == alice

    # bob is no longer the gauge manager
    with brownie.reverts():
        manager_proxy.set_gauge_manager(gauge, alice, {"from": bob})


def test_set_manager(alice, bob, manager_proxy):
    # alice is both the manager and the ownership_admin
    manager_proxy.set_manager(bob, {"from": alice})
    assert manager_proxy.manager() == bob

    # now alice is only the ownership_admin
    manager_proxy.set_manager(alice, {"from": alice})
    assert manager_proxy.manager() == alice

    with brownie.reverts():
        # bob is not the manager anymore
        manager_proxy.set_manager(alice, {"from": bob})
    assert manager_proxy.manager() == alice
