import hashlib
from time import sleep
from unittest import TestCase
from uuid import uuid4

from ethereum import utils

from blockchain_anchor.backends.ethereum import EthereumIntegration


class TestEthereum(TestCase):
    def setUp(self):
        # self.privkey = utils.sha3("this is an insecure passphrase")
        self.privkey = "32b4c7dc7c2c26d983a5ddeeb65e35b1f18e0148e30fe1ee58cd56bf7a0e5c1e"
        self.account = utils.decode_addr(utils.privtoaddr(self.privkey))
        # print(self.privkey)

    def test_anchor_supplied_pk(self):
        test_merkle_root = hashlib.sha256(uuid4().bytes).hexdigest()
        eth = EthereumIntegration("TestEth", self.privkey, self.account, "http://127.0.0.1:8079")
        tx_id = eth.anchor(test_merkle_root)
        assert tx_id is not None

        sleep(3)
        confirmation = eth.confirm(tx_id)
        print("")
        print(confirmation)

    # def test_anchor_sign_callback(self):
    #     test_merkle_root = hashlib.sha256(uuid4().bytes).hexdigest()
    #     called = False
    #
    #     def sign_cb(tx):
    #         nonlocal called
    #         called = True
    #         return tx
    #
    #     eth = EthereumIntegration("TestEth", sign_cb)
    #     eth.anchor(test_merkle_root)
    #     assert called is True
