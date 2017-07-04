import json
import sys
from datetime import datetime

import sqlalchemy.exc

from tierion.db import DataStore, Record
from tierion.accounts import *


def get_datastore(session, id=None):
    logging.info("Getting %s", "all datastores" if id is None else "datastore {}".format(id))

    query = session.query(DataStore)
    if id is not None:
        query = query.filter(DataStore.id == id)

    if id is None:
        return query.all()
    else:
        if len(query.all()) == 1:
            return query.all()[0]
        elif len(query.all()) == 0:
            return None
        logging.error("Looking up Datastore for ID %s returned %d items!", id, len(query.all()))
        raise Exception("Somehow ID lookup returned more than 1 item")


def create_datastore(session, name, group_name, redirect_enabled=False, redirect_url=None,
                     email_notification_enabled=False,
                     email_notification_address=None, post_data_enabled=False, post_data_url=None,
                     post_receipt_enabled=False,
                     post_receipt_url=None, do_commit=True):
    """
    :param name:                        The name of the datastore. [Required]
    :param group_name:                  The name of the group of which this datastore is a member.
    :param redirect_enabled: 	        A boolean indicating whether or not the custom redirect URL is enabled.
    :param redirect_url: 	            The URL a user will be redirected to when submitting data from an HTML Form. [Required if redirectEnabled = true]
    :param email_notification_enabled: 	A boolean indicating whether or not the email notification is enabled.
    :param email_notification_address: 	The recipient email address.
    :param post_data_enabled: 	        A boolean indicating whether or not the POST data URL is enabled.
    :param post_data_url: 	            The URL that new record data will be POSTed to when received. [Required if postDataEnabled = true]
    :param post_receipt_enabled: 	    A boolean indicating whether or not the POST receipt URL is enabled.
    :param post_receipt_url: 	        The URL that the blockchain receipt data will be POSTed to when generated. [Required if postReceiptEnabled = true]
    :return: The Datastore created, with the id incremented and a unique key generated, it is important to note that auto_increment requires commiting in between subsequent creates
    """
    ds = DataStore(
        key=str(uuid.uuid5(uuid.NAMESPACE_DNS, name)),
        name=name,
        groupName=group_name,
        redirectEnabled=redirect_enabled,
        redirectUrl=redirect_url,
        emailNotificationEnabled=email_notification_enabled,
        emailNotificationAddress=email_notification_address,
        postDataEnabled=post_data_enabled,
        postDataUrl=post_data_url,
        postReceiptEnabled=post_receipt_enabled,
        postReceiptUrl=post_receipt_url)

    session.add(ds)
    if do_commit:
        session.commit()
    return ds


def update_datastore(session, id, name=None, group_name=None, redirect_enabled=None, redirect_url=None,
                     email_notification_enabled=None,
                     email_notification_address=None, post_data_enabled=None, post_data_url=None,
                     post_receipt_enabled=None,
                     post_receipt_url=None, do_commit=True):
    """
    :param session:                     The db session to be used
    :param id:                          The id of the datastore to be updated
    :param name:                        The name of the datastore. [Required]
    :param group_name:                  The name of the group of which this datastore is a member.
    :param redirect_enabled: 	        A boolean indicating whether or not the custom redirect URL is enabled.
    :param redirect_url: 	            The URL a user will be redirected to when submitting data from an HTML Form. [Required if redirectEnabled = true]
    :param email_notification_enabled: 	A boolean indicating whether or not the email notification is enabled.
    :param email_notification_address: 	The recipient email address.
    :param post_data_enabled: 	        A boolean indicating whether or not the POST data URL is enabled.
    :param post_data_url: 	            The URL that new record data will be POSTed to when received. [Required if postDataEnabled = true]
    :param post_receipt_enabled: 	    A boolean indicating whether or not the POST receipt URL is enabled.
    :param post_receipt_url: 	        The URL that the blockchain receipt data will be POSTed to when generated. [Required if postReceiptEnabled = true]
    :return: The updated Datastore or None if no Datastore for the given ID could be found
    """

    ds = get_datastore(session, id)

    if ds is not None:
        if name is not None:
            ds.name = name
        if group_name is not None:
            ds.groupName = group_name
        if redirect_enabled is not None:
            ds.redirectEnabled = redirect_enabled
        if redirect_url is not None:
            ds.redirectUrl = redirect_url
        if email_notification_enabled is not None:
            ds.emailNotificationEnabled = email_notification_enabled
        if email_notification_address is not None:
            ds.emailNotificationAddress = email_notification_address
        if post_data_enabled is not None:
            ds.postDataEnabled = post_data_enabled
        if post_data_url is not None:
            ds.postDataUrl = post_data_url
        if post_receipt_enabled is not None:
            ds.postReceiptEnabled = post_receipt_enabled
        if post_receipt_url is not None:
            ds.postReceiptUrl = post_receipt_url

        if do_commit:
            session.commit()

    return ds


def delete_datastore(session, id, do_commit=True):
    """
    Deletes and returns a datastore with a given ID from the database
    :param session: The database session to be used
    :param id: The ID of the datastore to be deleted
    :param do_commit: Commits the deletion of the datastore if it was found
    :return: The deleted datastore or None if it did not exist
    """

    datastore = get_datastore(session, id)
    if datastore is not None:
        session.delete(datastore)

        if do_commit:
            session.commit()

    return datastore


def get_record(session, datastoreId=None, page=1, pageSize=100, startDate=None, endDate=None, id=None):
    """
    :param datastoreId: 	A unique numeric identifier for the Datastore from which Records are being requested. [Required]
    :param page: 	        The page number of the Record results to view. If not specified, page will default to 1.
    :param pageSize: 	    The number of Records to include in the Record results, between 1 and 10000. If not specified, pageSize will default to 100.
    :param startDate: 	    A timestamp representing the start of the requested date range for the Record results. If not specified, startDate will default to creation date and time of the Datastore.
    :param endDate: 	    A timestamp representing the end of the requested date range for the Record results. If not specified, endDate will default to the current date and time.
    :param id:              If ID is specified all other arguments are ignored and the record wit the specified ID returned
    :return                 A list of records matching the criteria or the record specified via ID - None on failure
    """

    if id is not None:
        query = session.query(Record).filter(Record.id == id)
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

        query = query.limit(pageSize).offset((page - 1) * pageSize)
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
