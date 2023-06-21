import brownie
import pytest
from eip712.messages import EIP712Message

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(swap, alice, accounts, idx):
    assert swap.allowance(alice, accounts[idx]) == 0


def test_approve(swap, alice, bob):
    swap.approve(bob, 10 ** 19, {"from": alice})

    assert swap.allowance(alice, bob) == 10 ** 19


def test_modify_approve_zero_nonzero(swap, alice, bob):
    swap.approve(bob, 10 ** 19, {"from": alice})
    swap.approve(bob, 0, {"from": alice})
    swap.approve(bob, 12345678, {"from": alice})

    assert swap.allowance(alice, bob) == 12345678


def test_revoke_approve(swap, alice, bob):
    swap.approve(bob, 10 ** 19, {"from": alice})
    swap.approve(bob, 0, {"from": alice})

    assert swap.allowance(alice, bob) == 0


def test_approve_self(swap, alice, bob):
    swap.approve(alice, 10 ** 19, {"from": alice})

    assert swap.allowance(alice, alice) == 10 ** 19


def test_only_affects_target(swap, alice, bob):
    swap.approve(bob, 10 ** 19, {"from": alice})

    assert swap.allowance(bob, alice) == 0


def test_returns_true(swap, alice, bob):
    tx = swap.approve(bob, 10 ** 19, {"from": alice})

    assert tx.return_value is True


def test_approval_event_fires(alice, bob, swap):
    tx = swap.approve(bob, 10 ** 19, {"from": alice})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [alice, bob, 10 ** 19]


def test_infinite_approval(swap, alice, bob):
    swap.approve(bob, 2 ** 256 - 1, {"from": alice})
    swap.transferFrom(alice, bob, 10 ** 18, {"from": bob})

    assert swap.allowance(alice, bob) == 2 ** 256 - 1


def test_permit(accounts, bob, chain, swap, web3):

    alice = accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")

    class Permit(EIP712Message):
        # EIP-712 Domain Fields
        _name_: "string" = swap.name()  # noqa: F821
        _version_: "string" = swap.version()  # noqa: F821
        _chainId_: "uint256" = chain.id  # noqa: F821
        _verifyingContract_: "address" = swap.address  # noqa: F821

        # EIP-2612 Data Fields
        owner: "address"  # noqa: F821
        spender: "address"  # noqa: F821
        value: "uint256"  # noqa: F821
        nonce: "uint256"  # noqa: F821
        deadline: "uint256" = 2 ** 256 - 1  # noqa: F821

    permit = Permit(owner=alice.address, spender=bob.address, value=2 ** 256 - 1, nonce=0)
    sig = alice.sign_message(permit)

    tx = swap.permit(alice, bob, 2 ** 256 - 1, 2 ** 256 - 1, sig.v, sig.r, sig.s, {"from": bob})

    assert swap.allowance(alice, bob) == 2 ** 256 - 1
    assert tx.return_value is True
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [alice.address, bob, 2 ** 256 - 1]
    assert swap.nonces(alice) == 1


def test_permit_contract(accounts, bob, chain, swap, web3):

    src = """
@view
@external
def isValidSignature(_hash: bytes32, _sig: Bytes[65]) -> bytes32:
    return 0x1626ba7e00000000000000000000000000000000000000000000000000000000
    """
    mock_contract = brownie.compile_source(src, vyper_version="0.3.1").Vyper.deploy({"from": bob})
    alice = accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")

    class Permit(EIP712Message):
        # EIP-712 Domain Fields
        _name_: "string" = swap.name()  # noqa: F821
        _version_: "string" = swap.version()  # noqa: F821
        _chainId_: "uint256" = chain.id  # noqa: F821
        _verifyingContract_: "address" = swap.address  # noqa: F821

        # EIP-2612 Data Fields
        owner: "address"  # noqa: F821
        spender: "address"  # noqa: F821
        value: "uint256"  # noqa: F821
        nonce: "uint256"  # noqa: F821
        deadline: "uint256" = 2 ** 256 - 1  # noqa: F821

    permit = Permit(owner=alice.address, spender=bob.address, value=2 ** 256 - 1, nonce=0)
    sig = alice.sign_message(permit)

    tx = swap.permit(
        mock_contract, bob, 2 ** 256 - 1, 2 ** 256 - 1, sig.v, sig.r, sig.s, {"from": bob}
    )

    # make sure this is hit when owner is a contract
    assert tx.subcalls[-1]["function"] == "isValidSignature(bytes32,bytes)"
