import copy
import itertools as it
import math
from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple

import brownie
from brownie import ZERO_ADDRESS, Contract, chain, convert
from brownie.test import contract_strategy, strategy
from dataclassy import dataclass


@dataclass(iter=True, slots=True)
class Data:
    account: str = ZERO_ADDRESS
    percentage: int = 0
    cancel_time: int = 0
    expire_time: int = 0

    def __int__(self):
        return (
            (convert.to_uint(self.account) << 96)
            + (self.percentage << 80)
            + (self.cancel_time << 40)
            + self.expire_time
        )


class BoostDelegationLogic:
    def __init__(self, voting_escrow: Contract) -> None:
        self.delegation_count: DefaultDict[str, int] = defaultdict(lambda: 0)
        self.operator_of: DefaultDict[str, str] = defaultdict(lambda: ZERO_ADDRESS)

        self._delegation_data: DefaultDict[str, DefaultDict[str, List[Data]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._delegated_to: DefaultDict[str, DefaultDict[str, Data]] = defaultdict(
            lambda: defaultdict(lambda: Data())
        )

        self.is_killed: bool = False

        self.voting_escrow = voting_escrow

    def get_delegated_to(self, delegator: str, gauge: str) -> Tuple[str, int, int, int]:
        return tuple(self._delegated_to[delegator][gauge])

    def get_delegation_data(
        self, receiver: str, gauge: str, index: int
    ) -> Tuple[str, int, int, int]:
        if len(data := self._delegation_data[receiver][gauge]) > index:
            return tuple(data[index])
        return tuple(Data())

    def set_operator(self, operator: str, tx_params: Dict) -> bool:
        self.operator_of[tx_params["from"]] = operator
        return True

    def _delete_delegation_data(self, delegator: str, gauge: str, data: Data) -> bool:
        self._delegated_to[delegator][gauge] = Data()
        self.delegation_count[delegator] -= 1
        assert self.delegation_count[delegator] >= 0

        # delegation data has the delegator not the receiver
        receiver = data.account
        delegation_data = Data(delegator, *(tuple(data)[1:]))
        index = self._delegation_data[receiver][gauge].index(delegation_data)

        assert 0 <= index < 10
        self._delegation_data[receiver][gauge].remove(delegation_data)
        assert 0 <= len(self._delegation_data[receiver][gauge]) < 10

    def delegate_boost(
        self,
        delegator: str,
        gauge: str,
        receiver: str,
        pct: int,
        cancel_time: int,
        expire_time: int,
        tx_params: Dict,
    ):
        assert not self.is_killed
        assert tx_params["from"] in [delegator, self.operator_of[delegator]]

        assert delegator != receiver
        assert 100 <= pct <= 10_000
        assert chain.time() < expire_time < 2 ** 40
        assert cancel_time <= expire_time

        assert self.voting_escrow.balanceOf(delegator) >= 2500 * 10 ** 18

        # check for existing delegation
        if int(data := self._delegated_to[delegator][gauge]) != 0:
            # check that existing delegation has expired
            assert data.expire_time <= chain.time()
            self._delete_delegation_data(delegator, gauge, data)

        if gauge == ZERO_ADDRESS:
            # trying to delegate globally without first clearing records
            assert self.delegation_count[delegator] == 0
        else:
            # Cannot delegate per-gauge while global delegation is active
            assert int(self._delegated_to[delegator][ZERO_ADDRESS]) == 0

        data = Data(receiver, pct, cancel_time, expire_time)
        self._delegated_to[delegator][gauge] = data
        self.delegation_count[delegator] += 1

        delegation_data = copy.deepcopy(data)
        delegation_data.account = delegator
        self._delegation_data[receiver][gauge].append(delegation_data)
        assert len(self._delegation_data[receiver][gauge]) <= 10

    def cancel_delegation(self, delegator: str, gauge: str, tx_params: Dict):
        msg_sender = tx_params["from"]

        data = self._delegated_to[delegator][gauge]
        assert int(data) != 0

        receiver = data.account
        if msg_sender not in [receiver, self.operator_of[receiver]]:
            assert msg_sender in [delegator, self.operator_of[delegator]]
            assert data.cancel_time <= chain.time()

        self._delete_delegation_data(delegator, gauge, data)

    def update_delegation_records(self, user: str, gauge: str):
        for data in self._delegation_data[user][gauge]:
            delegator = data.account
            if data.expire_time <= chain.time():
                self._delete_delegation_data(delegator, gauge, self._delegated_to[delegator][gauge])

    def get_adjusted_vecrv_balance(self, user: str, gauge: str, block_identifier: int):
        with brownie.multicall(block_identifier=block_identifier):
            vecrv_balance = self.voting_escrow.balanceOf(user)

        if self.is_killed:
            return vecrv_balance

        if (delegation_count := self.delegation_count[user]) != 0:
            is_global = False
            if delegation_count == 1:
                data = self._delegated_to[user][ZERO_ADDRESS]
                if data.expire_time > chain.time():
                    vecrv_balance = vecrv_balance * (10_000 - data.percentage) // 10_000
                    is_global = True

            if not is_global:
                data = self._delegated_to[user][gauge]
                if data.expire_time > chain.time():
                    vecrv_balance = vecrv_balance * (10_000 - data.percentage) // 10_000

        for target in set([gauge, ZERO_ADDRESS]):
            for data in self._delegation_data[user][target]:
                if data.expire_time > chain.time():
                    delegator = data.account
                    with brownie.multicall(block_identifier=block_identifier):
                        delegator_balance = self.voting_escrow.balanceOf(delegator)
                    vecrv_balance += delegator_balance * (10_000 - data.percentage) // 10_000

        return vecrv_balance

    def set_is_killed(self, killed: bool):
        self.is_killed = killed


class StateMachine:

    st_account = strategy("address")
    st_gauge = contract_strategy("LiquidityGauge")
    st_percentage = strategy("uint16")
    st_time = strategy("uint40")

    def __init__(cls, accounts, boost_delegation, gauges, voting_escrow) -> None:
        cls.accounts = accounts
        cls.boost_delegation = boost_delegation
        cls.gauges = gauges
        cls.voting_escrow = voting_escrow

    def setup(self):
        brownie.multicall.deploy({"from": self.accounts[0]})
        self._state = BoostDelegationLogic(self.voting_escrow)

    def initialize(self):
        self.boost_delegation.set_killed(True, {"from": self.boost_delegation.admin()})
        self._state.set_is_killed(True)

    def rule_delegate_boost(
        self,
        delegator="st_account",
        gauge="st_gauge",
        receiver="st_account",
        pct="st_percentage",
        cancel_time="st_time",
        expire_time="st_time",
        msg_sender="st_account",
    ):
        try:
            self._state.delegate_boost(
                delegator.address,
                gauge.address,
                receiver.address,
                pct,
                cancel_time,
                expire_time,
                {"from": msg_sender.address},
            )
        except AssertionError:
            with brownie.reverts():
                self.boost_delegation.delegate_boost(
                    delegator, gauge, receiver, pct, cancel_time, expire_time, {"from": msg_sender}
                )
        else:
            self.boost_delegation.delegate_boost(
                delegator, gauge, receiver, pct, cancel_time, expire_time, {"from": msg_sender}
            )

    def rule_set_operator(self, account="st_account", operator="st_account"):
        self._state.set_operator(operator.address, {"from": account.address})
        self.boost_delegation.set_operator(operator, {"from": account})

    def rule_cancel_delegation(
        self, delegator="st_account", gauge="st_gauge", msg_sender="st_account"
    ):
        try:
            self._state.cancel_delegation(
                delegator.address, gauge.address, {"from": msg_sender.address}
            )
        except AssertionError:
            with brownie.reverts():
                self.boost_delegation.cancel_delegation(delegator, gauge, {"from": msg_sender})
        else:
            self.boost_delegation.cancel_delegation(delegator, gauge, {"from": msg_sender})

    def rule_update_delegation_records(
        self, user="st_account", gauge="st_gauge", msg_sender="st_account"
    ):
        try:
            self._state.update_delegation_records(user.address, gauge.address)
        except AssertionError:
            with brownie.reverts():
                self.boost_delegation.update_delegation_records(user, gauge, {"from": msg_sender})
        else:
            self.boost_delegation.update_delegation_records(user, gauge, {"from": msg_sender})

    def invariant_delegation_data(self):
        collected_data = defaultdict(lambda: defaultdict(list))
        with brownie.multicall(block_identifier=chain.height):
            # batch all the calls into one using multicall
            for account, gauge, idx in it.product(self.accounts, self.gauges, range(10)):
                collected_data[account.address][gauge.address].append(
                    self.boost_delegation.get_delegation_data(account, gauge, idx)
                )

        for account, gauge, idx in it.product(self.accounts, self.gauges, range(10)):
            # then make assertions about the data
            on_chain_data = collected_data[account.address][gauge.address][idx]
            expected_data = self._state.get_delegation_data(account.address, gauge.address, idx)
            assert tuple(on_chain_data) == tuple(expected_data)

    def invariant_delegated_to(self):
        collected_data = defaultdict(lambda: defaultdict(lambda: Data()))
        with brownie.multicall(block_identifier=chain.height):
            for account, gauge in it.product(self.accounts, self.gauges):
                collected_data[account.address][
                    gauge.address
                ] = self.boost_delegation.get_delegated_to(account, gauge)

        for account, gauge in it.product(self.accounts, self.gauges):
            on_chain_data = collected_data[account.address][gauge.address]
            expected_data = self._state.get_delegated_to(account.address, gauge.address)
            assert tuple(on_chain_data) == tuple(expected_data)

    def invariant_adjusted_vecrv_balance(self):
        collected_data = defaultdict(lambda: defaultdict(lambda: 0))
        with brownie.multicall(block_identifier=chain.height):
            for account, gauge in it.product(self.accounts, self.gauges):
                collected_data[account.address][
                    gauge.address
                ] = self.boost_delegation.get_adjusted_vecrv_balance(account, gauge)

        for account, gauge in it.product(self.accounts, self.gauges):
            on_chain_data = collected_data[account.address][gauge.address]
            expected_data = self._state.get_adjusted_vecrv_balance(
                account.address, gauge.address, chain.height
            )
            assert math.isclose(on_chain_data, expected_data, rel_tol=0.00001)


def test_state_machine(
    state_machine,
    alice,
    accounts,
    boost_delegation,
    LiquidityGauge,
    crv,
    voting_escrow,
):
    total_accounts = len(accounts)
    total_crv = crv.balanceOf(alice)
    amount = total_crv // total_accounts
    # fund accounts to be used in the test
    for acct in accounts:
        crv.transfer(acct, amount, {"from": alice})
        crv.approve(voting_escrow, amount, {"from": acct})
        voting_escrow.create_lock(amount, chain.time() + 86400 * 365 * 4, {"from": acct})

    # deploy some mock gauges
    gauges = [LiquidityGauge.deploy({"from": alice}) for _ in range(5)]

    # because this is a simple state machine, we use more steps than normal
    settings = {"stateful_step_count": 25, "max_examples": 30}

    state_machine(
        StateMachine,
        accounts,
        boost_delegation,
        gauges,
        voting_escrow,
        settings=settings,
    )
