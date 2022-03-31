import json

import rlp
import solcx
from brownie import ZERO_ADDRESS, FactorySidechains, ProxyAdmin, Recover, accounts, project, web3
from hexbytes import HexBytes

with open("contracts/deployers/ImplementationDeployer.yul") as f:
    template = f.read()

with open("contracts/deployers/FactoryDeployer.yul") as f:
    factory_deployer_src = f.read()


def replace_constants(src, replacements):
    for r in replacements:
        src = src.replace("3D80F3", r, 1)
    return src


def generate_deploy_code(pool_size):
    input_data = {
        "language": "Yul",
        "sources": {
            "Deployer": {
                "content": replace_constants(
                    template,
                    [
                        getattr(project.CurveFactoryProject, f"Plain{pool_size}Basic").bytecode[2:],
                        getattr(project.CurveFactoryProject, f"Plain{pool_size}Balances").bytecode[
                            2:
                        ],
                        getattr(project.CurveFactoryProject, f"Plain{pool_size}ETH").bytecode[2:],
                        getattr(project.CurveFactoryProject, f"Plain{pool_size}Optimized").bytecode[
                            2:
                        ],
                    ],
                )
            }
        },
        "settings": {"outputSelection": {"*": {"*": ["evm.bytecode.object"]}}},
    }
    return solcx.compile_standard(input_data)["contracts"]["Deployer"]["ImplementationDeployer"][
        "evm"
    ]["bytecode"]["object"]


def create_raw_tx(recovery, code):
    tx = {
        "nonce": "0x",
        "gasPrice": 100 * 10 ** 9,
        "gasLimit": int(accounts[0].estimate_gas(data=code) * 1.1),
        "to": "0x",
        "value": "0x",
        "data": code,
        "v": 27,
        "r": 0x1234567890ABCDEF,
        "s": 0x1234567890ABCDEF,
    }

    sighash = web3.keccak(rlp.encode([HexBytes(v) for k, v in tx.items() if k not in "vrs"]))

    while (sender := recovery.ecr(sighash, tx["v"], tx["r"], tx["s"])) == ZERO_ADDRESS:
        tx["r"] += 1
    serialized = rlp.encode(list(map(HexBytes, tx.values()))).hex()
    total_cost = 100 * 10 ** 9 * tx["gasLimit"]
    return sender, serialized, total_cost


def main():
    recovery = Recover.deploy({"from": accounts[0]})

    data = {}

    for i in range(2, 5):
        origin, raw, total_cost = create_raw_tx(recovery, generate_deploy_code(i))
        root = accounts.at(accounts.at(origin, force=True).get_deployment_address(0), force=True)
        contract_addrs = [root.get_deployment_address(i) for i in range(1, 5)]

        data[i] = {
            "origin": origin,
            "raw_tx": raw,
            "total_cost": total_cost,
            "contracts": contract_addrs,
        }

    input_data = {
        "language": "Yul",
        "sources": {
            "Deployer": {
                "content": replace_constants(
                    factory_deployer_src,
                    [
                        ProxyAdmin.deploy.encode_input(
                            [
                                "0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a",
                                "0xbabe61887f1de2713c6f97e567623453d3C79f67",
                            ]
                        )[2:],
                        FactorySidechains.bytecode[2:],
                        "".join(["00" * 12 + c[2:] for c in data[2]["contracts"]]),
                        "".join(["00" * 12 + c[2:] for c in data[3]["contracts"]]),
                        "".join(["00" * 12 + c[2:] for c in data[4]["contracts"]]),
                    ],
                )
            }
        },
        "settings": {"outputSelection": {"*": {"*": ["evm.bytecode.object"]}}},
    }
    code = solcx.compile_standard(input_data)["contracts"]["Deployer"]["FactoryDeployer"]["evm"][
        "bytecode"
    ]["object"]

    origin, raw, total_cost = create_raw_tx(recovery, code)
    root = accounts.at(accounts.at(origin, force=True).get_deployment_address(0), force=True)
    contract_addrs = [root.get_deployment_address(i) for i in range(1, 3)]

    data["factory"] = {
        "origin": origin,
        "raw_tx": raw,
        "total_cost": total_cost,
        "contracts": contract_addrs,
    }

    with open("data.json", "w") as f:
        json.dump(data, f)
