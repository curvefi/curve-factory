from brownie import accounts, project, FactorySidechains, ProxyAdmin, ZERO_ADDRESS, history

from itertools import product
from collections import defaultdict


def main():
    dev = accounts.load("dev")
    accounts[0].transfer(dev, 1e19)
    
    implementations = defaultdict(list)
    
    for size, variant in product(range(2, 5), ["Basic", "Balances", "ETH", "Optimized"]):
        Implementation = getattr(project.CurveFactoryProject, f"Plain{size}{variant}")
        implementations[size].append(Implementation.deploy({"from": dev, "priority_fee": "auto"}))

    proxy = ProxyAdmin.deploy(["0xbabe61887f1de2713c6f97e567623453d3C79f67", dev], {"from": dev, "priority_fee": "auto"})
    factory = FactorySidechains.deploy(proxy, {"from": dev, "priority_fee": "auto"})

    for size, implementations in implementations.items():
        factory.set_plain_implementations(size, implementations + [ZERO_ADDRESS] * 6, {"from": dev, "priority_fee": "auto"})

    factory.commit_transfer_ownership(proxy, {"from": dev, "priority_fee": "auto"})

    print(sum([(tx.gas_price + tx.priority_fee) * int(tx.gas_used * 1.1) for tx in history[1:]]) / 1e18)
