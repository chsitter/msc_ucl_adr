import concurrent.futures
import logging
import requests
import json

import time


def _post_request(url, data, result_cb):
    res = requests.post(url, json.dumps(data))
    if res.status_code == 200:
        result_cb(res.json())
    else:
        logging.error("Posting request failed: %s", res)
        result_cb(None)
    return res


def _send_transaction(url, data, result_cb):
    res = requests.post(url, json.dumps(data))
    if res.status_code == 200:
        if "error" in res.json():
            logging.error("Sending transaction failed: %s", res.json()["error"])
            result_cb(None)
        else:
            transaction_hash = res.json()["result"]
            logging.error("Send transaction done: %s", res)
            result_cb(transaction_hash)
    else:
        logging.error("Send transaction failed: %s", res)
        result_cb(None)
    return res


def _get_transaction_receipt(url, data, result_cb):
    res = requests.post(url, json.dumps(data))
    if res.status_code == 200:
        result_json = res.json()
        if result_json["result"] is None:
            logging.info("Transaction receipt for %s not yet available", data["params"]["data"])
            # Transaction receipt not yet available
        result_cb(result_json["result"])
    else:
        logging.error("Send transaction failed: %s", res)
        result_cb(None)
    return res


class BlockchainIntegration:
    _host = None
    _port = None
    _name = None

    def __init__(self, name, host, port):
        self._host = host
        self._port = port
        self._name = name

    def test_connection(self, result_cb):
        logging.info("Testing connection to %s - %s:%s", self._name, self._host, self._port)

    def send_transaction(self, src, dst, data, receipt_callback):
        logging.info("Sending transaction to %s %s -> %s", self._name, src, dst)

    def get_name(self):
        return self._name

    def __str__(self):
        return "{} - {}:{}".format(self._name, self._host, self._port)


class EthereumIntegration(BlockchainIntegration):
    _op_count = 0
    _gas = 0
    _gas_price = 0
    _base_rpc_data = {"jsonrpc": "2.0"}
    _server_url = None
    _event_loop = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="Ethereum_worker")

    def __init__(self, host, port, gas=50000, gas_price=200000):
        super().__init__("Ethereum", host, port)
        self._server_url = "http://{}:{}".format(self._host, self._port)

    def test_connection(self, result_cb):
        super().test_connection(result_cb)
        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "web3_clientVersion"
        rpc_data["params"] = []
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return self._event_loop.submit(_post_request, self._server_url, rpc_data, result_cb)

    def send_transaction(self, src, dst, data, result_cb):
        super().send_transaction(src, dst, data, result_cb)

        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "eth_sendTransaction"
        rpc_data["params"] = [{
            "from": src,
            "to": dst,
            # "gas": hex(self._gas),             #this is optional?
            # "gasPrice": hex(self._gas_price),  #this is optional?
            # "value": "0x9184e72a",             #this is optional?
            "data": data
        }]
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return self._event_loop.submit(_send_transaction, self._server_url, rpc_data, result_cb)

    def get_transaction_receipt(self, transaction_hash, result_cb):
        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "eth_getTransactionReceipt"
        rpc_data["params"] = [transaction_hash]
        rpc_data["id"] = self._op_count
        self._op_count += 1

        self._event_loop.submit(_get_transaction_receipt, self._server_url, rpc_data, result_cb)


class BitcoinIntegration(BlockchainIntegration):

    def __init__(self, host, port):
        super().__init__("Bitcoin", host, port)
