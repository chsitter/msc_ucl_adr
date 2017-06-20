import time

import logging


class DocumentCache:
    _max_size = -1
    _max_age = -1
    _documents = {}
    _anchor_cb = None

    def __init__(self, anchor_cb, max_cache_size=50, max_doc_age=48):
        # TODO: Implement max-age handling
        logging.warning("max-age handling not supported yet")
        self._max_size = max_cache_size
        self._max_age = max_doc_age
        self._anchor_cb = anchor_cb

    def add_document(self, doc, do_hash):
        self._documents[document_hash] = time.time()

        if len(self._documents) >= self._max_size:
            self._anchor_cb(self._documents)
