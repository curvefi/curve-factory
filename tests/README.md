## Factory Test Suite

The factory test suite provides a range of unit tests in fork mode to test all supported factory pool implementations.

The current factory supported pool implementations are:

- USD metapool (using [`3Pool`](https://etherscan.io/address/0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7))
- BTC metapool (using [`sBTC`](https://etherscan.io/address/0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714))
- USD metapool with a rebase token
- BTC metapool with a rebase token
- Plain pools with 2 coins (one of which may be ETH)

To run the full test suite, run:

```
brownie test
```

There are two different pool types supported by the factory:

- Metapools
- Plain pools

There is further support for:

- Rebase tokens in metapools (e.g. `aTokens`)
- ETH in plain pools

To run the full test suite targeting a specific pool type, run:

```
brownie test --plain
```

or

```
brownie test --meta
```

A factory plain pool may contain 2-4 coins, where one token may be ETH. To specify the number of tokens a plain pool should have for testing, run:

```
brownie test --plain --n-coins <number_of_coins>
```

_Note_: One must explicitly set the `--plain` flag when specifying `--n-coins`.

To explicitly target pools with a rebase token, run:

```
brownie test --rebase
```

For an in-depth explanation of how to use Brownie for testing, please refer to the official [Brownie docs](https://eth-brownie.readthedocs.io/en/stable/index.html).
