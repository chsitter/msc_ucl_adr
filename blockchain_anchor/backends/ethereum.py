import logging
import rlp
from ethereum import transactions
from web3 import Web3, HTTPProvider

from blockchain_anchor.backends import BlockchainIntegration


class EthereumIntegration(BlockchainIntegration):
    def __init__(self, privkey, account, web3_http_uri, gasprice=1000, startgas=100000):
        """

        :param name:        Name of this integration for use in Chainpoint receipt
        :param privkey:     private key to be used for tx signing or a callback function of the form fn(tx) -> tx
        :param gasprice:    gasprice for TX, default 1000
        :param startgas:    startgas for TX, default 10000
        """
        super().__init__("Ethereum")
        self._gasprice = gasprice
        self._startgas = startgas
        self._privkey = privkey
        self._account = "0x{}".format(account)
        self._web3 = Web3(HTTPProvider(web3_http_uri))

        # the nonce is defined to be the transaction count of the account
        # the problem here is that pending transactions aren't returned by getTransactionCount and we might want to add
        # eth.getBlock("pending", true).transactions to get them
        self._nonce = self._web3.eth.getTransactionCount(self._account)

    def anchor(self, hex_data):
        super().anchor(hex_data)

        tx = transactions.Transaction(self._nonce, self._gasprice, self._startgas, "", 0, hex_data)
        self._nonce += 1

        if callable(self._privkey):
            tx = self._privkey(tx)
        else:
            tx.sign(self._privkey)

        try:
            raw_tx = self._web3.toHex(rlp.encode(tx))
            result = self._web3.eth.sendRawTransaction(raw_tx)

            if result.startswith("0x"):
                result = result[2:]
        except ValueError as err:
            logging.error("Failed to send transaction: %s", err)
            result = None

        return result

    def confirm(self, tx_hash):
        super().confirm(tx_hash)
        try:
            if not tx_hash.startswith("0x"):
                tx_hash = "0x{}".format(tx_hash)
            receipt = self._web3.eth.getTransactionReceipt(tx_hash)
        except ValueError as err:
            logging.error("Failed getting transaction receipt for %s: %s", tx_hash, err)
            receipt = None

        if receipt is not None:
            return receipt['blockHash'][2:]  # Remove 0x prefix to have a hex hash only

    def get_name(self):
        return super().get_name()
