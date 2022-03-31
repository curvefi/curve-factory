object "ImplementationDeployer" {
    code {
        // copy to memory and deploy `PlainNBasic` implementation
        datacopy(0, dataoffset("Basic"), datasize("Basic"))
        pop(create(0, 0, datasize("Basic")))

        // copy to memory and deploy `PlainNBalances` implementation
        datacopy(0, dataoffset("Balances"), datasize("Balances"))
        pop(create(0, 0, datasize("Balances")))

        // copy to memory and deploy `PlainNETH` implementation
        datacopy(0, dataoffset("Native"), datasize("Native"))
        pop(create(0, 0, datasize("Native")))

        // copy to memory and deploy `PlainNOptimized` implementation
        datacopy(0, dataoffset("Optimized"), datasize("Optimized"))
        pop(create(0, 0, datasize("Optimized")))

        // self destruct + return
        selfdestruct(caller())
        return(0, 0)
    }

    // Implementations' deployment bytecode will be placed here
    data "Basic" hex"3D80F3"
    data "Balances" hex"3D80F3"
    data "Native" hex"3D80F3"
    data "Optimized" hex"3D80F3"
}
