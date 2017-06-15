import logging
import merkletools


def _chainpoint_type_name(name):
    if name == "Bitcoin":
        return "BTCOpReturn"
    elif name == "Ethereum":
        return "ETHOpReturn"  # TODO: check what that should be
    else:
        logging.error("Unknown backend name: %s", name)
        raise Exception("Unknown backend name: {}".format(name))


class ChainPoint:
    def __init__(self, strategy):
        self.strategy = strategy
        self.strategy.test_backend_connections()

    def anchor(self, documents, receipt_cb):
        mt = merkletools.MerkleTools()
        mt.add_leaf(documents, True)
        mt.make_tree()

        def build_chainpoint_receipts(merkle_tree, anchors):
            receipt_cb(ChainPoint.build_v2_receipts(merkle_tree, anchors))

        self.strategy.anchor_documents(mt, build_chainpoint_receipts)

    def build_v2_receipts(merkle_tree, anchors):
        logging.info("Received anchors from all backends %s -- %s", merkle_tree.get_merkle_root(), anchors)
        chainpoint_receipts = {}

        merkle_root = merkle_tree.get_merkle_root()
        for i in range(1, merkle_tree.get_leaf_count()):
            chainpoint_receipt = {}

            proof = merkle_tree.get_proof(i)
            target_hash = merkle_tree.get_leaf(i)

            chainpoint_receipt["@context"] = "https://w3id.org/chainpoint/v2"
            chainpoint_receipt["type"] = "ChainpointSHA256v2"
            chainpoint_receipt["targetHash"] = "0x{}".format(target_hash)
            chainpoint_receipt["merkleRoot"] = "0x{}".format(merkle_root)
            chainpoint_receipt["proof"] = proof
            chainpoint_receipt["anchors"] = [{"type": _chainpoint_type_name(name), "sourceId": sourceId} for
                                             name, sourceId in anchors.items()]

            chainpoint_receipts[target_hash] = chainpoint_receipt

        return chainpoint_receipts
