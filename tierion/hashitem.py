import logging
import sys
import uuid

import sqlalchemy.exc

from tierion.db import HashItem
from datetime import datetime


def create_hashitem(session, account_id, hex_data, do_commit=True):
    item = HashItem(accountId=account_id, sha256=hex_data)
    session.add(item)

    if do_commit:
        try:
            session.commit()
        except sqlalchemy.exc.InterfaceError:
            logging.error("Error creating record: %s", sys.exc_info())
            session.rollback()
            item = None

    return item


def get_hashitem(session, page=1, pageSize=100, startDate=None, endDate=None, item_id=None, pending=None, for_update=False):
    if item_id is not None:
        query = session.query(HashItem).filter(HashItem.id == item_id)
        if for_update:
            query.with_for_update()
        if len(query.all()) == 1:
            return query.all()[0]
        logging.error("Query for HashItem with id %s returned %s results", item_id, len(query.all()))
        return None
    else:
        query = session.query(HashItem)
        if startDate is not None:
            query = query.filter(HashItem.timestamp > datetime.fromtimestamp(startDate))
        if endDate is not None:
            query = query.filter(HashItem.timestamp < datetime.fromtimestamp(endDate))
        if pending is not None:
            query = query.filter(~HashItem.confirmations.any() if pending else HashItem.confirmations.any())

        query = query.limit(pageSize).offset((page - 1) * pageSize)
        if for_update:
            query.with_for_update()
        return query.all()


def get_receipt(session, receipt_id):
    res = session.query(HashItem).filter(HashItem.receipt_id == receipt_id).all()

    if len(res) == 1:
        item = res[0]

        # receipt = util.build_chainpoint_receipt(merkle_root, proof, item.sha256, anchors)
        return None
    else:
        logging.error("Query for receipt {} returned {} items", receipt_id, len(res))
        return None
