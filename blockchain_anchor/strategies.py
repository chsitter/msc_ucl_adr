import logging
from enum import Enum

from blockchain_anchor.backends import BlockchainIntegration


class AnchorState(Enum):
    UNSENT = 1,
    UNCONFIRMED = 2,
    CONFIRMED = 3,
    FAILED = 4,


class AnchoringStrategy:
    _integrations = None
    _name = None

    def __init__(self, name: str, description: str, integrations: [BlockchainIntegration]):
        logging.debug("Initialising AnchoringStrategy")
        self._name = name
        self._description = description
        self._integrations = [] if integrations is None else integrations

    def embed(self, hex_data):
        pass

    def get_embedding_status(self, hex_data):
        pass

    def confirm(self, hex_data):
        pass

    def describe(self):
        return "{}: {}".format(self._name, self._description)

    def get_name(self):
        return self._name


class AllAnchorStrategy(AnchoringStrategy):
    _pending_anchorings = {}

    def __init__(self, integrations: [BlockchainIntegration]):
        super().__init__("all", "This strategy anchors the document to all registered integrations", integrations)

    def embed(self, hex_data):
        self._pending_anchorings[hex_data] = {}
        for name, integration in self._integrations.items():
            assert isinstance(integration, BlockchainIntegration)
            self._pending_anchorings[hex_data][name] = {"state": AnchorState.UNSENT, "txid": None}
            embedding_result = integration.embed(hex_data)
            if embedding_result is None:
                self._pending_anchorings[hex_data][name] = {"state": AnchorState.FAILED, "txid": None}
            else:
                self._pending_anchorings[hex_data][name] = {"state": AnchorState.UNCONFIRMED,
                                                            "txid": embedding_result}

    def get_embedding_status(self, hex_data):
        return self._pending_anchorings[hex_data]

    def confirm(self, hex_data):
        results = {}
        if hex_data in self._pending_anchorings:
            for name, integration in self._integrations.items():
                results[name] = None
                assert isinstance(integration, BlockchainIntegration)
                pending = self._pending_anchorings[hex_data][name]
                if pending["state"] == AnchorState.CONFIRMED:
                    results[name] = pending["block_hash"]
                elif pending["state"] == AnchorState.UNCONFIRMED:
                    results[name] = integration.confirm(pending["txid"])

                    if results[name] is not None:
                        pending["block_hash"] = results[name]
                        pending["state"] = AnchorState.CONFIRMED

                elif pending["state"] == AnchorState.FAILED:
                    results[name] = 0x0
                else:
                    raise Exception("Unhandled confirmation condition")
                    # TODO: what do we do here?

            return results
        else:
            logging.warning("Can't create confirmation for data %s as data isn't pending", hex_data)
            return None
