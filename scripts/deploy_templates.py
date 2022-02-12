"""
Deploy gauge extension and metapool implementation contracts.

Constants should be set here for substitution in the contracts.
"""
from pathlib import Path

from brownie import ZERO_ADDRESS, MetaBalances, MetaStandard, accounts, compile_source

DEPLOYER = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)

# where we will store the modified source files
Path("tmp").mkdir(parents=True, exist_ok=True)


# CHANGE PRIOR TO DEPLOYMENT

FACTORY = ZERO_ADDRESS

BASE_POOL = ZERO_ADDRESS
BASE_COINS = [
    ZERO_ADDRESS,
    ZERO_ADDRESS,
    ZERO_ADDRESS,
]
BASE_LP_TOKEN = ZERO_ADDRESS


def deploy_meta_implementation(_implementation_source: str):

    source = _implementation_source
    source = source.replace("69", str(len(BASE_COINS)), 1)
    source = source.replace(f"[{', '.join([ZERO_ADDRESS] * 69)}]", f"[{', '.join(BASE_COINS)}]")
    for addr in [BASE_POOL, BASE_LP_TOKEN]:
        source = source.replace(f"= {ZERO_ADDRESS}", f"= {addr}", 1)

    META = compile_source(source).Vyper
    meta = META.deploy({"from": DEPLOYER})

    with open(f"tmp/{meta.address}", "w") as f:
        f.write(source)

    return meta.address


def main():
    with open("tmp/deployments.txt", "a") as f:
        f.write(f"Base Pool Templates - {BASE_POOL}\n")

    for implementation in [MetaStandard, MetaBalances]:
        source = implementation._build["source"]
        meta_impl = deploy_meta_implementation(source)

        with open("tmp/deployments.txt", "a") as f:
            f.write(f"{implementation._name} deployed at - {meta_impl}\n")
