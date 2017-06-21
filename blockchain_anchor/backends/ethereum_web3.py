import json

import logging
import requests
from web3 import Web3, KeepAliveRPCProvider, IPCProvider

from blockchain_anchor.backends import BlockchainIntegration


class EthereumIntegration(BlockchainIntegration):
    _op_count = 0
    _gas = 0
    _gas_price = 0
    _base_data = {"jsonrpc": "2.0"}

    def __init__(self, eth_acct, eth_acct_secret, ipc_path):
        super().__init__("Ethereum")
        self._eth_acct = eth_acct
        self._eth_acct_secret = eth_acct_secret
        self._web3 = Web3(
            IPCProvider(ipc_path=ipc_path))

    def test_connection(self):
        super().test_connection()
        return self._web3.isConnected()

    def embed(self, hex_data):
        super().embed(hex_data)

        data = {
            "from": self._eth_acct,
            "value": "0x0",
            "data": hex_data
        }
        tx_hash = self._web3.personal.signAndSendTransaction(data, self._eth_acct_secret)
        logging.debug("Embedded data %s into TX %s", hex_data, tx_hash)
        return tx_hash

    def confirm(self, tx_hash):
        super().confirm(tx_hash)
        receipt = self._web3.eth.getTransactionReceipt(tx_hash)
        if receipt is not None and "blockHash" in receipt:
            block_hash_ = receipt["blockHash"]
            if block_hash_.startswith("0x"):
                block_hash_ = block_hash_[2:]
            return block_hash_
        else:
            return None

