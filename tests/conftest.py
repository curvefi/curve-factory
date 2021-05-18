import pytest
from brownie import Contract, ZERO_ADDRESS
from brownie_tokens import ERC20, MintableForkToken

from pathlib import Path

from brownie._config import CONFIG
from brownie.project.main import get_loaded_projects

import json

pytest_plugins = [
    "fixtures.coins",
    "fixtures.deployments",
    "fixtures.accounts",
    "fixtures.factory",
    "fixtures.pooldata",
]


_pooldata = {}


def pytest_addoption(parser):
    parser.addoption("--meta", action="store_true", help="only run metapool tests")
    parser.addoption("--plain", action="store_true", help="only run plain pool tests")
    parser.addoption("--rebase", action="store_true", help="only run tests with rebase tokens")
    parser.addoption("--pool", help="only run tests for this metapool", type=str)
    parser.addoption("--n-coins", help="only run tests for a plain pool with this many coins", type=int, choices=[2,3,4])


def pytest_sessionstart():
    # load `testconf.json` for each pool
    project = get_loaded_projects()[0]
    for path in [i for i in project._path.glob("contracts/implementations/*") if i.is_dir()]:
        with path.joinpath("testconf.json").open() as fp:
            _pooldata[path.name] = json.load(fp)
            _pooldata[path.name].update(
                name=path.name, swap_contract=next(i.stem for i in path.glob("*.vy"))
            )
            #zap_contract = next((i.stem for i in path.glob("Deposit*")), None)
            #if zap_contract:
            #    _pooldata[path.name]["zap_contract"] = zap_contract


def pytest_generate_tests(metafunc):
    # Generate (multiple) parametrized calls to a test function
    project = get_loaded_projects()[0]
    if "pool_data" in metafunc.fixturenames:
        # parametrize `pool_data`
        metapools = ["meta-btc", "meta-btc-rebase", "meta-usd", "meta-usd-rebase"]
        test_path = Path(metafunc.definition.fspath).relative_to(project._path)
        if test_path.parts[1] in ("common", "meta", "plain"):
            if metafunc.config.getoption("meta"):
                pool = metafunc.config.getoption("pool")
                if metafunc.config.getoption("rebase"):
                    params = ["meta-btc-rebase", "meta-usd-rebase"]
                elif pool in metapools:
                    params = [pool]
                else:
                    params = metapools

            elif metafunc.config.getoption("plain"):
                if metafunc.config.getoption("n_coins"):
                    n_coins = metafunc.config.getoption("n_coins")
                    assert 2 <= n_coins <= 4
                    params = ["plain-"+str(n_coins)]
                else:
                    params = ["plain-2"]
            else:
                params = list(_pooldata)
        else:
            params = ["meta-usd"]

        metafunc.parametrize("pool_data", params, indirect=True, scope="session")


def pytest_collection_modifyitems(config, items):
    for item in items.copy():
        try:
            params = item.callspec.params
            data = _pooldata[params["pool_data"]]
        except Exception:
            continue


        # apply `skip_rebase` marker
        for marker in item.iter_markers(name="skip_rebase"):
            if data["rebase"]:
                items.remove(item)
                break

        if item not in items:
            continue

        # apply `skip_pool_type` marker
        for marker in item.iter_markers(name="skip_pool_type"):
            if len(set(data.get("type", [])) & set(marker.args)):
                items.remove(item)
                break

        if item not in items:
            continue


def pytest_ignore_collect(path, config):
    # Return True to prevent considering this path for collection
    project = get_loaded_projects()[0]
    path = Path(path).relative_to(project._path)
    path_parts = path.parts[1:-1]
    if path.is_dir():
        return None

    if path_parts == ():
        return None

    # always collect fixtures
    if path_parts[:1] == ("fixtures",):
        return None

    # with the `--meta` flag, skip any tests NOT in a `meta` subdirectory
    if config.getoption("meta") and "plain" in path_parts:
        return True

    # with the `--plain` flag, skip any tests NOT in a `plain` subdirectory
    if config.getoption("plain") and "meta" in path_parts:
        return True

    if config.getoption("meta") and path_parts:
        # with a specific pool targeted, only run pool and common tests
        if path_parts[0] not in ("meta", "common"):
            return True

    if config.getoption("pool") and path_parts:
        # with `--pool` ensure that `--meta` is set
        if path_parts[0] not in ("meta", "common"):
            return True

    if config.getoption("plain") and path_parts:
        # with a specific pool targeted, only run pool and common tests
        if path_parts[0] not in ("plain", "common"):
            return True

    if config.getoption("n_coins") and path_parts:
        # with `--n-coins` ensure that `--plain` is set
        if path_parts[0] not in ("plain", "common"):
            return True

    # always run common tests
    if path_parts[0] == "common":
        return None



# main parametrized fixture, used to pass data about each pool into the other fixtures
@pytest.fixture(scope="module")
def pool_data(request):
    project = get_loaded_projects()[0]

    if hasattr(request, "param"):
        impl_data = request.param
    else:
        test_path = Path(request.fspath).relative_to(project._path)
        impl_data = test_path.parts[1]


    return _pooldata[impl_data]


@pytest.fixture(scope="module")
def base_pool_data(pool_data):
    return pool_data.get("base_pool", None)


@pytest.fixture(scope="session")
def project():
    yield get_loaded_projects()[0]


@pytest.fixture(scope="session")
def is_forked():
    yield "fork" in CONFIG.active_network["id"]


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass

@pytest.fixture()
def new_factory(Factory, alice):
    contract = Factory.deploy({'from': alice})
    yield contract


@pytest.fixture(scope="module")
def swap_plain(PlainPoolImplementation, alice, factory, plain_coins):
    tx = factory.deploy_plain_pool("Test Plain", "PLN", plain_coins, 200, 4000000, 0, {'from': alice})
    yield PlainPoolImplementation.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_btc(MetaImplementationBTC, alice, base_pool_btc, factory, coin):
    tx = factory.deploy_metapool(base_pool_btc, "Test Swap BTC", "TSTB", coin, 200, 4000000, 0, {'from': alice})
    yield MetaImplementationBTC.at(tx.return_value)


@pytest.fixture(scope="module")
def rebase_coin(alice, ATokenMock, AaveLendingPoolMock, ERC20Mock):
    aave_lending_pool_mock = AaveLendingPoolMock.deploy({"from": alice})
    erc20_mock = ERC20Mock.deploy("ERC20MOCK", "ERC", 18, {"from": alice})
    yield ATokenMock.deploy("Rebase Mock",
                            "MOK",
                            18,
                            erc20_mock,
                            aave_lending_pool_mock,
                            {"from": alice})



@pytest.fixture(scope="module")
def swap_rebase(MetaImplementationRebaseUSD, alice, base_pool, factory, rebase_coin):
    tx = factory.deploy_metapool(base_pool, "Test Swap", "TST", rebase_coin, 200, 4000000, 1, {'from': alice})
    yield MetaImplementationRebaseUSD.at(tx.return_value)


@pytest.fixture(scope="module")
def swap_rebase_btc(MetaImplementationRebaseBTC, alice, base_pool, factory, rebase_coin):
    tx = factory.deploy_metapool(base_pool, "Test Swap", "TST", rebase_coin, 200, 4000000, 1, {'from': alice})
    yield MetaImplementationRebaseBTC.at(tx.return_value)


@pytest.fixture(scope="module")
def zap(DepositZapUSD, alice):
    yield DepositZapUSD.deploy({'from': alice})


@pytest.fixture(scope="module")
def base_pool(pool_data):
    pool = pool_data.get("base_pool", ZERO_ADDRESS)
    if pool != ZERO_ADDRESS:
        pool = Contract(pool)
        # ensure the base pool is balanced so our tests are deterministic
        decimals = [MintableForkToken(pool.coins(i)).decimals() for i in range(3)]
        max_balance = max([pool.balances(0) * 10**(18-decimals[0]), pool.balances(1) * 10**(18-decimals[1]), pool.balances(2) * 10**(18-decimals[2])])
        ideal_balances = [max_balance // 10**(18-decimals[0]), max_balance // 10**(18-decimals[1]), max_balance // 10**(18-decimals[2])]
        for i, amount in enumerate(ideal_balances):
            balance = pool.balances(i)
            if balance < amount:
                MintableForkToken(pool.coins(i))._mint_for_testing(pool, amount - balance)
        if hasattr(pool, "donate_admin_fees"):
            pool.donate_admin_fees({'from': pool.owner()})

    yield pool


@pytest.fixture(scope="module")
def base_pool_btc(alice, fee_receiver, implementation_btc, factory, implementation_rebase_btc):
    pool = Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")
    factory.add_base_pool(pool, fee_receiver, [implementation_btc, implementation_rebase_btc] + [ZERO_ADDRESS] * 8, {'from': alice})

    yield pool


@pytest.fixture(scope="module")
def plain_coins():
    yield [ERC20(decimals=7), ERC20(decimals=9), ZERO_ADDRESS, ZERO_ADDRESS]


@pytest.fixture(scope="module")
def plain_decimals(plain_coins):
    yield [i.decimals() if i != ZERO_ADDRESS else 0 for i in plain_coins]


@pytest.fixture
def set_fee_receiver(alice, fee_receiver, factory, swap):
    factory.set_fee_receiver(swap, fee_receiver, {"from": alice})


@pytest.fixture(scope="module")
def initial_amounts(wrapped_decimals, underlying_decimals, is_meta, base_pool):
    # 1e6 of each coin - used to make an even initial deposit in many test setups
    amounts = []
    if is_meta:
        amounts = [10**i * 1000000 for i in wrapped_decimals]
        amounts[1] = amounts[1] * 10**18 // base_pool.get_virtual_price()
    else:
        # plain pool
        amounts = [10**i * 1000000 for i in underlying_decimals]
    yield amounts


@pytest.fixture(scope="module")
def initial_amounts_underlying(underlying_decimals, is_meta):
    # 1e6 of each coin - used to make an even initial deposit in many test setups
    amounts = []
    amounts = [10**i * 1000000 for i in underlying_decimals]
    if is_meta:
        amounts[1:] = [i//3 for i in amounts[1:]]
    yield amounts


# shared logic for pool and base_pool setup fixtures

def _add_liquidity(acct, swap, amounts):
    swap.add_liquidity(amounts, 0, {'from': acct})


def _mint(acct, is_meta, wrapped_coins, wrapped_amounts, underlying_coins, underlying_amounts):
    if is_meta:
        for coin, amount in zip(wrapped_coins, wrapped_amounts):
            coin._mint_for_testing(acct, amount, {'from': acct})

    for coin, amount in zip(underlying_coins, underlying_amounts):
        if is_meta and coin == wrapped_coins[0]:
            continue
        coin._mint_for_testing(acct, amount, {'from': acct})


def _approve(owner, spender, *coins):
    for coin in set(x for i in coins for x in i):
        coin.approve(spender, 2**256-1, {'from': owner})


# pool setup fixtures

@pytest.fixture()
def add_initial_liquidity(alice, is_meta, mint_alice, approve_alice, swap, initial_amounts):
    # mint (10**7 * precision) of each coin in the pool
    _add_liquidity(alice, swap, initial_amounts)


@pytest.fixture()
def mint_bob(bob, is_meta, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(bob, is_meta, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_bob(bob, swap, underlying_coins, wrapped_coins):
    _approve(bob, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def mint_alice(alice, is_meta, underlying_coins, wrapped_coins, initial_amounts, initial_amounts_underlying):
    _mint(alice, is_meta, wrapped_coins, initial_amounts, underlying_coins, initial_amounts_underlying)


@pytest.fixture(scope="module")
def approve_alice(alice, swap, underlying_coins, wrapped_coins):
    _approve(alice, swap, underlying_coins, wrapped_coins)


@pytest.fixture()
def approve_zap(alice, bob, zap, swap, underlying_coins, initial_amounts_underlying):
    for underlying, amount in zip(underlying_coins, initial_amounts_underlying):
        if underlying == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            continue
        underlying.approve(zap, 2**256-1, {'from': alice})
        underlying.approve(zap, 2**256-1, {'from': bob})

    swap.approve(zap, 2**256-1, {'from': alice})
    swap.approve(zap, 2**256-1, {'from': bob})




### Added for rebase tokens

@pytest.fixture(scope="module")
def wrapped_rebase_coins(rebase_coin, base_lp_token):
    yield [rebase_coin, base_lp_token]


@pytest.fixture(scope="module")
def wrapped_rebase_decimals(wrapped_rebase_coins):
    yield [i.decimals() for i in wrapped_rebase_coins]


@pytest.fixture(scope="module")
def wrapped_rebase_amounts(base_pool, wrapped_coins, wrapped_decimals):
    wrapped_amounts = [10**i * 1000000 for i in wrapped_decimals]
    wrapped_amounts[1] = wrapped_amounts[1] * 10**18 // base_pool.get_virtual_price()
    yield wrapped_amounts


@pytest.fixture()
def mint_and_deposit(wrapped_rebase_coins, wrapped_rebase_amounts, alice, swap_rebase):
    for coin, amount in zip(wrapped_rebase_coins, wrapped_rebase_amounts):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(swap_rebase, amount, {"from": alice})
    swap_rebase.add_liquidity(wrapped_rebase_amounts, 0, {"from": alice})
