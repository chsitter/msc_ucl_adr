import logging


def build_chainpoint_receipt(item, version=2):
    assert version == 2  # So far only v2 supported
    logging.debug("Generating receipt for backends %s", [x.endpoint for x in item.confirmations])

    return {
        "@context": "https://w3id.org/chainpoint/v2",
        "type": "ChainpointSHA256v2",
        "targetHash": "{}".format(item.sha256),
        "merkleRoot": "{}".format(item.confirmations[0].merkle_root if len(item.confirmations) > 0 else "0x0"),
        "proof": item.proof,
        "anchors": [{"type": c.endpoint, "sourceId": c.tx_id} for c in item.confirmations]
    }
