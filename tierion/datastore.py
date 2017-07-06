from tierion.accounts import *
from tierion.db import DataStore


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



