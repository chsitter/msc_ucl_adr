import hashlib
import json
import logging
import sys
import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy.exc

from tierion import get_datastore, get_account
from tierion.db import Record


class RecordState(Enum):
    QUEUED = 'queued',
    UNPUBLISHED = 'unpublished',
    COMPLETE = 'complete'


def get_record(session, datastoreId=None, page=1, pageSize=100, startDate=None, endDate=None, status=None, id=None,
               for_update=False):
    """
    :param datastoreId: 	A unique numeric identifier for the Datastore from which Records are being requested. [Required]
    :param page: 	        The page number of the Record results to view. If not specified, page will default to 1.
    :param pageSize: 	    The number of Records to include in the Record results, between 1 and 10000. If not specified, pageSize will default to 100.
    :param startDate: 	    A timestamp representing the start of the requested date range for the Record results. If not specified, startDate will default to creation date and time of the Datastore.
    :param endDate: 	    A timestamp representing the end of the requested date range for the Record results. If not specified, endDate will default to the current date and time.
    :param id:              If ID is specified all other arguments are ignored and the record wit the specified ID returned
    :param for_update       If set to true, the select is executed with the for update modifier to lock all selected rows
    :return                 A list of records matching the criteria or the record specified via ID - None on failure
    """

    if id is not None:
        query = session.query(Record).filter(Record.id == id)
        if for_update:
            query.with_for_update()
        if len(query.all()) == 1:
            return query.all()[0]
        logging.error("Query for Record with ID %s returned %s results", id, len(query.all()))
        return None
    else:
        query = session.query(Record)
        if datastoreId is not None:
            query = query.filter(Record.datastoreId == datastoreId)
        if startDate is not None:
            query = query.filter(Record.timestamp > datetime.fromtimestamp(startDate))
        if endDate is not None:
            query = query.filter(Record.timestamp < datetime.fromtimestamp(endDate))
        if status is not None:
            query = query.filter(Record.status == status)

        query = query.limit(pageSize).offset((page - 1) * pageSize)
        if for_update:
            query.with_for_update()
        return query.all()


def create_record(session, account_id, datastore_id, data, status='queued', do_commit=True):
    """
    :param session:                     The session to be used for the DB connection
    :param account_id:	                A unique numeric identifier for the Account associated with this Record.
    :param datastore_id: 	            A unique numeric identifier for the Datastore associated with this Record.
    :param data:                        A dynamic collection of key/value pairs representing the custom data received for this Record.
    :param status:                      The records status, default is 'queued'
    :param do_commit:                   Whether to commit the transaction or not
    ":return:                           The created record or None on failure
    """

    ds = get_datastore(session, datastore_id)
    user = get_account(session, account_id)
    if ds is None:
        logging.error("DataStore %s does not exist!", datastore_id)
        return None
    if user is None:
        logging.error("User %s does not exist!", account_id)
        return None

    _json = json.dumps(data)
    rec = Record(
        id=str(uuid.uuid4()),
        accountId=account_id,
        datastoreId=datastore_id,
        status=status,
        data=data,
        json=_json,
        sha256=hashlib.sha256(bytearray(_json, 'utf-8')).hexdigest()
    )
    ds.records.append(rec)
    user.records.append(rec)

    session.add(rec)
    if do_commit:
        try:
            session.commit()
        except sqlalchemy.exc.InterfaceError:
            logging.error("Error creating record: %s", sys.exc_info())
            session.rollback()
            rec = None

    return rec


def delete_record(session, record_id, do_commit=True):
    """

    :param session:     The session to be used to communicate with the DB
    :param record_id:          The ID of the record to be deleted
    :param do_commit:   Whether to commit the deletion or not, defaults to True
    :return:            The deleted record or None if it did not exist
    """
    record = get_record(session, id=record_id)

    if record is not None:
        session.delete(record)
        if do_commit:
            session.commit()

    return record
