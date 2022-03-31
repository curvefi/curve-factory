object "FactoryDeployer" {
    code {
        // copy to memory and deploy proxy admin
        datacopy(0, dataoffset("ProxyAdmin"), datasize("ProxyAdmin"))
        let proxy_admin := create(0, 0, datasize("ProxyAdmin"))
        
        // copy to memory and deploy factory
        let size := datasize("FactorySidechains")
        datacopy(0, dataoffset("FactorySidechains"), size)
        mstore(size, proxy_admin) // append constructor argument
        let factory := create(0, 0, add(size, 32))

        // commit transfer ownership to proxy admin
        mstore(0, shl(224, 0x6b441a40))
        mstore(4, proxy_admin)
        pop(call(gas(), factory, 0, 0, 36, 0, 0))
        
        // set plain implementations
        mstore(0, shl(224, 0x9ddbf4b9))

        // setup calldata for setting size 2 pool implementations
        mstore(4, 2)
        datacopy(36, dataoffset("Plain2"), 128)
        pop(call(gas(), factory, 0, 0, 164, 0, 0))

        // setup calldata for setting size 3 pool implementations
        mstore(4, 3)
        datacopy(36, dataoffset("Plain3"), 128)
        pop(call(gas(), factory, 0, 0, 164, 0, 0))

        // setup calldata for setting size 4 pool implementations
        mstore(4, 4)
        datacopy(36, dataoffset("Plain4"), 128)
        pop(call(gas(), factory, 0, 0, 164, 0, 0))

        // self destruct + return
        selfdestruct(caller())
        return(0, 0)
    }

    // deployment bytecodes
    data "ProxyAdmin" hex"3D80F3"
    data "FactorySidechains" hex"3D80F3"

    // calldata for setting pool implementations
    data "Plain2" hex"3D80F3"
    data "Plain3" hex"3D80F3"
    data "Plain4" hex"3D80F3"
}
