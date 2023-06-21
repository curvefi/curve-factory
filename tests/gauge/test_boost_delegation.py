from brownie import ETH_ADDRESS


def test_boost_delegation_not_set_in_proxy(alice, gauge, voting_escrow):
    tx = gauge.user_checkpoint(alice, {"from": alice})
    subcall = next(
        (tx for tx in tx.subcalls if tx["function"] == "adjusted_balance_of(address)"), {}
    )
    next_subcall = tx.subcalls[tx.subcalls.index(subcall) + 1]

    expected = {"to": voting_escrow.address, "op": "STATICCALL", "function": "balanceOf(address)"}
    for k in expected.keys():
        assert next_subcall[k] == expected[k]


def test_boost_delegation_set_in_addr_provider(alice, gauge, mock_veboost_proxy):
    mock_veboost_proxy.set_delegation(ETH_ADDRESS, {"from": alice})

    tx = gauge.user_checkpoint(alice, {"from": alice})
    subcall = next(
        (tx for tx in tx.subcalls if tx["function"] == "adjusted_balance_of(address)"), {}
    )

    assert subcall["return_value"][0] == 69
