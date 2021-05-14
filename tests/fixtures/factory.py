import pytest

from brownie import Contract, ZERO_ADDRESS

@pytest.fixture(scope="module")
def implementation_usd(MetaImplementationUSD, alice):
    yield MetaImplementationUSD.deploy({'from': alice})


@pytest.fixture(scope="module")
def implementation_btc(MetaImplementationBTC, alice):
    yield MetaImplementationBTC.deploy({'from': alice})


@pytest.fixture(scope="module")
def implementation_plain(PlainPoolImplementation, alice):
    yield PlainPoolImplementation.deploy({'from': alice})


@pytest.fixture(scope="module")
def implementation_rebase_btc(MetaImplementationRebaseBTC, alice):
    yield MetaImplementationRebaseBTC.deploy({'from': alice})


@pytest.fixture(scope="module")
def implementation_rebase_usd(MetaImplementationRebaseUSD, alice):
    yield MetaImplementationRebaseUSD.deploy({'from': alice})


@pytest.fixture(scope="module")
def factory(Factory, alice, fee_receiver, base_pool, implementation_btc, implementation_rebase_btc, implementation_usd, implementation_rebase_usd, implementation_plain):
    contract = Factory.deploy({'from': alice})
    if base_pool != ZERO_ADDRESS:
        if base_pool.address == "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714":
            contract.add_base_pool(btc_base_pool, fee_receiver, [implementation_btc, implementation_rebase_btc] + [ZERO_ADDRESS] * 8, {'from': alice})
        else:
            contract.add_base_pool(base_pool, fee_receiver, [implementation_usd, implementation_rebase_usd] + [ZERO_ADDRESS] * 8, {'from': alice})
    contract.set_plain_implementations(2, [implementation_plain] + [ZERO_ADDRESS] * 9, {'from': alice})
    yield contract
