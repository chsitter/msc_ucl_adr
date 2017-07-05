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
from tierion.record import create_record, delete_record, get_record, RecordState


def _check_queue_fn(callback, queue_max_size, record_max_age):
    logging.debug("Checking queue (max_size: %d, max_age: %d)", queue_max_size, record_max_age)
    session = db.create_session()

    end_date = int((datetime.now() - timedelta(seconds=record_max_age)).timestamp())
    have_expired_records = len(get_record(session, status='queued', endDate=end_date)) > 0
    session.rollback()

    queued_records = get_record(session, status='queued', for_update=True)

    if len(queued_records) >= queue_max_size or have_expired_records:
        sent = callback(queued_records)

        if sent:
            for r in queued_records:
                r.status = RecordState.UNPUBLISHED.value[0]  # TODO: why [0]?
                session.add(r)
            session.commit()
        else:
            session.rollback()
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
    thr.start()
    return thr


def stop_anchoring_timer(timer_thread: QueueCheckerThread):
    logging.info("Stopping QueueChecker Thread")
    timer_thread.stop()


def build_merkle_tree(records):
    """
    Builds a merkletools merkle tree from the list of records passed in
    :param records:
    :return:
    """
    logging.debug("Building merkle tree for {} records".format(records))
    mt = merkletools.MerkleTools()
    for r in records:
        mt.add_leaf(r.sha256)
    mt.make_tree()

    return [r.id for r in records], mt
