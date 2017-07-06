import hashlib
import json
from unittest import TestCase
from uuid import uuid4

from tierion import db, datastore, record, accounts, hashitem
from tierion.db import Record


class TestDataStoreAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()

    def test_create_datastore(self):
        ds1 = datastore.create_datastore(self.session, "Test1", "TestGroup")
        assert ds1.id is not None

    def test_create_multiple_datastores_get_different_id_and_key(self):
        ds1 = datastore.create_datastore(self.session, "Test1", "TestGroup")
        ds2 = datastore.create_datastore(self.session, "Test2", "TestGroup")

        assert ds1.id != ds2.id
        assert ds1.key != ds2.key

    def test_get_all_datastores(self):
        stores = []
        for i in range(1, 10):
            stores.append(
                datastore.create_datastore(self.session, "Test{}".format(i), "TestGroup"))

        result = datastore.get_datastore(self.session)
        assert len(result) == len(stores)
        assert len({x.id for x in result}) == len(result)  # no ID duplicated
        assert len({x.key for x in result}) == len(result)  # no key duplicated
        assert sorted([x.id for x in stores]) == sorted([x.id for x in result])

    def test_get_specific_datastore(self):
        stores = []
        for i in range(1, 10):
            stores.append(
                datastore.create_datastore(self.session, "Test{}".format(i), "TestGroup"))

        result = datastore.get_datastore(self.session, 1)
        assert isinstance(result, db.DataStore)
        assert result.id == 1

    def test_get_non_existing_datastore(self):
        result = datastore.get_datastore(self.session, 1)
        assert result is None

    def test_update_datastore(self):
        ds = datastore.create_datastore(self.session, "Test1", "TestGroup")
        assert ds.name == "Test1"

        upd = datastore.update_datastore(self.session, ds.id, "Update", "UpdateGroup")
        assert upd.name == "Update"
        assert upd.groupName == "UpdateGroup"

    def test_update_non_existing_datastore(self):
        upd = datastore.update_datastore(self.session, 1, "Update", "UpdateGroup")
        assert upd is None

    def test_delete_datastore(self):
        ds = datastore.create_datastore(self.session, "Test1", "TestGroup")

        deleted = datastore.delete_datastore(self.session, ds.id)
        assert datastore.get_datastore(self.session, ds.id) is None
        assert deleted.id == ds.id
        assert deleted.key == ds.key
        assert deleted.name == ds.name

    def test_delete_non_existing_datastore(self):
        deleted = datastore.delete_datastore(self.session, 1)
        assert deleted is None


class TestAccountsAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)
        self.session = db.create_session()

    def test_create_user_and_log_in(self):
        acct = accounts.create_account(self.session, "test", "test@test.com", "test user", "password")

        assert acct is not None
        assert accounts.login(self.session, "test", "password") is True
        assert accounts.login(self.session, "test", "wrong pass") is False


class TestRecordAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")
        self.ds1 = datastore.create_datastore(self.session, "Store1", "Testing")
        self.ds2 = datastore.create_datastore(self.session, "Store2", "Testing")

    def test_create_record(self):
        data = {"a": "1", "b": "2"}
        r = record.create_record(self.session, self.user.id, self.ds1.id, data)

        assert r is not None
        assert r.json == json.dumps(data)

    def test_create_two_records(self):
        data1 = {"a": "1", "b": "2"}
        data2 = {"a": "1", "b": "3"}
        r1 = record.create_record(self.session, self.user.id, self.ds1.id, data1)
        r2 = record.create_record(self.session, self.user.id, self.ds1.id, data2)
        assert r1.id != r2.id
        assert r1.json != r2.json
        assert r1.sha256 != r2.sha256

    def test_get_non_existant_record(self):
        assert record.get_record(self.session, id=42) is None

    def test_get_specific_record(self):
        data1 = {"a": "1", "b": "2"}
        data2 = {"a": "1", "b": "3"}
        r1 = record.create_record(self.session, self.user.id, self.ds1.id, data1)
        record.create_record(self.session, self.user.id, self.ds1.id, data2)

        res = record.get_record(self.session, id=r1.id)
        assert isinstance(res, Record)
        assert r1.id == res.id

    def test_get_record_invalid_datastore_returns_none(self):
        data = {"a": "1", "b": "2"}
        record.create_record(self.session, self.user.id, self.ds1.id, data)
        assert len(record.get_record(self.session, datastoreId=42)) == 0

    def test_get_records_paginate(self):
        data = {"a": "1", "b": "2"}
        for i in range(1, 10):
            record.create_record(self.session, self.user.id, self.ds1.id, data)

        p1 = record.get_record(self.session, page=1, pageSize=5)
        p2 = record.get_record(self.session, page=2, pageSize=5)

        assert len(p1) == 5
        assert len(p2) == 4

    def test_get_records_date_filter(self):
        # TODO: gotta test that one
        pass

    def test_create_record_invalid_datastore(self):
        assert record.create_record(self.session, self.user.id, -1, {}) is None

    def test_create_record_invalid_account(self):
        assert record.create_record(self.session, 42, self.ds1.id, {}) is None

    def test_delete_record(self):
        data = {"a": "1", "b": "2"}
        r1 = record.create_record(self.session, self.user.id, self.ds1.id, data)
        r2 = record.create_record(self.session, self.user.id, self.ds1.id, data)

        r1_del = record.delete_record(self.session, record_id=r1.id)
        assert record.get_record(self.session, id=r1.id) is None
        assert r1.id == r1_del.id
        assert r1.sha256 == r1_del.sha256
        assert record.get_record(self.session, id=r2.id) is not None

    def test_delete_non_existing_record(self):
        assert record.delete_record(self.session, record_id=42) is None


class TestHashAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")

    def test_create_hashitem(self):
        hex_data = hashlib.sha256(uuid4().bytes).hexdigest()
        item = hashitem.create_hashitem(self.session, self.user.id, hex_data)

        assert item is not None
        assert item.sha256 == hex_data

    def test_get_pending_hashitems(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())

        items = hashitem.get_hashitem(self.session, pending=True)

        assert len(items) == 2

    def test_get_not_pending_hashitems(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())

        items = hashitem.get_hashitem(self.session, pending=False)

        assert len(items) == 0
