import logging

from ethereum import utils
from flask import Flask

import flask_rest
import tierion
from blockchain_anchor.backends.ethereum import EthereumIntegration
from tierion import db

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.WARNING)
    logging.info("Starting up!")

    engine = db.init("sqlite:///tierion.db", False)
    session = db.create_session()

    eth_privkey = "32b4c7dc7c2c26d983a5ddeeb65e35b1f18e0148e30fe1ee58cd56bf7a0e5c1e"
    eth_acct = utils.decode_addr(utils.privtoaddr(eth_privkey))

    eth = EthereumIntegration(eth_privkey, eth_acct, "http://127.0.0.1:8079")


    def anchor_documents_callback(merkle_root):
        logging.info("Anchoring merkle_root %s", merkle_root)

        # TODO: Anchor to multiple
        eth_tx_id = eth.anchor(merkle_root)

        if eth_tx_id is None:
            logging.error("Anchoring merkle root %s failed", merkle_root)
            return None
        else:
            logging.debug("Anchored merkle tree root %s into transaction %s", merkle_root, eth_tx_id)
            return [("ETHData", eth_tx_id)]


    def confirm_anchorings_callback(endpoint, transaction_id):
        logging.info("Confirming transaction %s on %s", transaction_id, endpoint)
        if endpoint == "ETHData":
            tx_id = eth.confirm(transaction_id)
            return tx_id
        elif endpoint == "BTCOpReturn":
            tx_id = None  # btc.confirm(transaction_id)
            return tx_id
        else:
            logging.info("Transaction %s on %s not yet confirmed", transaction_id, endpoint)
            return None


    anchor_thr = tierion.start_anchoring_timer(anchor_documents_callback, queue_max_size=3, checking_interval=30)
    confirm_thr = tierion.start_confirmation_thread(confirm_anchorings_callback, checking_interval=30)

    app = Flask(__name__)

    flask_rest.setup(app, session)
    app.run(debug=True, use_reloader=False)

    tierion.stop_anchoring_thread(anchor_thr)
    tierion.stop_confirmation_thread(confirm_thr)
