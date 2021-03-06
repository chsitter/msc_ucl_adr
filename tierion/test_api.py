import hashlib
import json
from unittest import TestCase
from uuid import uuid4

from tierion import db, datastore, record, accounts, hashitem, _check_queue_fn, RecordState, _check_confirmations_fn
from tierion.db import Record
from tierion.chainpoint_util import build_chainpoint_receipt


class TestDataStoreAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")


    def test_create_datastore(self):
        ds1 = datastore.create_datastore(self.session, self.user.id, "Test1", "TestGroup")
        assert ds1.id is not None

    def test_create_multiple_datastores_get_different_id_and_key(self):
        ds1 = datastore.create_datastore(self.session, self.user.id, "Test1", "TestGroup")
        ds2 = datastore.create_datastore(self.session, self.user.id, "Test2", "TestGroup")

        assert ds1.id != ds2.id
        assert ds1.key != ds2.key

    def test_get_all_datastores(self):
        stores = []
        for i in range(1, 10):
            stores.append(
                datastore.create_datastore(self.session, self.user.id, "Test{}".format(i), "TestGroup"))

        result = datastore.get_datastore(self.session, self.user.id)
        assert len(result) == len(stores)
        assert len({x.id for x in result}) == len(result)  # no ID duplicated
        assert len({x.key for x in result}) == len(result)  # no key duplicated
        assert sorted([x.id for x in stores]) == sorted([x.id for x in result])

    def test_get_specific_datastore(self):
        stores = []
        for i in range(1, 10):
            stores.append(
                datastore.create_datastore(self.session, self.user.id, "Test{}".format(i), "TestGroup"))

        result = datastore.get_datastore(self.session, self.user.id, 1)
        assert isinstance(result, db.DataStore)
        assert result.id == 1

    def test_get_non_existing_datastore(self):
        result = datastore.get_datastore(self.session, self.user.id, 1)
        assert result is None

    def test_update_datastore(self):
        ds = datastore.create_datastore(self.session, self.user.id, "Test1", "TestGroup")
        assert ds.name == "Test1"

        upd = datastore.update_datastore(self.session, self.user.id, ds.id, "Update", "UpdateGroup")
        assert upd.name == "Update"
        assert upd.groupName == "UpdateGroup"

    def test_update_non_existing_datastore(self):
        upd = datastore.update_datastore(self.session, 1, "Update", "UpdateGroup")
        assert upd is None

    def test_delete_datastore(self):
        ds = datastore.create_datastore(self.session, self.user.id, "Test1", "TestGroup")

        deleted = datastore.delete_datastore(self.session, self.user.id, ds.id)
        assert datastore.get_datastore(self.session, self.user.id, ds.id) is None
        assert deleted.id == ds.id
        assert deleted.key == ds.key
        assert deleted.name == ds.name

    def test_delete_non_existing_datastore(self):
        deleted = datastore.delete_datastore(self.session, self.user.id, 1)
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
        login_ok, account_id = accounts.login(self.session, "test", "password")
        assert login_ok is True
        assert account_id is not None
        login_ok, account_id = accounts.login(self.session, "test", "wrong pass")
        assert login_ok is False
        assert account_id is None


class TestRecordAPI(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")
        self.ds1 = datastore.create_datastore(self.session, self.user.id, "Store1", "Testing")
        self.ds2 = datastore.create_datastore(self.session, self.user.id, "Store2", "Testing")

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
        assert r1.hashitem.sha256 != r2.hashitem.sha256

    def test_get_non_existant_record(self):
        assert record.get_record(self.session, self.user.id, id=42) is None

    def test_get_specific_record(self):
        data1 = {"a": "1", "b": "2"}
        data2 = {"a": "1", "b": "3"}
        r1 = record.create_record(self.session, self.user.id, self.ds1.id, data1)
        record.create_record(self.session, self.user.id, self.ds1.id, data2)

        res = record.get_record(self.session, self.user.id, id=r1.id)
        assert isinstance(res, Record)
        assert r1.id == res.id

    def test_get_record_invalid_datastore_returns_none(self):
        data = {"a": "1", "b": "2"}
        record.create_record(self.session, self.user.id, self.ds1.id, data)
        assert len(record.get_record(self.session, self.user.id, datastoreId=42)) == 0

    def test_get_records_paginate(self):
        data = {"a": "1", "b": "2"}
        for i in range(1, 10):
            record.create_record(self.session, self.user.id, self.ds1.id, data)

        p1 = record.get_record(self.session, self.user.id, page=1, pageSize=5)
        p2 = record.get_record(self.session, self.user.id, page=2, pageSize=5)

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

        r1_del = record.delete_record(self.session, self.user.id, record_id=r1.id)
        assert record.get_record(self.session, self.user.id, id=r1.id) is None
        assert r1.id == r1_del.id
        assert r1.hashitem.sha256 == r1_del.hashitem.sha256
        assert record.get_record(self.session, self.user.id, id=r2.id) is not None

    def test_delete_non_existing_record(self):
        assert record.delete_record(self.session, self.user.id, record_id=42) is None


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


class TestAnchorCheckerFunctions(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")
        self.datastore = datastore.create_datastore(self.session, self.user.id, "testDS", "testGroup")

    def test_anchor_cb_is_called_when_queue_size_exceeded_for_hashitems(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored

        _check_queue_fn(test_cb, 4, 600)
        assert to_be_anchored is None
        _check_queue_fn(test_cb, 2, 600)
        assert to_be_anchored is not None

    def test_anchor_cb_is_called_when_age_exceeded_for_hashitems(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored

        _check_queue_fn(test_cb, 4, 600)
        assert to_be_anchored is None
        _check_queue_fn(test_cb, 4, 0)
        assert to_be_anchored is not None

    def test_anchor_cb_is_called_when_queue_size_exceeded_for_records(self):
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0")
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar1")
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar2")
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored

        _check_queue_fn(test_cb, 4, 600)
        assert to_be_anchored is None
        _check_queue_fn(test_cb, 2, 600)
        assert to_be_anchored is not None

    def test_anchor_cb_is_called_when_age_is_exceeded_for_records(self):
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0")
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar1")
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar2")
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored

        _check_queue_fn(test_cb, 4, 600)
        assert to_be_anchored is None
        _check_queue_fn(test_cb, 4, 0)
        assert to_be_anchored is not None

    def test_hashitem_has_merkle_proof_after_anchoring(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored
            return [("ETHData", "0xfakeId")]

        all_items = hashitem.get_hashitem(self.session)
        assert all_items is not None
        assert len(all_items) is 1
        assert all_items[0].proof is None
        assert len(all_items[0].confirmations) == 0
        self.session.rollback()  # why this?

        _check_queue_fn(test_cb, 0, 0)
        assert to_be_anchored is not None

        all_items = hashitem.get_hashitem(self.session)
        assert all_items is not None
        assert len(all_items) is 1
        assert all_items[0].proof is not None
        assert len(all_items[0].confirmations) == 1

    def test_record_has_merkle_proof_and_status_unpublished_after_anchoring(self):
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0")
        to_be_anchored = None

        def test_cb(merkle_root_to_be_anchored):
            nonlocal to_be_anchored
            to_be_anchored = merkle_root_to_be_anchored
            return [("ETHData", "0xfakeId")]

        all_records = record.get_record(self.session, self.user.id)
        assert all_records is not None
        assert len(all_records) is 1
        assert all_records[0].hashitem.proof is None
        assert all_records[0].status == RecordState.QUEUED.value[0]
        assert len(all_records[0].hashitem.confirmations) == 0
        self.session.rollback()  # why this?

        _check_queue_fn(test_cb, 0, 0)
        assert to_be_anchored is not None

        all_records = record.get_record(self.session, self.user.id)
        assert all_records is not None
        assert len(all_records) is 1
        assert all_records[0].hashitem.proof is not None
        assert all_records[0].status == RecordState.UNPUBLISHED.value[0]
        assert len(all_records[0].hashitem.confirmations) == 1

    def test_confirmation_checker_updates_confirmations(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0")
        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0)

        def test_confirmation_cb(endpoint, transaction_id):
            return "0xfakeBlockHash"

        records = record.get_record(self.session, self.user.id)
        hashitems = hashitem.get_hashitem(self.session, self.user.id)
        assert len(records) == 1
        assert len(hashitems) == 2
        record_confirmation = records[0].hashitem.confirmations
        assert len(record_confirmation) == 1
        assert record_confirmation[0].block_header is None
        self.session.rollback()

        _check_confirmations_fn(test_confirmation_cb)

        records = record.get_record(self.session, self.user.id)
        hashitems = hashitem.get_hashitem(self.session, self.user.id)
        assert len(records) == 1
        assert len(hashitems) == 2
        record_confirmation = records[0].hashitem.confirmations
        assert len(record_confirmation) == 1
        assert record_confirmation[0].block_header is not None
        assert hashitems[0].confirmations[0] is not None
        assert hashitems[1].confirmations[0] is not None

    def test_post_receipt_is_not_sent_when_disabled(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0",)
        called = None

        def test_post_cb(url, receipt):
            nonlocal called
            called = (url, receipt)

        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0, post_receipt_cb=test_post_cb)
        assert called is None

    def test_post_receipt_is_sent_when_enabled(self):
        datastore_do_post_receipt = datastore.create_datastore(self.session, self.user.id, "testDS", "testGroup", post_receipt_enabled=True, post_receipt_url="https://foobar")
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        record.create_record(self.session, self.user.id, datastore_do_post_receipt.id, "foobar0",)
        called = None

        def test_post_cb(url, receipt):
            nonlocal called
            called = (url, receipt)

        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0, post_receipt_cb=test_post_cb)
        assert called is not None
        assert called[0] == "https://foobar"

    def test_post_receipt_is_sent_for_correct_records(self):
        datastore_do_post_receipt = datastore.create_datastore(self.session, self.user.id, "testDS", "testGroup", post_receipt_enabled=True, post_receipt_url="https://foobar")
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        record.create_record(self.session, self.user.id, self.datastore.id, "foobar0",)
        record.create_record(self.session, self.user.id, datastore_do_post_receipt.id, "foobar1",)
        called = None
        call_count = 0

        def test_post_cb(url, receipt):
            nonlocal called
            nonlocal call_count
            called = (url, receipt)
            call_count += 1

        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0, post_receipt_cb=test_post_cb)
        assert call_count == 1
        assert called is not None
        assert called[0] == "https://foobar"


class TestUtils(TestCase):
    def setUp(self):
        self.engine = db.init("sqlite:///:memory:", False)

        db.Base.metadata.drop_all(bind=self.engine)
        db.Base.metadata.create_all(bind=self.engine)

        self.session = db.create_session()
        self.user = accounts.create_account(self.session, "tester", "test@test.com", "tester user", "secret")
        self.datastore = datastore.create_datastore(self.session, self.user.id, "testDS", "testGroup")

    def test_create_receipt_for_confirmed_item(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0)
        _check_confirmations_fn(lambda _a, _b: "0xfakeBlockHash")

        hashitems = hashitem.get_hashitem(self.session)
        assert len(hashitems) == 1
        receipt = build_chainpoint_receipt(hashitems[0])
        assert len(receipt["anchors"]) == 1
        assert receipt['anchors'][0] == {'type': 'Ethereum', 'sourceId': '0xfakeTxId'}

    def test_create_receipt_for_item_with_tx_no_block(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())
        _check_queue_fn(lambda _: [("Ethereum", "0xfakeTxId")], 0, 0)

        hashitems = hashitem.get_hashitem(self.session)
        assert len(hashitems) == 1
        receipt = build_chainpoint_receipt(hashitems[0])
        assert len(receipt["anchors"]) == 1
        assert receipt['anchors'][0] == {'type': 'Ethereum', 'sourceId': '0xfakeTxId'}

    def test_create_receipt_for_item_no_tx_no_block(self):
        hashitem.create_hashitem(self.session, self.user.id, hashlib.sha256(uuid4().bytes).hexdigest())

        hashitems = hashitem.get_hashitem(self.session)
        assert len(hashitems) == 1
        receipt = build_chainpoint_receipt(hashitems[0])
        assert len(receipt["anchors"]) == 0
