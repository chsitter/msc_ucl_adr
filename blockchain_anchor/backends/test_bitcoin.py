import hashlib
import logging
from unittest import TestCase
from uuid import uuid4

import base58

from blockchain_anchor.backends.bitcoin import BitcoinIntegration, BitcoindService, make_raw_transaction, \
    build_pay_to_pubkey_hash_script, build_op_return_script, wif_to_private_key


class TestBitcoinIntegration(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        self.host = "localhost"
        self.port = 18332
        self.account = "mmEXEzUGcMmmiLsfxxM8gB8TQSTkuR1drf"
        self.privkey = "cTyF9pebH3kwwzUt5gzaxSDQ1DbqYfx4P1i4d1TyjtSDEeUFgYsk"
        self.secret = "c8805869db20730a2ddb7f62cfa2745c"
        self.rpc_user = "bitcoinrpc"
        self.svc = BitcoindService(self.host, self.port, self.rpc_user, self.secret)

    def test_wif_to_privkey(self):
        k = wif_to_private_key("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ")
        self.assertEqual(k.upper(), "0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D")

    def test_anchor(self):
        test_merkle_root = hashlib.sha256(uuid4().bytes).hexdigest()
        btc = BitcoinIntegration(self.privkey, self.account, self.svc)

        print(btc.anchor(test_merkle_root))

    def test_confirm(self):
        txid = "decc1b4cbddc2e3450223b4ce3d8e76c54185041d67c4da44671fa5f6fcc46ff"
        btc = BitcoinIntegration(self.privkey, self.account, self.svc, self.account)

        print(btc.confirm(txid))

    def test_base58stuff(self):
        real = base58.b58decode_check(self.account)

        print(bytearray(real)[1:21].hex())

        want = bytearray.fromhex("6a41da65987f4630c8ee968c249f60af6a731746")
        print(want.hex())

    def test_create_raw_tx(self):
        test_merkle_root = "e915de7a88f72aea9920b5a94c9a1e3da5a47aa262399e9940777124d5a8cda3"
        wanted_raw_transaction = bytearray.fromhex(
            "02000000010263a9b6b4f55ab8914f15cecc0825ae1f771dfaf9c266f067c99740458cbbe60000000000ffffffff010065cd1d000000001976a9146a41da65987f4630c8ee968c249f60af6a73174688ac00000000")
        utxo1 = {'txid': 'e6bb8c454097c967f066c2f9fa1d771fae2508ccce154f91b85af5b4b6a96302', 'vout': 0,
                 'address': 'mzxnH5CKFFWA7TFnX2DHjQbHsCPNbydoEs',
                 'scriptPubKey': '2103ca49b910134e0d94217e3198fcd2b0de4c3f4abc1bcc8a1ae849d556cecded61ac',
                 'amount': 12.5, 'confirmations': 141, 'spendable': True, 'solvable': True, 'safe': True}

        output1 = {"satoshis": 5 * 100000000, "pubkeyScript": build_pay_to_pubkey_hash_script(self.account)}
        output2 = {"satoshis": 0, "pubkeyScript": build_op_return_script(test_merkle_root)}

        print(make_raw_transaction([utxo1], [output1, output2]))
        print(wanted_raw_transaction.hex())
