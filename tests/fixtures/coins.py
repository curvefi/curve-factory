import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS, ERC20Mock, ERC20MockNoReturn
from brownie_tokens import MintableForkToken, ERC20

# public fixtures - these can be used when testing


@pytest.fixture(scope="module")
def wrapped_coins(project, alice, pool_data, _underlying_coins, is_forked, ATokenMock, AaveLendingPoolMock):
    return _wrapped(project, alice, pool_data, _underlying_coins, is_forked, ATokenMock, AaveLendingPoolMock)


@pytest.fixture(scope="module")
def underlying_coins(_underlying_coins):
    return _underlying_coins


@pytest.fixture(scope="module")
def meta_coin(_underlying_coins):
    return _underlying_coins[0]


@pytest.fixture(scope="module")
def base_lp_token(wrapped_coins):
    return wrapped_coins[1]


def _wrapped(project, alice, pool_data, underlying_coins, is_forked, ATokenMock, AaveLendingPoolMock):
    coins = []

    if pool_data["type"] == "plain":
        return underlying_coins

    if is_forked:
        for coin_data in pool_data["coins"]:
            coins.append(MintableForkToken(coin_data["underlying_address"]))
    else:
        if pool_data["rebase"]:
            aave_lending_pool_mock = AaveLendingPoolMock.deploy({"from": alice})
            erc20_mock = ERC20Mock.deploy("ERC20MOCK", "MOK", 18, {"from": alice})
            coins.append(ATokenMock.deploy("Rebase Mock", "MOK", 18, erc20_mock, aave_lending_pool_mock, {"from": alice}))
        else:
            for coin_data in pool_data["coins"]:
                if coin_data["tethered"]:
                    coins.append(ERC20MockNoReturn.deploy(coin_data["name"], "MOK", coin_data["decimals"], {"from": alice}))
                else:
                    coins.append(ERC20Mock.deploy(coin_data["name"], "MOK", coin_data["decimals"], {"from": alice}))
    return coins


def _underlying(alice, project, pool_data, is_forked, ATokenMock, AaveLendingPoolMock):
    coins = []

    if is_forked:
        if pool_data["type"] == "meta":
            meta_coin = pool_data["coins"][0]["underlying_address"]
            coins.append(MintableForkToken(meta_coin))
            for coin_data in pool_data["base_coins"]:
                coins.append(MintableForkToken(coin_data["underlying_address"]))
        else:
            pool_coins = pool_data.get("coins", [])
            for coin_data in pool_coins:
                coins.append(MintableForkToken(coin_data["underlying_address"]))
            if len(coins) == 0:
                for i in range(pool_data["n_coins"]):
                    coins.append(ERC20(18))
    else:
        if pool_data["type"] == "meta":
            if pool_data["rebase"]:
                # we deploy a rebase token to use in the metapool
                aave_lending_pool_mock = AaveLendingPoolMock.deploy({"from": alice})
                erc20_mock = ERC20Mock.deploy("ERC20MOCK", "MOK", 18, {"from": alice})
                coins.append(ATokenMock.deploy("Rebase Mock", "MOK", 18, erc20_mock, aave_lending_pool_mock, {"from": alice}))
            else:
                meta_coin = pool_data["coins"][0]
                if meta_coin["tethered"]:
                    coins.append(ERC20MockNoReturn.deploy(meta_coin["name"], "MOK", meta_coin["decimals"], {"from": alice}))
                else:
                    coins.append(ERC20Mock.deploy(meta_coin["name"], "MOK", meta_coin["decimals"], {"from": alice}))
            for coin_data in pool_data["base_coins"]:
                if coin_data["tethered"]:
                    coins.append(ERC20MockNoReturn.deploy(coin_data["name"], "MOK", coin_data["decimals"], {"from": alice}))
                else:
                    coins.append(ERC20Mock.deploy(coin_data["name"], "MOK", coin_data["decimals"], {"from": alice}))

        elif pool_data["type"] == "plain":
            for i, coin_data in enumerate(pool_data["coins"]):
                if coin_data.get("underlying_address") == ETH_ADDRESS:
                    coins.append(ETH_ADDRESS)
                    continue
                decimals = coin_data["decimals"]
                deployer = ERC20MockNoReturn if coin_data["tethered"] else ERC20Mock
                contract = deployer.deploy(
                    f"Underlying Coin {i}", f"UC{i}", decimals, {"from": alice}
                )
                coins.append(contract)
            if not len(coins):
                for i in range(pool_data["n_coins"]):
                    contract = ERC20Mock.deploy(f"Underlying Coin {i}", f"UC{i}", 18, {"from": alice})
                    coins.append(contract)
            # deploy mock tokens
    return coins


@pytest.fixture(scope="module")
def base_coins(alice, pool_data, is_forked, base_pool_data):
    coins = []
    assert pool_data["type"] == "meta"

    if is_forked:
        for coin_data in pool_data["base_coins"]:
            coins.append(MintableForkToken(coin_data["underlying_address"]))
    else:
        for coin_data in pool_data["base_coins"]:
            coins.append(ERC20(pool_data["decimals"]))
    return coins


@pytest.fixture(scope="module")
def coin(underlying_coins):
    return underlying_coins[0]


# private fixtures - do not use in testing

@pytest.fixture(scope="module")
def _underlying_coins(alice, project, pool_data, is_forked, ATokenMock, AaveLendingPoolMock):
    return _underlying(alice, project, pool_data, is_forked, ATokenMock, AaveLendingPoolMock)
