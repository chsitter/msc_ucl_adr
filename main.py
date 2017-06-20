import logging

import blockchain_anchor

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting up!")

    config = {
        "backends": {
            "Ethereum": blockchain_anchor.backends.EthereumIntegration,
            "Bitcoin": blockchain_anchor.backends.BitcoinIntegration
        },
        "backend_config": {
            "Ethereum": {
                "user": "dummy",
                "secret": "dummy_pass",
                "host": "localhost",
                "port": 8079,
            },
            "Bitcoin": {
                "user": "bitcoinrpc",
                "secret": "c8805869db20730a2ddb7f62cfa2745c",
                "host": "localhost",
                "port": 18332,
            }
        },
        "anchoring_strategies": [blockchain_anchor.strategies.BasicAnchoringStrategy],
        "caching": {
            "max_cache_size": 10,
            "max_doc_age": 2
        }
    }

    anchor = blockchain_anchor.init_anchor(config)
    logging.info("Built strategies - %s", [x.get_name() for x in anchor.get_anchoring_strategies()])

    print("-----------")
    print(anchor.get_strategy_backend_status())
    print("-----------")

    # anchor.anchor("basic", "document1", True)
    # anchor.anchor("basic", "document2", True)
