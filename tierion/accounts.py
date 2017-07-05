import hashlib
import uuid

import logging

from tierion.db import Account


def create_account(session, name, email, full_name, secret, do_commit=True):
    salt = uuid.uuid4().hex
    user = Account(
        name=name,
        email=email,
        fullname=full_name,
        password_hash=hashlib.sha512(bytearray(secret + salt, 'utf-8')).hexdigest(),
        apiKey=hashlib.sha512(uuid.uuid4().bytes).hexdigest(),
        salt=salt
    )

    session.add(user)
    if do_commit:
        session.commit()

    return user


def get_account(session, account_id):
    query = session.query(Account).filter(Account.id == account_id)

    if len(query.all()) == 1:
        return query.all()[0]
    logging.error("Account query for %s returned %s results", account_id, len(query.all()))
    return None


def delete_account(session, account_id, do_commit=True):
    account = get_account(session, account_id)
    if account is not None:
        session.delete(account)
        if do_commit:
            session.commit()

    return account


def login(session, account=None, secret=None, api_key=None):
    """

    :param session:     Session to be used for database connection
    :param account:     Account to e used, must be email in combination with api_token
    :param secret:      Either secret or api_token must be supplied
    :param api_key:   Either secret or api_token must be supplied
    :return:            True if login successful, False otherwise
    """
    if account is not None:
        if secret is not None:
            res = session.query(Account).filter(Account.name == account).all()
            if len(res) == 1:
                acct = res[0]
                salt = acct.salt
                return acct.password_hash == hashlib.sha512(bytearray(secret + salt, 'utf-8')).hexdigest()

            return False
        elif api_key is not None:
            res = session.query(Account).filter(Account.email == account).all()
            if len(res) == 1:
                acct = res[0]
                return acct.apiKey == api_key
