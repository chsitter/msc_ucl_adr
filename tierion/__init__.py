import logging
import sched
import time
from datetime import datetime, timedelta
from threading import Thread

import merkletools
import sys

from tierion import db
from tierion.accounts import create_account, delete_account, get_account, login
from tierion.datastore import create_datastore, update_datastore, delete_datastore, get_datastore
from tierion.db import Confirmation
from tierion.record import create_record, delete_record, get_record, RecordState
from tierion.hashitem import create_hashitem, get_hashitem


def _check_queue_fn(callback, queue_max_size, record_max_age):
    logging.debug("Checking queue (max_size: %d, max_age: %d)", queue_max_size, record_max_age)
    session = db.create_session()

    end_date = int((datetime.utcnow() - timedelta(seconds=record_max_age)).timestamp())
    have_expired_hashitems = len(get_hashitem(session, pending=True, end_date=end_date)) > 0
    session.rollback()

    queued_hashitems = get_hashitem(session, pending=True, for_update=True)

    if len(queued_hashitems) >= queue_max_size or have_expired_hashitems:
        # sent = callback(queued_hashitems)
        # [("Ethereum", eth_tx_id)], merkle_root, hashitem_proofs
        # TODO: maybe return the merkle tree and look up leaf hashes in here

        logging.debug("Anchoring %d hashitems including %d records", len(queued_hashitems), len([x for x in queued_hashitems if x.record is not None]))
        merkle_root, hashitem_proofs = build_merkle_tree(queued_hashitems)

        tx_ids = callback(merkle_root)

        if tx_ids is not None:

            confirmations = [db.Confirmation(endpoint=ep, tx_id=tx_id, merkle_root=merkle_root) for ep, tx_id in tx_ids]
            [session.add(c) for c in confirmations]
            for i in queued_hashitems:
                if i.id in hashitem_proofs:
                    i.proof = hashitem_proofs[i.id]
                    if i.record is not None:
                        i.record.status = RecordState.UNPUBLISHED.value[0]  # TODO: why [0]?
                    [i.confirmations.append(c) for c in confirmations]
                    session.add(i)
                else:
                    logging.warning("Ignoring hashitem %s as no proof found", i.id)
            session.commit()
        else:
            logging.info("Anchoring callback returned no transaction ids, rolling back changes")
            session.rollback()
    else:
        session.rollback()


def _check_confirmations_fn(callback):
    logging.debug("Checking pending confirmations")
    session = db.create_session()
    pending_confirmations = session.query(Confirmation).filter(Confirmation.block_header.is_(None)).with_for_update().all()

    if len(pending_confirmations) > 0:
        for c in pending_confirmations:
            block_header = callback(c.endpoint, c.tx_id)
            if block_header is not None:
                c.block_header = block_header
                session.add(c)

        session.commit()
    else:
        session.rollback()


class QueueCheckerThread(Thread):
    def __init__(self, interval, callback, cb_args):
        Thread.__init__(self)
        self.stopped = False
        self.interval = interval
        self.callback = callback
        self.cb_args = cb_args
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def run(self):
        while not self.stopped:
            self.scheduler.run()
            self.scheduler.enter(self.interval, 1, self.callback, self.cb_args)

    def stop(self):
        self.stopped = True
        sys.exit()  # TODO: this feels like a bit of a hack


class ConfirmationCheckerThread(Thread):
    def __init__(self, interval, callback, cb_args):
        Thread.__init__(self)
        self.stopped = False
        self.interval = interval
        self.callback = callback
        self.cb_args = cb_args
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def run(self):
        while not self.stopped:
            self.scheduler.run()
            self.scheduler.enter(self.interval, 1, self.callback, self.cb_args)

    def stop(self):
        self.stopped = True
        sys.exit()  # TODO: this feels like a bit of a hack


def start_anchoring_timer(callback, queue_max_size=10, record_max_age=600, checking_interval=30):
    """
    This function starts a timer that periodically checks for queued records and sends a list of these (with a DB lock held) to the callback
    :param callback: A function of the form ([Record]) -> {true,false}
    :param queue_max_size: the maximum number of queued records, callback is called when this is exceeded
    :param record_max_age: the maximum age of queued records, callback is called when this is exceeded
    :param checking_interval: the interval at which to check the queue size as well as the record age
    """
    logging.info("Starting QueueChecker Thread")
    thr = QueueCheckerThread(checking_interval, _check_queue_fn, [callback, queue_max_size, record_max_age])
    thr.daemon = True
    thr.start()
    return thr


def start_confirmation_thread(callback, checking_interval=30):
    logging.info("Starting ConfirmationChecker Thread")
    thr = ConfirmationCheckerThread(checking_interval, _check_confirmations_fn, [callback])
    thr.daemon = True
    thr.start()
    return thr


def stop_anchoring_thread(timer_thread: QueueCheckerThread):
    logging.info("Stopping QueueChecker Thread")
    timer_thread.stop()


def stop_confirmation_thread(confirm_thread: ConfirmationCheckerThread):
    logging.info("Stopping ConfirmationCheckerThread Thread")
    confirm_thread.stop()


def build_merkle_tree(hashitems):
    """
    Builds a merkletools merkle tree from the list of records passed in
    :param hashitems: Hex strings to be added as leaf nodes
    :return:
    """
    logging.debug("Building merkle tree for {} hashitems".format(len(hashitems)))
    mt = merkletools.MerkleTools()
    for i in hashitems:
        mt.add_leaf(i.sha256)

    mt.make_tree()
    item_proofs = {hashitems[i].id: mt.get_proof(i) for i in range(0, len(hashitems))}
    return mt.get_merkle_root(), item_proofs
