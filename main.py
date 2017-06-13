import logging

import time

import strategy
import chainpoint
import backends

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting up!")

    s = strategy.AnchoringStrategy()
    s.register_backend(backends.EthereumIntegration("localhost", 8079))

    cp = chainpoint.ChainPoint(s)
    cp.anchor([])

    while True:
        # Sleep forever so that our workers can do their magic
        time.sleep(500)
