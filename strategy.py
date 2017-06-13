import logging
import threading

import merkle


# Simple implementation to just anchor with all registered backends
# let's make this an interface and provide different implementations
class AnchoringStrategy:
    backends = []
    pending_anchorings = {}

    def __init__(self, backends=None):
        logging.debug("Initialising AnchoringStrategy")
        if backends is not None:
            self.backends.extend(backends)

    def register_backend(self, backend):
        logging.debug("Registering backend %s", backend)
        self.backends.append(backend)

    def test_backend_connections(self):
        conditions = [threading.Condition() for x in self.backends]
        for (cv, b) in zip(conditions, self.backends):
            def result_cb(res):
                cv.acquire()
                logging.info("Connection to '%s' is %s", b, "working" if res else "broken")
                cv.notify()
                cv.release()

            b.test_connection(result_cb)

        for cv in conditions:
            cv.acquire()
            cv.wait()

    def anchor_documents(self, documents, receipt_callback):
        merkle_root = merkle.build_tree(documents)

        self.pending_anchorings[merkle_root] = {}

        def result_cb(backend, res):
            logging.info("Received anchoring result from %s -> %s", backend, res)
            self.pending_anchorings[merkle_root][backend.get_name()] = res

            if len(self.pending_anchorings[merkle_root]) == len(self.backends):
                logging.info("Received anchoring results from all backends")
                receipt_callback(merkle_root, self.pending_anchorings[merkle_root])


        # TODO: work out the from and to that we'll use (needs to be different for bitcoin and ethereum etc)
        for backend in self.backends:
            backend.send_transaction("0x0f28b4a4e9b8b7a00e399fc472592236be0cbf59",
                                     "0xdd275fcd58e199d6ced00ca9f1eada83fec94ad3",
                                     merkle_root.get_hash(),
                                     lambda receipt: result_cb(backend, receipt))
