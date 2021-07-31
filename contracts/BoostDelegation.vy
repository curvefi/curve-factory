# @version 0.2.15
"""
@title Boost Delegation
@author Curve Finance
@license MIT
@notice Allows delegation of veCRV boost within factory gauges
"""

from vyper.interfaces import ERC20


struct ReceivedBoost:
    length: uint256
    data: uint256[10]


# user -> data on global boosts delegated to user
# delegation data is tightly packed as [address][uint16 pct][uint40 cancel time][uint40 expire time]
delegation_count: HashMap[address, uint256]

# user -> pool -> data on per-pool boosts delegated to user
delegation_data: HashMap[address, HashMap[address, ReceivedBoost]]

# user -> pool -> address that user has delegated boost to for this pool
delegated_to: public(HashMap[address, HashMap[address, uint256]])

operator: HashMap[address, address]

VOTING_ESCROW: constant(address) = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2


@external
def set_operator(_operator: address) -> bool:
    """
    @notice Set the authorized operator for an address
    @dev An operator can delegate boost, including creating delegations that
         cannot be cancelled. This permission should only be given to trusted
         3rd parties and smart contracts where the contract behavior is known
         to be not malicious.
    @param _operator Approved operator address. Set to `ZERO_ADDRESS` to revoke
                     the currently active approval.
    @return bool success
    """
    self.operator[msg.sender] = _operator
    return True


@internal
def _delete_delegation_data(_delegator: address, _gauge: address, _delegation_data: uint256):
    # delete record for the delegator
    self.delegated_to[_delegator][_gauge] = 0
    self.delegation_count[_delegator] -= 1

    receiver: address = convert(shift(_delegation_data, 96), address)
    length: uint256 = self.delegation_data[receiver][_gauge].length

    # delete record for the receiver
    for i in range(10):
        if i == length - 1:
            self.delegation_data[receiver][_gauge].data[i] = 0
            break
        if self.delegation_data[receiver][_gauge].data[i] == _delegation_data:
            self.delegation_data[receiver][_gauge].data[i] = self.delegation_data[receiver][_gauge].data[length-1]
            self.delegation_data[receiver][_gauge].data[length-1] = 0


@external
def delegate_boost(
    _delegator: address,
    _gauge: address,
    _receiver: address,
    _pct: uint256,
    _cancel_time: uint256,
    _expire_time: uint256
) -> bool:
    """
    @notice Delegate per-gauge or global boost to another account
    @param _delegator Address of the user delegating boost. The caller must be the
                      delegator or the approved operator of the delegator.
    @param _gauge Address of the gauge to delegate for. Set as ZERO_ADDRESS for
                  global delegation. Global delegation is not possible if there is
                  also one or more active per-gauge delegations.
    @param _receiver Address to delegate boost to.
    @param _pct Percentage of boost to delegate. 100% is expressed as 10000.
    @param _cancel_time Delegation cannot be cancelled before this time.
    @param _expire_time Delegation automatically expires at this time.
    @return bool success
    """
    assert msg.sender in [_delegator, self.operator[_delegator]], "Only owner or operator"

    assert _pct <= 10000, "Percent too high"
    assert _expire_time < 2**40, "Expiry time too high"
    assert _expire_time > block.timestamp, "Already expired"
    assert _cancel_time <= _expire_time, "Cancel time after expiry time"

    # check for an existing, expired delegation
    data: uint256 = self.delegated_to[_delegator][_gauge]
    if data != 0:
        assert data % 2**40 <= block.timestamp, "Existing delegation has not expired"
        self._delete_delegation_data(_delegator, _gauge, data)

    if _gauge == ZERO_ADDRESS:
        assert self.delegation_count[_delegator] == 0, "Cannot delegate globally while per-gauge is active"
    else:
        assert self.delegated_to[_delegator][ZERO_ADDRESS] == 0, "Cannot delegate per-gauge while global is active"

    # tightly pack the delegation data
    # [address][uint16 pct][uint40 cancel time][uint40 expire time]
    data = (
        shift(convert(_receiver, uint256), -96) +
        shift(_pct, -80) +
        shift(_cancel_time, -40) +
        _expire_time
    )
    idx: uint256 = self.delegation_data[_receiver][_gauge].length

    self.delegation_data[_receiver][_gauge].data[idx] = data
    self.delegated_to[_delegator][_gauge] = data
    self.delegation_data[_receiver][_gauge].length = idx + 1

    return True


@external
def cancel_delegation(_delegator: address, _gauge: address) -> bool:
    """
    @notice Cancel an existing boost delegation
    @param _delegator Address of the user delegating boost. The caller must be the
                      delegator or the approved operator of the delegator.
    @param _gauge Address of the gauge to cancel delegattion for. Set as ZERO_ADDRESS
                  for global delegation.
    @return bool success
    """
    assert msg.sender in [_delegator, self.operator[_delegator]], "Only owner or operator"

    data: uint256 = self.delegated_to[_delegator][_gauge]
    assert data != 0, "No delegation for this pool"
    assert shift(data, 40) % 2**40 <= block.timestamp, "Not yet cancellable"
    self._delete_delegation_data(_delegator, _gauge, data)

    return True


@view
@external
def get_adjusted_vecrv_balance(_user: address, _gauge: address) -> uint256:
    """
    @notice Get the adjusted veCRV balance of an account after delegation
    @param _user Address to query a veCRV balance for
    @param _gauge Gauge address
    @return Adjusted veCRV balance after delegation
    """
    # query the initial vecrv balance for `_user`
    voting_balance: uint256 = ERC20(VOTING_ESCROW).balanceOf(_user)

    # check if the user has delegated any vecrv and reduce the voting balance
    delegation_count: uint256 = self.delegation_count[_user]
    if delegation_count != 0:
        is_global: bool = False
        # apply global delegation
        if delegation_count == 1:
            data: uint256 = self.delegated_to[_user][ZERO_ADDRESS]
            if data % 2**40 > block.timestamp:
                voting_balance = voting_balance * (10000 - shift(data, 80) % 2**16) / 10000
                is_global = True
        # apply pool-specific delegation
        if not is_global:
            data: uint256 = self.delegated_to[_user][_gauge]
            if data % 2**40 > block.timestamp:
                voting_balance = voting_balance * (10000 - shift(data, 80) % 2**16) / 10000

    # check for other vecrv delegated to `_user` and increase the voting balance
    for target in [_gauge, ZERO_ADDRESS]:
        length: uint256 = self.delegation_data[_user][target].length
        if length > 0:
            for i in range(10):
                if i == length:
                    break
                data: uint256 = self.delegation_data[_user][target].data[i]
                if data % 2**40 > block.timestamp:
                    delegator: address = convert(shift(data, 96), address)
                    delegator_balance: uint256 = ERC20(VOTING_ESCROW).balanceOf(delegator)
                    voting_balance += delegator_balance * (shift(data, 80) % 2**16) / 10000

    return voting_balance


@external
def update_delegation_records(_user: address, _gauge: address) -> bool:
    """
    @notice Remove data about any expired delegations for a user.
    @dev Reduces gas costs when calling `get_adjusted_vecrv_balance` on
         an address with expired delegations.
    @param _user Address to update records for.
    @param _gauge Gauge address. Use `ZERO_ADDRESS` for global delegations.
    """
    length: uint256 = self.delegation_data[_user][_gauge].length - 1
    adjusted_length: uint256 = length

    # iterate in reverse over `delegation_data` and remove expired records
    for i in range(10):
        if i > length:
            break
        idx: uint256 = length - i
        data: uint256 = self.delegation_data[_user][_gauge].data[idx]
        if data % 2**40 <= block.timestamp:
            # delete record for the delegator
            delegator: address = convert(shift(data, 96), address)
            self.delegated_to[delegator][_gauge] = 0
            self.delegation_count[delegator] -= 1

            # delete record for the receiver
            if idx == adjusted_length:
                self.delegation_data[_user][_gauge].data[idx] = 0
            else:
                self.delegation_data[_user][_gauge].data[idx] = self.delegation_data[_user][_gauge].data[adjusted_length]
            adjusted_length -= 1

    return True
