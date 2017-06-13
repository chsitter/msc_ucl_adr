import logging


class ChainPoint:
    def __init__(self, strategy):
        self.strategy = strategy
        self.strategy.test_backend_connections()

    def anchor(self, documents):
        # TODO: needs data

        def build_chainpoint_receipts(merkle_root, anchors):
            logging.info("Received anchors from all backends %s -- %s", merkle_root.get_hash(), anchors)

        self.strategy.anchor_documents(documents, build_chainpoint_receipts)
