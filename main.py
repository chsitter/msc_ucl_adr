import logging

from flask import Flask

import blockchain_anchor
import flask_rest
import tierion
from blockchain_anchor import datastore
from blockchain_anchor.backends.bitcoin_bitcoind import BitcoinIntegration
from blockchain_anchor.backends.ethereum_web3 import EthereumIntegration
from blockchain_anchor.strategies import AllAnchorStrategy
from tierion import db

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting up!")

    config = {
        "backends": {
            "Ethereum": (EthereumIntegration,
                         {
                             "eth_acct": "0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59",
                             "eth_acct_secret": "password",
                             "ipc_path": "/Users/chsitter/Documents/UCL/msc/project/ethereum_testnet/geth.ipc"
                         }),
            "Bitcoin": (BitcoinIntegration,
                        {
                            "user": "bitcoinrpc",
                            "secret": "c8805869db20730a2ddb7f62cfa2745c",
                            "host": "localhost",
                            "port": 18332,
                            "change_addr": "mqCnowcw6K24bqD4Xcio3iync1ziWXEqio"
                        })
        },
        "strategies": {
            "all": AllAnchorStrategy,
        }
    }

    engine = db.init("sqlite:///tierion.db", False)
    session = db.create_session()

    # anchor = blockchain_anchor.init_anchor(config, "all")
    # ds = datastore.DataStores(anchor)

    def anchor_documents_callback(records):
        logging.debug("Anchoring %d records", len(records))
        (leaf_ids, merkle_tree) = tierion.build_merkle_tree(records)
        logging.debug("Anchoring merkle tree root %s", merkle_tree.get_merkle_root())
        return False

    thr = tierion.start_anchoring_timer(anchor_documents_callback, checking_interval=30)

    app = Flask(__name__)
    flask_rest.setup(app, session)
    app.run(debug=True, use_reloader=False)

    tierion.stop_anchoring_timer(thr)
