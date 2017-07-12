import logging

import requests
import rlp
from ethereum import transactions
from web3 import Web3, HTTPProvider

from blockchain_anchor.backends import BlockchainIntegration


class EthereumService:
    def get_transaction_count(self, account):
        """
        queries the current transaction count for an account
        :param account: account identifier of the form '0x...'
        :return: integer representing the current tx count or None on error
        """
        pass

    def send_raw_transaction(self, transaction_hex):
        """
        sends a signed raw transaction off to an ethereum service
        :param transaction_hex: serialised raw signed transaction of the form '0x...'
        :return: the transaction ID for the submitted transaction in the form '0x...' or None on error
        """
        pass

    def get_transaction_receipt(self, transaction_id):
        """
        gets a receipt for a previously submitted transaction
        :param transaction_id: tx id of the form '0x...'
        :return: the receipt data or None on error
        """
        pass


class Web3EthereumService(EthereumService):
    def __init__(self, web3_http_uri):
        self._web3 = Web3(HTTPProvider(web3_http_uri))

    def get_transaction_receipt(self, transaction_id):
        try:
            return self._web3.eth.getTransactionReceipt(transaction_id)
        except ValueError as err:
            logging.error("Failed getting transaction receipt for %s: %s", transaction_id, err)
            receipt = None
        return receipt

    def get_transaction_count(self, account):
        try:
            tx_count = self._web3.eth.getTransactionCount(account)
        except ValueError as err:
            logging.error("Failed getting transaction count for %s: %s", account, err)
            tx_count = None
        return tx_count

    def send_raw_transaction(self, transaction_hex):
        try:
            result = self._web3.eth.sendRawTransaction(transaction_hex)
            result = result if result.startswith("0x") else "0x".format(result)
        except ValueError as err:
            logging.error("Failed to send transaction: %s", err)
            result = None
        return result


class EtherscanService(EthereumService):
    def __init__(self, api_key, url="https://api.etherscan.io/api"):
        """
        Create an instance of the Etherscan Service for Ethereum integration, pointing to one of the networks exposed by etherscan
        :param api_key: your API key as shown in the etherscan account page
        :param url: defaults to 'https://api.etherscan.io/api', but can be e.g. 'https://ropsten.etherscan.io/api' for ropsten testnet
        """
        self._api_key = api_key
        self._url = url

    def get_transaction_receipt(self, transaction_id):
        params = {"module": "proxy",
                  "action": "eth_getTransactionReceipt",
                  "txhash": transaction_id,
                  "tag": "latest",
                  "apikey": self._api_key}
        res = requests.get(self._url, params=params)
        if res.status_code == 200:
            if "error" in res.json():
                return None
            return res.json()["result"]
        else:
            return None

    def get_transaction_count(self, account):
        params = {"module": "proxy",
                  "action": "eth_getTransactionCount",
                  "address": account,
                  "tag": "latest",
                  "apikey": self._api_key}
        res = requests.get(self._url, params=params)
        if res.status_code == 200:
            if "error" in res.json():
                return None
            return int(res.json()["result"], 16)
        else:
            return None

    def send_raw_transaction(self, transaction_hex):
        params = {"module": "proxy",
                  "action": "eth_sendRawTransaction",
                  "hex": transaction_hex if transaction_hex.startswith("0x") else "0x{}".format(transaction_hex),
                  "apikey": self._api_key}

        res = requests.get(self._url, params=params)
        if res.status_code == 200:
            if "error" in res.json():
                return None
            return res.json()["result"]
        else:
            return None


class EthereumIntegration(BlockchainIntegration):
    def __init__(self, privkey, account, service: EthereumService, gasprice=1000, startgas=100000):
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
        self._account = account if account.startswith("0x") else "0x{}".format(account)
        self._service = service

        # the nonce is defined to be the transaction count of the account
        # the problem here is that pending transactions aren't returned by getTransactionCount and we might want to add
        # eth.getBlock("pending", true).transactions to get them
        self._nonce = self._service.get_transaction_count(self._account)

    def anchor(self, hex_data):
        super().anchor(hex_data)

        tx = transactions.Transaction(self._nonce, self._gasprice, self._startgas, "", 0, hex_data)
        self._nonce += 1

        if callable(self._privkey):
            tx = self._privkey(tx)
        else:
            tx.sign(self._privkey)

        raw_tx = Web3.toHex(rlp.encode(tx))
        result = self._service.send_raw_transaction(raw_tx)

        return result[2:]

    def confirm(self, tx_hash):
        super().confirm(tx_hash)
        receipt = self._service.get_transaction_receipt(tx_hash if tx_hash.startswith("0x") else "0x{}".format(tx_hash))

        if receipt is not None:
            return receipt['blockHash'][2:]  # Remove 0x prefix to have a hex hash only

    def get_name(self):
        return super().get_name()
