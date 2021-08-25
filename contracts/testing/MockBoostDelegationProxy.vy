# @version 0.2.15
"""
@title Mock Boost Delegation
"""
from vyper.interfaces import ERC20

delegation: public(address)
voting_escrow: public(address)


@external
def __init__(voting_escrow: address, _delegation: address):
    self.delegation = _delegation
    self.voting_escrow = voting_escrow


@view
@external
def adjusted_balance_of(_addr: address) -> uint256:
    if self.delegation == ZERO_ADDRESS:
        return ERC20(self.voting_escrow).balanceOf(_addr)
    # simulated behavior being that we'd call the actual
    # veboost contract
    # which would look like
    # Veboost(addr).adjusted_balance_of(_addr)
    # but for the most part we are just afirming that this
    # contract is called not the implementation of veboost
    return 69


@external
def set_delegation(_delegation: address):
    self.delegation = _delegation
