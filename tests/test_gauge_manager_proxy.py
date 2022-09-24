import brownie
import pytest


@pytest.fixture(scope="module")
def manager_proxy(alice, factory, owner_proxy, ManagerProxy):
    factory.commit_transfer_ownership(owner_proxy, {"from": alice})
    owner_proxy.accept_transfer_ownership(factory, {"from": alice})

    return ManagerProxy.deploy(factory, alice, {"from": alice})


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
