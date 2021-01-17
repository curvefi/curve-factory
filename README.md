# curve-factory

Permissionless deployment of Curve metapools.

## Overview

The metapool factory has several core components:

* [`Factory`](contracts/Factory.vy) is the main contract used to deploy new metapools. It also acts a registry for finding the deployed pools and querying information about them.
* New pools are deployed via a proxy contract. The [implementation contract](contracts/MetaImplementationUSD.vy) targetted by the proxy is determined according to the base pool. This is the same technique used to create pools in Uniswap V1.
* [Deposit contracts](contracts/DepositZapUSD.vy) ("zaps") are used for wrapping and unwrapping underlying assets when depositing into or withdrawing from pools.

See the [documentation](https://curve.readthedocs.io/factory-overview.html) for more detailed information.

### Dependencies

* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev
* [brownie](https://github.com/eth-brownie/brownie) - tested with version [1.13.0](https://github.com/eth-brownie/brownie/releases/tag/v1.13.0)
* [brownie-token-tester](https://github.com/iamdefinitelyahuman/brownie-token-tester)
* [ganache-cli](https://github.com/trufflesuite/ganache-cli) - tested with version [6.12.1](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.12.1)

### Testing

Testing is performed in a forked mainnet environment.

To run the unit tests:

```bash
brownie test
```

You can optionally include the following flags:

* `--decimals`: The number of decimal places for the token used to test the factory pool. Default is 18.
* `--return_value`: The return value given by the token used to test the factory pool. Valid options are `True` and `None`.

### Deployment

To deploy the contracts, first modify the [`deployment script`](scripts/deploy.py) to unlock the account you wish to deploy from. Then:

```bash
brownie run deploy --network mainnet
```

### License

(c) Curve.Fi, 2020 - [All rights reserved](LICENSE).
