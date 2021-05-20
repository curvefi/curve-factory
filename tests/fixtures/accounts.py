import pytest


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def dave(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def fee_receiver(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[5]

