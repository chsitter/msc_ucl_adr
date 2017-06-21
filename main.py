import logging

import time

import merkletools

import blockchain_anchor
from blockchain_anchor import chainpoint_util
from blockchain_anchor.backends.bitcoin_bitcoind import BitcoinIntegration
from blockchain_anchor.backends.ethereum_web3 import EthereumIntegration
from blockchain_anchor.strategies import AllAnchorStrategy

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting up!")

    config = {
        "backends": {
            "Ethereum": (EthereumIntegration,
                         {
                             "eth_acct": "0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59",
                             "eth_acct_secret": "password",
                             "ipc_path": "/Users/chsitter/Documents/UCL/msc/project/ethereum_testnet/geth.ipc"
                         }),
            "Bitcoin": (BitcoinIntegration,
                        {
                            "user": "bitcoinrpc",
                            "secret": "c8805869db20730a2ddb7f62cfa2745c",
                            "host": "localhost",
                            "port": 18332,
                            "change_addr": "mqCnowcw6K24bqD4Xcio3iync1ziWXEqio"
                        })
        },
        "strategies": {
            "all": AllAnchorStrategy,
        }
    }

    mt = merkletools.MerkleTools()
    mt.add_leaf(["Foo", "Bar", "Baz"], True)
    mt.make_tree()
    merkle_root = "0x{}".format(mt.get_merkle_root())

    anchor = blockchain_anchor.init_anchor(config, "all")
    anchor.anchor(merkle_root)

    while True:
        anchors = anchor.confirm(merkle_root)
        if anchors is not None:
                print(chainpoint_util.build_v2_receipt(mt, anchors))
        time.sleep(1)
