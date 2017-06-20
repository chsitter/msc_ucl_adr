import logging

from blockchain_anchor import DocumentCache


class AnchoringStrategy:
    _backends = None
    _name = None
    _cache = None

    def __init__(self, name, backends, description, cache):
        logging.debug("Initialising AnchoringStrategy")
        self._name = name
        self._description = description
        self._backends = [] if backends is None else backends
        self._cache = cache

    def test_backend_connections(self):
        pass

    def anchor_document(self, user, doc, do_hash):
        pass

    def anchor_documents(self, merkle_tree, receipt_callback):
        pass

    def get_name(self):
        return self._name

    def describe(self):
        return "{}: {}".format(self._name, self._description)


class BasicAnchoringStrategy(AnchoringStrategy):
    _pending_anchorings = {}

    def __init__(self, backends, cache):
        super().__init__("basic", backends, "This strategy anchors the document to all registered backends", cache)

    def test_backend_connections(self):
        return {name: "up" if be.test_connection() else "down" for name, be in self._backends.items()}

    def anchor_document(self, user, doc, do_hash):
        assert isinstance(self._cache, DocumentCache)
        self._cache.add_document()

    def anchor_documents(self, merkle_tree, receipt_callback):
        self._pending_anchorings[merkle_tree] = {}

        def result_cb(backend, res):
            logging.info("Received anchoring result from %s -> %s", backend, res)
            self._pending_anchorings[merkle_tree][backend.get_name()] = res

            if len(self._pending_anchorings[merkle_tree]) == len(self._backends):
                logging.info("Received anchoring results from all backends")
                receipt_callback(merkle_tree, self._pending_anchorings[merkle_tree])

        # TODO: work out the from and to that we'll use (needs to be different for bitcoin and ethereum etc)
        for backend in self._backends:
            backend.embed("0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59",
                                     "0xdd275fcd58e199d6ced00ca9f1eada83fec94ad3",
                                     "0x{}".format(merkle_tree.get_merkle_root()),
                          lambda receipt: result_cb(backend, receipt))
