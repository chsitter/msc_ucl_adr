import logging
import sys
from datetime import datetime

import sqlalchemy.exc

from tierion.db import HashItem


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


def get_hashitem(session, account_id=None, page=1, page_size=100, start_date=None, end_date=None, item_id=None, pending=None, for_update=False):
    query = session.query(HashItem)
    if account_id is not None:
        query.filter(HashItem.accountId == account_id)

    if item_id is not None:
        query = query.filter(HashItem.id == item_id)
        if for_update:
            query.with_for_update()
        if len(query.all()) == 1:
            return query.all()[0]
        logging.error("Query for HashItem with id %s returned %s results", item_id, len(query.all()))
        return None
    else:
        if start_date is not None:
            query = query.filter(HashItem.timestamp > datetime.fromtimestamp(start_date))
        if end_date is not None:
            query = query.filter(HashItem.timestamp < datetime.fromtimestamp(end_date))
        if pending is not None:
            query = query.filter(~HashItem.confirmations.any() if pending else HashItem.confirmations.any())

        query = query.limit(page_size).offset((page - 1) * page_size)
        if for_update:
            query.with_for_update()
        return query.all()


# def get_receipt(session, receipt_id):
#     res = session.query(HashItem).filter(HashItem.receipt_id == receipt_id).all()
#
#     if len(res) == 1:
#         item = res[0]
#
#         # receipt = util.build_chainpoint_receipt(merkle_root, proof, item.sha256, anchors)
#         return None
#     else:
#         logging.error("Query for receipt {} returned {} items", receipt_id, len(res))
#         return None
