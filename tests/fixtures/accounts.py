import pytest

transfer_amt = (1_000_000_000 - 1_000_000) * 10 ** 18


@pytest.fixture(scope="session")
def eth_holder(accounts):
    return accounts[9]


@pytest.fixture(scope="session")
def alice(accounts, eth_holder):
    accounts[0].transfer(eth_holder, transfer_amt)
    return accounts[0]


@pytest.fixture(scope="session")
def bob(accounts, eth_holder):
    accounts[1].transfer(eth_holder, transfer_amt)
    return accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts, eth_holder):
    accounts[2].transfer(eth_holder, accounts[2].balance())
    return accounts[2]


@pytest.fixture(scope="session")
def dave(accounts, eth_holder):
    accounts[3].transfer(eth_holder, transfer_amt)
    return accounts[3]


@pytest.fixture(scope="session")
def erin(accounts, eth_holder):
    accounts[4].transfer(eth_holder, transfer_amt)
    return accounts[4]


@pytest.fixture(scope="session")
def frank(accounts, eth_holder):
    accounts[5].transfer(eth_holder, transfer_amt)
    return accounts[5]


@pytest.fixture(scope="session")
def fee_receiver(frank):
    return frank
