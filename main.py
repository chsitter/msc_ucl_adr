import logging

import time

import strategy
import chainpoint
import backends

if __name__ == "__main__":
    config = {
        "Ethereum": {
            "host": "localhost",
            "port": 8079,
        },
        "Bitcoin": {
            "user": "bitcoinrpc",
            "secret": "c8805869db20730a2ddb7f62cfa2745c",
            "host": "localhost",
            "port": 18332,
        }
    }

    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting up!")

    s = strategy.BasicAnchoringStrategy()
    # s.register_backend(backends.EthereumIntegration(config["Ethereum"]["host"], config["Ethereum"]["port"]))
    s.register_backend(backends.BitcoinIntegration(**config["Bitcoin"]))

    cp = chainpoint.ChainPoint(s)


    def print_receipts(receipts):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        for target_hash, receipt in receipts.items():
            print("{}:".format(target_hash))
            pp.pprint(receipt)
            print()
            print("-------------------")
            print()


    cp.anchor(["Foo", "Bar", "Baz"], lambda res: print(res))

    while True:
        # Sleep forever so that our workers can do their magic
        time.sleep(500)
