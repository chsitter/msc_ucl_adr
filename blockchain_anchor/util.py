import logging
import merkletools


def _chainpoint_type_name(name):
    if name == "Bitcoin":
        return "BTCOpReturn"
    elif name == "Ethereum":
        return "ETHData"
    else:
        logging.error("Unknown backend name: %s", name)
        raise Exception("Unknown backend name: {}".format(name))


def build_v3_receipt(merkle_tree: merkletools.MerkleTools, anchors):
    logging.info("Received anchors from backends %s -- %s", merkle_tree.get_merkle_root(), anchors)
    raise Exception("Not yet implemented - Specification on www.chainpoint.org, v3 currently in beta")


def build_v2_receipt_single(merkle_root, proof, rec_hash, anchors):
    logging.info("Received anchors from backends %s -- %s", merkle_root, anchors)
    return {"@context": "https://w3id.org/chainpoint/v2",
            "type": "ChainpointSHA256v2",
            "targetHash": "{}".format(rec_hash),
            "merkleRoot": "{}".format(merkle_root),
            "proof": proof,
            "anchors": [{"type": _chainpoint_type_name(name), "sourceId": sourceId} for name, sourceId in
                        anchors.items()]}


def build_v2_receipt(merkle_tree: merkletools.MerkleTools, anchors):
    logging.info("Received anchors from backends %s -- %s", merkle_tree.get_merkle_root(), anchors)
    chainpoint_receipts = {}

    merkle_root = merkle_tree.get_merkle_root()
    for i in range(1, merkle_tree.get_leaf_count()):
        chainpoint_receipt = {}

        proof = merkle_tree.get_proof(i)
        target_hash = merkle_tree.get_leaf(i)

        chainpoint_receipt["@context"] = "https://w3id.org/chainpoint/v2"
        chainpoint_receipt["type"] = "ChainpointSHA256v2"
        chainpoint_receipt["targetHash"] = "{}".format(target_hash)
        chainpoint_receipt["merkleRoot"] = "{}".format(merkle_root)
        chainpoint_receipt["proof"] = proof
        chainpoint_receipt["anchors"] = [{"type": _chainpoint_type_name(name), "sourceId": sourceId} for
                                         name, sourceId in anchors.items()]

        chainpoint_receipts[target_hash] = chainpoint_receipt

    return chainpoint_receipts
