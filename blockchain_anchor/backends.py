import logging
import requests
import json

from bitcoin import from_int_to_byte, from_string_to_bytes, safe_hexlify, deserialize, serialize


def mk_opreturn(msg, rawtx=None, json=0):
    def op_push(data):
        import struct
        if len(data) < 0x4c:
            return from_int_to_byte(len(data)) + from_string_to_bytes(data)
        elif len(data) < 0xff:
            return from_int_to_byte(76) + struct.pack('<B', len(data)) + from_string_to_bytes(data)
        elif len(data) < 0xffff:
            return from_int_to_byte(77) + struct.pack('<H', len(data)) + from_string_to_bytes(data)
        elif len(data) < 0xffffffff:
            return from_int_to_byte(78) + struct.pack('<I', len(data)) + from_string_to_bytes(data)
        else:
            raise Exception("Input data error. Rawtx must be hex chars" \
                            + "0xffffffff > len(data) > 0")

    orhex = safe_hexlify(b'\x6a' + op_push(msg))
    orjson = {'script': orhex, 'value': 0}
    if rawtx is not None:
        try:
            txo = deserialize(rawtx)
            if not 'outs' in txo.keys(): raise Exception("OP_Return cannot be the sole output!")
            txo['outs'].append(orjson)
            newrawtx = serialize(txo)
            return newrawtx
        except:
            raise Exception("Raw Tx Error!")
    return orhex if not json else orjson


def _post_request(url, data, user, secret):
    res = requests.post(url, json.dumps(data), auth=(user, secret), timeout=2.5)
    if res.status_code == 200:
        return res.json()
    else:
        logging.error("Posting request failed: %s", res.json())
        return None


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

    def __init__(self, name, host, port, user, secret):
        self._host = host
        self._port = port
        self._name = name
        self._user = user
        self._secret = secret

    def test_connection(self):
        logging.info("%s: Testing connection to %s:%s", self._name, self._host, self._port)

    def embed(self, hexData):
        logging.info("%s: Embedding data %s", self._name, hexData)

    def confirm(self, tx_hash):
        logging.info("%s: Confirming transaction %s got embedded", self._name, tx_hash)


class EthereumIntegration(BlockchainIntegration):
    _op_count = 0
    _gas = 0
    _gas_price = 0
    _base_rpc_data = {"jsonrpc": "2.0"}
    _server_url = None

    def __init__(self, host, port, user, secret):
        super().__init__("Ethereum", host, port, user, secret)
        self._server_url = "http://{}:{}".format(self._host, self._port)

    def test_connection(self):
        super().test_connection()
        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "web3_clientVersion"
        rpc_data["params"] = []
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return _post_request(self._server_url, rpc_data, self._user, self._secret)

    def embed(self, hexData):
        super().embed(hexData)

        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "eth_sendTransaction"
        rpc_data["params"] = [{
            "from": src,
            "to": dst,
            # "gas": hex(self._gas),             #this is optional?
            # "gasPrice": hex(self._gas_price),  #this is optional?
            # "value": "0x9184e72a",             #this is optional?
            "data": hexData
        }]
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return _send_transaction(self._server_url, rpc_data)

    def confirm(self, tx_hash, ):
        super().confirm(tx_hash)
        rpc_data = self._base_rpc_data.copy()
        rpc_data["method"] = "eth_getTransactionReceipt"
        rpc_data["params"] = [tx_hash]
        rpc_data["id"] = self._op_count
        self._op_count += 1

        _get_transaction_receipt(self._server_url, rpc_data)


class BitcoinIntegration(BlockchainIntegration):
    _op_count = 0
    _server_url = None
    _base_rpc_data = {"jsonrpc": "1.0"}
    _fee_satoshis = 10000  # TODO: make configurable

    def __init__(self, host, port, user, secret):
        super().__init__("Bitcoin", host, port, user, secret)
        self._server_url = "http://{}:{}".format(host, port)

    def test_connection(self):
        super().test_connection()

        rpc_data = self._base_rpc_data.copy()

        rpc_data["method"] = "getbestblockhash"
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return _post_request(self._server_url, rpc_data, self._user, self._secret)

    def embed(self, src, dst, hexData):
        super().embed(src, dst, hexData)

        def _send_raw_transaction(res):
            rpc_data = self._base_rpc_data.copy()
            rpc_data["method"] = "sendrawtransaction"
            rpc_data["params"] = [res["result"]['hex']]

            rpc_data["id"] = self._op_count  # TODO: not thread safe - but okay for now
            self._op_count += 1
            return _post_request(self._server_url, rpc_data, self._user, self._secret)

        def _sign_transaction(res):

            # TODO: it's not possible to add pubkey scripts using the RPC API, so we'll have to construct the TX ourselves
            res["result"] = mk_opreturn(hexData, res["result"])

            rpc_data = self._base_rpc_data.copy()
            rpc_data["method"] = "signrawtransaction"
            rpc_data["params"] = [
                res["result"]
            ]
            rpc_data["id"] = self._op_count  # TODO: not thread safe - but okay for now
            self._op_count += 1

            return _post_request(self._server_url, rpc_data, self._user, self._secret)

        def _process_unspent_outputs(res):
            utxos_enough_money = [utxo for utxo in res["result"] if utxo["amount"] * 1000000 > self._fee_satoshis]
            if len(utxos_enough_money) > 0:
                logging.info("Using UTXO: %s", utxos_enough_money[0])

                rpc_data = self._base_rpc_data.copy()
                rpc_data["method"] = "createrawtransaction"
                rpc_data["params"] = [
                    [{"txid": utxos_enough_money[0]["txid"], "vout": utxos_enough_money[0]["vout"]}],
                    {
                        "mqCnowcw6K24bqD4Xcio3iync1ziWXEqio": utxos_enough_money[0]["amount"] - (
                            self._fee_satoshis / 1000000)
                    }
                ]
                rpc_data["id"] = self._op_count  # TODO: not thread safe - but okay for now
                self._op_count += 1

                return _post_request(self._server_url, rpc_data, self._user, self._secret)
            else:
                logging.error("Not enough money to pay for transaction fees")

        self.get_unspent_outputs()

    def confirm(self, tx_hash):
        super().confirm(tx_hash)
        pass

    def get_unspent_outputs(self):
        rpc_data = self._base_rpc_data.copy()

        rpc_data["method"] = "listunspent"
        rpc_data["id"] = self._op_count
        self._op_count += 1

        return _post_request(self._server_url, rpc_data, self._user, self._secret)
