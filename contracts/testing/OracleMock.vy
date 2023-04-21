# @version 0.3.7
"""
@title Oracle mock for ETH rebase
"""

price: constant(uint256) = 1 * 10**18

@view
@external
def get_price() -> uint256:
    return price
