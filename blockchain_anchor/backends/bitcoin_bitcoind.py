import logging

import requests
from bitcoin import *

from blockchain_anchor.backends import BlockchainIntegration


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


class BitcoinIntegration(BlockchainIntegration):
    _op_count = 0
    _server_url = None
    _base_data = {"jsonrpc": "1.0"}
    _fee_satoshis = 10000  # TODO: make configurable

    def __init__(self, host, port, user, secret, change_addr):
        super().__init__("Bitcoin")
        self._host = host
        self._port = port
        self._user = user
        self._secret = secret
        self._change_addr = change_addr

    def get_server_url(self):
        return "http://{}:{}".format(self._host, self._port)

    def _send_post_request(self, payload):
        res = requests.post(self.get_server_url(), json.dumps(payload), auth=(self._user, self._secret), timeout=2.5)
        ret, err = None, None
        if res.status_code == 200:
            res_json = res.json()
            if "result" in res_json:
                ret = res_json["result"]
            if "error" in res_json:
                err = res_json["error"]

            return ret, err
        else:
            return None, res.json()

    def anchor(self, hex_data):
        super().anchor(hex_data)
        utxos, err = self.get_unspent_outputs()
        if err is not None:
            logging.error("Error %s", err)
            return None

        utxos_enough_money = [utxo for utxo in utxos if utxo["amount"] * 100000000 > self._fee_satoshis]
        if len(utxos_enough_money) <= 0:
            logging.error("No UTXO with enough money found")
            return None

        logging.info("Using UTXO: %s", utxos_enough_money[0])
        data = self._base_data.copy()
        data["method"] = "createrawtransaction"
        data["params"] = [
            [{"txid": utxos_enough_money[0]["txid"], "vout": utxos_enough_money[0]["vout"]}],
            {
                # TODO: need to figure out how many decimals etc etc
                self._change_addr: "{:.4f}".format(utxos_enough_money[0]["amount"] - (self._fee_satoshis / 100000000))
            }
        ]
        data["id"] = self._op_count
        self._op_count += 1
        raw_tx, err = self._send_post_request(data)

        if err is not None:
            logging.error("Error creating raw transaction: %s", err)
            return None

        # This is ridiculous - but the bitcoin RCP API is utter rubbish
        raw_tx = mk_opreturn(hex_data, raw_tx)

        data = self._base_data.copy()
        data["method"] = "signrawtransaction"
        data["params"] = [
            raw_tx
        ]
        data["id"] = self._op_count
        self._op_count += 1

        signed_tx, err = self._send_post_request(data)
        if err is not None:
            logging.error("Error signing raw transaction: %s", err)
            return None

        data = self._base_data.copy()
        data["method"] = "sendrawtransaction"
        data["params"] = [signed_tx["hex"]]

        data["id"] = self._op_count  # TODO: not thread safe - but okay for now
        self._op_count += 1
        tx_id, err = self._send_post_request(data)

        if err is not None:
            logging.error("Error sending transaction: %s", err)
            return None

        return tx_id

    def confirm(self, tx_hash):
        super().confirm(tx_hash)
        data = self._base_data.copy()

        data["method"] = "gettransaction"
        data["params"] = [tx_hash]
        data["id"] = self._op_count
        self._op_count += 1

        res, err = self._send_post_request(data)
        if err is not None:
            logging.error("Error getting transaction receipt: %s", err)
            return None

        confirmations = res["confirmations"]
        if confirmations > 0:
            return res["blockhash"]

        return None

    def get_unspent_outputs(self):
        data = self._base_data.copy()

        data["method"] = "listunspent"
        data["id"] = self._op_count
        self._op_count += 1

        return self._send_post_request(data)
