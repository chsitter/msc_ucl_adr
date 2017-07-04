import hashlib
import uuid

import logging

from tierion.db import Account


def create_account(session, name, full_name, secret, do_commit=True):
    salt = uuid.uuid4().hex
    _hash = hashlib.sha512(bytearray(secret + salt, 'utf-8')).hexdigest()
    user = Account(
        name=name,
        fullname=full_name,
        password_hash=_hash,
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


def login(session, account_name, secret):
    res = session.query(Account).filter(Account.name == account_name).all()
    if len(res) == 1:
        acct = res[0]
        salt = acct.salt
        return acct.password_hash == hashlib.sha512(bytearray(secret + salt, 'utf-8')).hexdigest()

    return False
