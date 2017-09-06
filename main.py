import logging

from ethereum import utils
from flask import Flask
from flask_cors import CORS

import flask_rest
import tierion
from blockchain_anchor.backends import ethereum, bitcoin
from tierion import db

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.WARNING)
    logging.info("Starting up!")

    engine = db.init("sqlite:///tierion.db", False)
    session = db.create_session()

    eth_privkey = "32b4c7dc7c2c26d983a5ddeeb65e35b1f18e0148e30fe1ee58cd56bf7a0e5c1e"
    eth_acct = utils.decode_addr(utils.privtoaddr(eth_privkey))
    eth_svc = ethereum.Web3EthereumService("http://127.0.0.1:8079")
    eth = ethereum.EthereumIntegration(eth_privkey, eth_acct, eth_svc)

    btc_privkey = "cTyF9pebH3kwwzUt5gzaxSDQ1DbqYfx4P1i4d1TyjtSDEeUFgYsk"
    btc_acct = "mmEXEzUGcMmmiLsfxxM8gB8TQSTkuR1drf"
    btc_svc = bitcoin.BitcoindService("localhost", 18332, "bitcoinrpc", "c8805869db20730a2ddb7f62cfa2745c")
    btc = bitcoin.BitcoinIntegration(btc_privkey, btc_acct, btc_svc)

    # eth = None    # disable eth
    btc = None  # disable btc


    def anchor_documents_callback(merkle_root):
        logging.info("Anchoring merkle_root %s", merkle_root)

        eth_tx_id = eth.anchor(merkle_root) if eth is not None else None
        btc_tx_id = btc.anchor(merkle_root) if btc is not None else None

        if eth_tx_id is None and btc_tx_id is None:
            logging.error("Anchoring merkle root %s failed", merkle_root)
            return None
        else:
            logging.debug("Anchored merkle tree root %s into transaction %s", merkle_root, eth_tx_id)

            endpoints = []
            if eth is not None:
                endpoints.append(("ETHData", eth_tx_id))
            if btc is not None:
                endpoints.append(("BTCOpReturn", btc_tx_id))

            return endpoints


    # def confirm_anchorings_callback(endpoint, transaction_id):
    #     logging.info("Confirming transaction %s on %s", transaction_id, endpoint)
    #
    #     if endpoint == "ETHData":
    #         block_header = eth.confirm(transaction_id)
    #     elif endpoint == "BTCOpReturn":
    #         block_header = None
    #         # block_header = btc.confirm(transaction_id)
    #     else:
    #         logging.info("Unsupported endpoint %s", endpoint)
    #         return None
    #
    #     if block_header is None:
    #         logging.info("Transaction %s on %s not yet confirmed", transaction_id, endpoint)
    #
    #     return block_header


    anchor_thr = tierion.start_anchoring_timer(anchor_documents_callback, queue_max_size=3, checking_interval=30)
    # confirm_thr = tierion.start_confirmation_thread(confirm_anchorings_callback, checking_interval=30)

    app = Flask(__name__)
    CORS(app)

    flask_rest.setup(app, session)
    app.run(debug=True, use_reloader=False)

    tierion.stop_anchoring_thread(anchor_thr)
    # tierion.stop_confirmation_thread(confirm_thr)
