import hashlib
import json
import logging

import base58
import ecdsa
import requests
from bitcoin import privtopub

from blockchain_anchor.backends import BlockchainIntegration

OP_DUP = 0x76
OP_HASH160 = 0xA9
OP_EQUALVERIFY = 0x88
OP_CHECKSIG = 0xAC
OP_RETURN = 0x6a


def to_varint(number: int):
    if number < 0xFD:
        return bytearray(number.to_bytes(1, "little"))
    elif number <= 0xFFFF:
        return bytearray(0xFD) + number.to_bytes(2, "little")
    elif number <= 0xFFFFFFFF:
        return bytearray(0xFE) + number.to_bytes(5, "little")
    else:
        return bytearray(0xFF) + number.to_bytes(9, "little")


def to_varstr(data: bytearray):
    return to_varint(len(data)) + data


def build_pay_to_pubkey_hash_script(address):
    # OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
    pubkeyScript = bytearray([OP_DUP, OP_HASH160])
    pubkeyScript = pubkeyScript + bytes([0x14])
    pubkeyScript = pubkeyScript + base58.b58decode_check(address)[1:21]
    pubkeyScript = pubkeyScript + bytearray([OP_EQUALVERIFY, OP_CHECKSIG])
    return pubkeyScript.hex()


def build_op_return_script(merkle_root):
    # OP_RETURN <data>
    opReturn = bytearray([OP_RETURN])
    opReturn = opReturn + to_varint(len(merkle_root))
    opReturn = opReturn + bytearray.fromhex(merkle_root)
    return opReturn.hex()


def wif_to_private_key(private_key_wif):
    compressed = False
    pk = bytearray(base58.b58decode_check(private_key_wif))[1:]
    if pk[-1] == 0x01:
        compressed = True
        pk = pk[0:-1]
    return pk.hex(), compressed


def make_raw_transaction(utxos, outputs):
    """

    :param utxos: list of tuples [(txid, vout), (txid, vout), ...]
    :param outputs: list of triples [(to_address, script, amount), (to_address, script, amount), ...]
    :return: the raw unsigned transaction as a byte array
    """
    assert (len(utxos) == 1)  # Currently only supports a single input

    raw_tx = bytearray(int(1).to_bytes(4, 'little'))  # version number
    raw_tx = raw_tx + to_varint(len(utxos))  # number of utxos, inputs into this tx

    for utxo in utxos:
        reverse_txid = bytearray.fromhex(utxo['txid'])
        reverse_txid.reverse()
        raw_tx = raw_tx + reverse_txid
        raw_tx = raw_tx + utxo['vout'].to_bytes(4, 'little')

        scriptSig = bytearray.fromhex(utxo['scriptPubKey'])
        raw_tx = raw_tx + to_varstr(scriptSig)  # pubkey script [len + data]
        raw_tx = raw_tx + bytearray([0xff, 0xff, 0xff, 0xff])  # Sequence number, always 0xffffffff

    raw_tx = raw_tx + to_varint(len(outputs))  # number of outputs
    for output in outputs:
        raw_tx = raw_tx + int(output['satoshis']).to_bytes(8, 'little')
        pk_script = bytearray.fromhex(output['pubkeyScript'])
        raw_tx = raw_tx + to_varstr(pk_script)

    raw_tx = raw_tx + int(0).to_bytes(4, 'little')  # lock time
    return raw_tx.hex()


def sign_transaction(private_key_wif, raw_unsigned_transaction, utxos, outputs):
    print(raw_unsigned_transaction)

    private_key, compressed_pk = wif_to_private_key(private_key_wif)
    tx = bytearray.fromhex(raw_unsigned_transaction) + int(1).to_bytes(4, 'little')

    double_sha256_tx = hashlib.sha256(hashlib.sha256(tx).digest()).digest()
    signing_key = ecdsa.SigningKey.from_string(bytearray.fromhex(private_key), curve=ecdsa.SECP256k1)
    # public_key = bytearray([0x04]) + signing_key.get_verifying_key().to_string()
    public_key = bytearray.fromhex(privtopub(private_key_wif))
    signature = signing_key.sign_digest(double_sha256_tx, sigencode=ecdsa.util.sigencode_der) + int(1).to_bytes(1,
                                                                                                                'little')
    scriptSig = to_varstr(signature) + to_varstr(public_key)

    utxos[0]["scriptPubKey"] = scriptSig.hex()
    return make_raw_transaction(utxos, outputs)


class BitcoinService:
    def get_unspent_outputs(self, account: object) -> list:
        """
        queries the utxos for the account specified
        :param account: account identifier of the form '0x...'
        :return: list of utxos belonging to this account or None on error
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


class BitcoinIntegration(BlockchainIntegration):
    _op_count = 0

    def __init__(self, privkey, account, service: BitcoinService, change_addr=None, transaction_fee=1000):
        """

        :param name:        Name of this integration for use in Chainpoint receipt
        :param privkey:     private key to be used for tx signing or a callback function of the form fn(tx) -> tx
        :param change_addr: Bitcoin address for change, defaults to account
        :param transaction_fee:      amount in satoshis to be paid as transaction fees, default 1000
        """
        super().__init__("Bitcoin")
        self._privkey = privkey
        self._account = account if account.startswith("0x") else "0x{}".format(account)
        self._service = service
        self._change_addr = self._account if change_addr is None else change_addr
        self._transaction_fee = transaction_fee

    def anchor(self, hex_data):
        super().anchor(hex_data)
        utxos = self._service.get_unspent_outputs(self._account)
        if utxos is None:
            logging.error("Error getting utxos for account %s", self._account)
            return None

        utxos_enough_money = [utxo for utxo in utxos if utxo["amount"] * 100000000 > self._transaction_fee]
        if len(utxos_enough_money) <= 0:
            logging.error("No UTXO with enough money found")
            return None

        print("building TX")
        logging.info("Using UTXO: %s", utxos_enough_money[0])
        print(utxos_enough_money[0])

        output1 = {"satoshis": (utxos_enough_money[0]['amount'] * 100000000) - self._transaction_fee, "pubkeyScript": build_pay_to_pubkey_hash_script(self._change_addr)}
        output2 = {"satoshis": 0, "pubkeyScript": build_op_return_script(hex_data)}

        raw_unsigned_transaction = make_raw_transaction([utxos_enough_money[0]], [output1, output2])

        # # TODO: this needs to be done offline, not via the rpc, but damn that's confusing
        data = self._service._base_data.copy()
        data["method"] = "signrawtransaction"
        data["params"] = [
            raw_unsigned_transaction
        ]
        data["id"] = self._op_count
        self._op_count += 1

        signed_transaction = self._service._send_post_request(data)['hex']
        # signed_transaction = self._sign_transaction(raw_unsigned_transaction, [utxos_enough_money[0]], [output1, output2])
        # print(signed_transaction)
        # TODO: this is the end of the above TODO
        return self._service.send_raw_transaction(signed_transaction)

    def confirm(self, tx_hash):
        super().confirm(tx_hash)

        receipt = self._service.get_transaction_receipt(tx_hash if tx_hash.startswith("0x") else "0x{}".format(tx_hash))

        if receipt is not None and 'blockhash' in receipt:
            return receipt['blockhash']
        return None

    def _sign_transaction(self, raw_unsigned_transaction, inputs, outputs):
        if callable(self._privkey):
            tx = self._privkey(raw_unsigned_transaction)
        else:
            tx = sign_transaction(self._privkey, raw_unsigned_transaction, inputs, outputs)

        return tx

    def get_name(self):
        return super().get_name()


class BitcoindService(BitcoinService):
    def __init__(self, host, port, user, secret):
        self._host = host
        self._port = port
        self._user = user
        self._secret = secret
        self._base_data = {"jsonrpc": "1.0"}
        self._op_count = 1

    def get_transaction_receipt(self, transaction_id):
        data = self._base_data.copy()

        data["method"] = "gettransaction"
        data["params"] = [transaction_id]
        data["id"] = self._op_count
        self._op_count += 1

        return self._send_post_request(data)

    def send_raw_transaction(self, transaction_hex):
        data = self._base_data.copy()

        data["method"] = "sendrawtransaction"
        data["params"] = [transaction_hex]
        data["id"] = self._op_count
        self._op_count += 1

        return self._send_post_request(data)

    def get_unspent_outputs(self, account: object) -> list:
        data = self._base_data.copy()

        data["method"] = "listunspent"
        data["id"] = self._op_count
        self._op_count += 1

        return self._send_post_request(data)

    def get_server_url(self):
        return "http://{}:{}".format(self._host, self._port)

    def _send_post_request(self, payload):
        res = requests.post(self.get_server_url(), json.dumps(payload), auth=(self._user, self._secret), timeout=2.5)
        if res.status_code == 200:
            res_json = res.json()
            if "result" in res_json:
                return res_json["result"]
            if "error" in res_json:
                logging.error(res_json["error"])
                return None
        else:
            logging.error("%d: %s", res.status_code, res.text)
