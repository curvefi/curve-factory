import pytest

transfer_amt = (1_000_000_000 - 1_000_000) * 10 ** 18


@pytest.fixture(scope="session")
def alice(accounts):
    accounts[0].transfer(accounts[-1], transfer_amt)
    return accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    accounts[1].transfer(accounts[-1], transfer_amt)
    return accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    accounts[2].transfer(accounts[-1], accounts[2].balance())
    return accounts[2]


@pytest.fixture(scope="session")
def dave(accounts):
    accounts[3].transfer(accounts[-1], transfer_amt)
    return accounts[3]


@pytest.fixture(scope="session")
def erin(accounts):
    accounts[4].transfer(accounts[-1], transfer_amt)
    return accounts[4]


@pytest.fixture(scope="session")
def frank(accounts):
    accounts[5].transfer(accounts[-1], transfer_amt)
    return accounts[5]


@pytest.fixture(scope="session")
def fee_receiver(frank):
    return frank
