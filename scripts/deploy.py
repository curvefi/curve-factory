from brownie import (
    DepositZapBTC,
    DepositZapUSD,
    Factory,
    MetaImplementationBTC,
    MetaImplementationUSD,
    OwnerProxy,
    accounts,
)
from brownie.network.gas.strategies import GasNowScalingStrategy

# modify me prior to deployment on mainnet!
DEPLOYER = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)

gas_price = GasNowScalingStrategy("slow", "fast")


OWNER_ADMIN = "0x40907540d8a6C65c637785e8f8B742ae6b0b9968"
PARAM_ADMIN = "0x4EEb3bA4f221cA16ed4A0cC7254E2E32DF948c5f"
EMERGENCY_ADMIN = "0x00669DF67E4827FCc0E48A1838a8d5AB79281909"

BASE_3POOL = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
BASE_SBTC = "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714"

FEE_RECEIVER_USD = "0xa464e6dcda8ac41e03616f95f4bc98a13b8922dc"
FEE_RECEIVER_BTC = "0xf9fc73496484290142ee856639f69e04465985cd"


def main(deployer=DEPLOYER):
    factory = Factory.deploy({"from": deployer})

    implementation_usd = MetaImplementationUSD.deploy({"from": deployer, "gas_price": gas_price})
    factory.add_base_pool(
        BASE_3POOL, implementation_usd, FEE_RECEIVER_USD, {"from": deployer, "gas_price": gas_price}
    )

    implementation_btc = MetaImplementationBTC.deploy({"from": deployer, "gas_price": gas_price})
    factory.add_base_pool(
        BASE_SBTC, implementation_btc, FEE_RECEIVER_BTC, {"from": deployer, "gas_price": gas_price}
    )

    proxy = OwnerProxy.deploy(
        OWNER_ADMIN, PARAM_ADMIN, EMERGENCY_ADMIN, {"from": deployer, "gas_price": gas_price}
    )

    factory.commit_transfer_ownership(proxy, {"from": deployer, "gas_price": gas_price})
    proxy.accept_transfer_ownership(factory, {"from": deployer, "gas_price": gas_price})

    DepositZapUSD.deploy({"from": deployer, "gas_price": gas_price})
    DepositZapBTC.deploy({"from": deployer, "gas_price": gas_price})
