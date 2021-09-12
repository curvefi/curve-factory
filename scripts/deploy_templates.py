"""
Deploy gauge extension and metapool implementation contracts.

Constants should be set here for substitution in the contracts.
"""


from brownie import (
    ZERO_ADDRESS,
    GaugeExtension,
    MetaBalances,
    MetaStandard,
    accounts,
    compile_source,
)

DEPLOYER = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)


# CHANGE PRIOR TO DEPLOYMENT

BASE_GAUGE = ZERO_ADDRESS
FACTORY = ZERO_ADDRESS

BASE_POOL = ZERO_ADDRESS
BASE_COINS = [
    ZERO_ADDRESS,
    ZERO_ADDRESS,
    ZERO_ADDRESS,
]
BASE_LP_TOKEN = ZERO_ADDRESS
GAUGE_EXTENSION_IMPL = None  # change this if one is already deployed


def deploy_gauge_extension(_base_gauge: str, _factory: str):
    source = GaugeExtension._build["source"]
    for addr in [_base_gauge, _factory]:
        source = source.replace(ZERO_ADDRESS, addr, 1)

    MetaGaugeExtension = compile_source(source).Vyper
    return MetaGaugeExtension.deploy({"from": DEPLOYER})


def deploy_meta_implementation(_implementation_source: str):
    # use the global variable
    global GAUGE_EXTENSION_IMPL

    if GAUGE_EXTENSION_IMPL is None:
        GAUGE_EXTENSION_IMPL = deploy_gauge_extension(BASE_GAUGE, FACTORY).address

    source = _implementation_source
    for addr in [BASE_POOL, BASE_LP_TOKEN, BASE_GAUGE, GAUGE_EXTENSION_IMPL]:
        source = source.replace(ZERO_ADDRESS, addr, 1)
    source = source.replace("69", str(len(BASE_COINS)), 1)
    source = source.replace(f"[{', '.join([ZERO_ADDRESS] * 69)}]", f"[{', '.join(BASE_COINS)}]")

    META = compile_source(source).Vyper
    meta = META.deploy({"from": DEPLOYER})
    return meta.address, GAUGE_EXTENSION_IMPL


def main():
    with open("deployments.txt", "a") as f:
        f.write(f"Base Pool Templates - {BASE_POOL}\n")

    for implementation in [MetaStandard, MetaBalances]:
        source = implementation._build["source"]
        meta_impl, gauge_extension_impl = deploy_meta_implementation(source)
        print(f"{implementation._name} deployed at - {meta_impl}")
        print(f"Gauge Extension - {gauge_extension_impl}")

        with open("deployments.txt", "a") as f:
            f.write(f"{implementation._name} deployed at - {meta_impl}\n")
    with open("deployments.txt", "a") as f:
        f.write(f"Gauge Extension - {gauge_extension_impl}\n")
