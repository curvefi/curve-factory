# @version 0.3.1


@pure
@external
def ecr(_sighash: bytes32, _v: uint8, _r: uint256, _s: uint256) -> address:
    return ecrecover(_sighash, convert(_v, uint256), _r, _s)
