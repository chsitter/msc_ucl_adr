import logging

import time

from blockchain_anchor.backends.bitcoin_bitcoind import BitcoinIntegration
from blockchain_anchor.backends.ethereum_web3 import EthereumIntegration

if __name__ == "__main__":
    # "user": "dummy",
    # "secret": "dummy_pass",
    # "host": "localhost",
    # "port": 8079,

    # ,
    #               "0xdd275fcd58e199d6ced00ca9f1eada83fec94ad3",
    #               "0x{}".format(merkle_tree.get_merkle_root()),
    #               lambda receipt: result_cb(backend, receipt))
    logging.basicConfig(level=logging.DEBUG)

    eth_bc = EthereumIntegration("0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59", "password", "/Users/chsitter/Documents/UCL/msc/project/ethereum_testnet/geth.ipc")
    btc_bc = BitcoinIntegration("localhost", "18332", "bitcoinrpc", "c8805869db20730a2ddb7f62cfa2745c", "mqCnowcw6K24bqD4Xcio3iync1ziWXEqio")
    print(eth_bc.test_connection())
    print(btc_bc.test_connection())
    tx_hash_eth = eth_bc.embed("0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675")
    tx_hash_btc = btc_bc.embed("0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675")

    while 1:
        print(eth_bc.confirm(tx_hash_eth))
        print(btc_bc.confirm(tx_hash_btc))
        time.sleep(10)
