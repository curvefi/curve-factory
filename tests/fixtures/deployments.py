import pytest
from brownie import (
    Contract,
    ZERO_ADDRESS,
    Factory,
    MetaImplementationBTC,
    MetaImplementationRebaseBTC,
    MetaImplementationUSD,
    MetaImplementationRebaseUSD,
    PlainPoolImplementation,
)

implementations = {
    "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714": [
        MetaImplementationBTC,
        MetaImplementationRebaseBTC,
    ],
    "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7": [
        MetaImplementationUSD,
        MetaImplementationRebaseUSD,
    ],
    ZERO_ADDRESS: [PlainPoolImplementation],
}


def _swap(
    project,
    alice,
    underlying,
    wrapped,
    pool_data,
    meta_coin,
    underlying_decimals,
    wrapped_decimals,
    factory,
    base_pool,
    name="MOCK-SWAP",
    symbol="MOK",
):
    deploy_func = (
        "deploy_metapool" if pool_data["type"] == "meta" else "deploy_plain_pool"
    )
    abi = next(
        i["inputs"]
        for i in Factory.abi
        if i["name"] == deploy_func
    )

    if len(wrapped) < 4:
        wrapped = wrapped + (4 - len(wrapped)) * [ZERO_ADDRESS]

    if len(underlying_decimals) < 4:
        underlying_decimals = underlying_decimals + (4 - len(underlying_decimals)) * [
            ZERO_ADDRESS
        ]

    # This is a bit hacky and needs to be changed once there are more than two
    # possible implementations (non-rebase/rebase) per pool type.
    # With the current set up, rebase implementations are always at index 1
    impl_id = int(pool_data["rebase"])
    base_address = base_pool.address if hasattr(base_pool, "address") else ZERO_ADDRESS

    args = {
        "_base_pool": base_address,
        "_name": name,
        "_symbol": symbol,
        "_coin": meta_coin,
        "_coins": wrapped,
        "_decimals": underlying_decimals,
        "_A": 200,
        "_fee": 4000000,
        "_implementation_idx": impl_id,
    }

    init_args = [args[i["name"]] for i in abi] + [({"from": alice})]

    # contract = deployer.deploy({"from": alice})
    # contract.initialize(*init_args)

    tx = None
    if pool_data["type"] == "meta":
        tx = factory.deploy_metapool(*init_args)
    else:
        tx = factory.deploy_plain_pool(*init_args)

    implementation = implementations[base_address][impl_id]
    contract = implementation.at(tx.return_value)

    for coin in [i for i in wrapped if hasattr(i, "_set_pool")]:
        # required for aTokens
        coin._set_pool(contract)

    return contract


@pytest.fixture(scope="module")
def swap(
    project,
    alice,
    _underlying_coins,
    wrapped_coins,
    pool_data,
    meta_coin,
    underlying_decimals,
    wrapped_decimals,
    factory,
    base_pool,
):
    return _swap(
        project,
        alice,
        _underlying_coins,
        wrapped_coins,
        pool_data,
        meta_coin,
        underlying_decimals,
        wrapped_decimals,
        factory,
        base_pool,
        pool_data.get("name", None),
        pool_data.get("symbol", None),
    )
