import logging
import threading


class AnchoringStrategy:
    _backends = []

    def __init__(self, backends=None):
        logging.debug("Initialising AnchoringStrategy")
        if backends is not None:
            self._backends.extend(backends)

    def register_backend(self, backend):
        logging.debug("Registering backend %s", backend)
        self._backends.append(backend)

    def test_backend_connections(self):
        pass

    def anchor_documents(self, merkle_tree, receipt_callback):
        pass


class BasicAnchoringStrategy(AnchoringStrategy):
    _pending_anchorings = {}

    def __init__(self, backends=None):
        super().__init__(backends)

    def test_backend_connections(self):
        conditions = [threading.Condition() for x in self._backends]
        for (cv, b) in zip(conditions, self._backends):
            def result_cb(res):
                cv.acquire()
                logging.info("Connection to '%s' is %s", b, "working" if res else "broken")
                cv.notify()
                cv.release()

            b.test_connection(result_cb)

        # It's okay to block waiting for that test as it's somewhat a precondition for everything else anyway
        for cv in conditions:
            cv.acquire()
            cv.wait()

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
            backend.send_transaction("0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59",
                                     "0xdd275fcd58e199d6ced00ca9f1eada83fec94ad3",
                                     "0x{}".format(merkle_tree.get_merkle_root()),
                                     lambda receipt: result_cb(backend, receipt))
