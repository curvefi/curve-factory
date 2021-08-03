import brownie

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400


def test_kick(add_initial_liquidity, alice, bob, chain, gauge, voting_escrow, crv, swap):
    chain.sleep(2 * WEEK + 5)

    crv.approve(voting_escrow, MAX_UINT256, {"from": alice})
    voting_escrow.create_lock(10 ** 20, chain.time() + 4 * WEEK, {"from": alice})

    swap.approve(gauge.address, MAX_UINT256, {"from": alice})
    gauge.deposit(10 ** 21, {"from": alice})

    assert gauge.working_balances(alice) == 10 ** 21

    chain.sleep(WEEK)

    with brownie.reverts("dev: kick not allowed"):
        gauge.kick(alice, {"from": bob})

    chain.sleep(4 * WEEK)

    gauge.kick(alice, {"from": bob})
    assert gauge.working_balances(alice) == 4 * 10 ** 20

    with brownie.reverts("dev: kick not needed"):
        gauge.kick(alice, {"from": bob})
