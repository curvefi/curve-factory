# @version 0.2.8


interface Curve:
    def initialize(
        _name: String[32],
        _symbol: String[10],
        _coin: address,
        _A: uint256,
        _fee: uint256,
        _owner: address,
    ): nonpayable


implementation: public(address)
owner: public(address)


@external
def __init__(_implementation: address, _owner: address):
    self.implementation = _implementation
    self.owner = _owner


@external
def deploy_pool(_name: String[32], _symbol: String[10], _coin: address, _A: uint256, _fee: uint256) -> address:
    pool: address = create_forwarder_to(self.implementation)
    Curve(pool).initialize(_name, _symbol, _coin, _A, _fee, self.owner)
    return pool
