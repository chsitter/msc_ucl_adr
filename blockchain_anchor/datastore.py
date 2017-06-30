import json
from enum import Enum
from time import time

import merkletools

from blockchain_anchor import chainpoint_util


class DataStore:
    def __init__(self, datastore_id, name, group_name, redirect_enabled, redirect_url, email_notification_enabled,
                 email_notification_address, post_data_enabled, post_data_url, post_receipt_enabled,
                 post_receipt_url):
        self.id = datastore_id
        self.key = "key-{}".format(self.id)
        self.name = name
        self.groupName = group_name
        self.emailNotificationEnabled = email_notification_enabled
        self.emailNotificationAddress = email_notification_address
        self.postReceiptEnabled = post_receipt_enabled
        self.postReceiptUrl = post_receipt_url
        self.postDataEnabled = post_data_enabled
        self.postDataURL = post_data_url
        self.redirectEnabled = redirect_enabled
        self.redirectUrl = redirect_url
        self.created_timestamp = time()

        self.records = []
        self.tree_built = False
        self.mt = merkletools.MerkleTools()

    def add_record(self, record):
        self.records.append(record)
        return record

    def del_record(self, record_id):
        raise Exception("Not yet supported")

    def get_record(self, record_id):
        return [x for x in self.records if x.id == record_id][0]

    def get_records(self, page=None, page_size=None, start_date=None, end_date=None):
        # TODO: Pagination and all this crap
        return self.records

    def json_describe(self):
        return json.dumps({
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "groupName": self.groupName,
            "redirectEnabled": self.redirectEnabled,
            "redirectUrl": self.redirectUrl,
            "emailNotificationEnabled": self.emailNotificationEnabled,
            "emailNotificationAddress": self.emailNotificationAddress,
            "postDataEnabled": self.postDataEnabled,
            "postDataUrl": self.postDataURL,
            "postReceiptEnabled": self.postReceiptEnabled,
            "postReceiptUrl": self.postReceiptUrl,
            "timestamp": self.created_timestamp
        })


class RecordState(Enum):
    QUEUED = 'queued',
    UNPUBLISHED = 'unpublished',
    COMPLETE = 'complete'


class Record:
    def __init__(self, record_id, account_id, datastore_id, status: RecordState, data, json, sha256):
        self.id = record_id
        self.accountId = account_id
        self.datastoreId = datastore_id
        self.status = status

        self.data = data
        self.json = json
        self.sha256 = sha256
        self.timestamp = time()
        self.blockchain_receipt = None
        self.insights = None
        self.proof = None
        self.merkle_root = None

    def set_proof(self, proof):
        self.proof = proof

    def get_proof(self):
        return self.proof

    def set_merkle_root(self, merkle_root):
        self.merkle_root = merkle_root

    def set_receipt(self, receipt):
        self.blockchain_receipt = receipt

    def json_describe(self):
        return json.dumps({
            "id": self.id,
            "accountId": self.accountId,
            "datastoreId": self.datastoreId,
            "status": self.status.value,
            "data": self.data,
            "json": self.json,
            "sha256": self.sha256,
            "timestamp": self.timestamp,
            "blockchain_receipt": self.blockchain_receipt
        })


class DataStores:
    def __init__(self, anchor):
        self.datastores = {}
        self.next_datastore_id = 0
        self.records = {}
        self.next_record_id = 0
        self.merkle_tree = merkletools.MerkleTools()
        self.queued_records = {}
        self.pending_records = {}
        self.anchor = anchor

    def create_datastore(self, name, group_name, redirect_enabled, redirect_url, email_notification_enabled,
                         email_notification_address, post_data_enabled, post_data_url, post_receipt_enabled,
                         post_receipt_url):
        """
        :param name:                        The name of the datastore. [Required]
        :param group_name:                   The name of the group of which this datastore is a member.
        :param redirect_enabled: 	        A boolean indicating whether or not the custom redirect URL is enabled.
        :param redirect_url: 	            The URL a user will be redirected to when submitting data from an HTML Form. [Required if redirectEnabled = true]
        :param email_notification_enabled: 	A boolean indicating whether or not the email notification is enabled.
        :param email_notification_address: 	The recipient email address.
        :param post_data_enabled: 	        A boolean indicating whether or not the POST data URL is enabled.
        :param post_data_url: 	            The URL that new record data will be POSTed to when received. [Required if postDataEnabled = true]
        :param post_receipt_enabled: 	        A boolean indicating whether or not the POST receipt URL is enabled.
        :param post_receipt_url: 	            The URL that the blockchain receipt data will be POSTed to when generated. [Required if postReceiptEnabled = true]
        :return:
        """
        ds = DataStore(self.next_datastore_id, name, group_name, redirect_enabled, redirect_url,
                       email_notification_enabled,
                       email_notification_address, post_data_enabled, post_data_url, post_receipt_enabled,
                       post_receipt_url)
        self.datastores[self.next_datastore_id] = ds
        self.next_datastore_id += 1
        return ds

    def get(self, dsid=None):
        if dsid is None:
            return [x for x in self.datastores]
        elif dsid in self.datastores:
            return self.datastores[dsid]
        else:
            return None

    def delete(self, dsid):
        ds = self.datastores[dsid]
        del self.datastores[dsid]
        return ds

    def create_record(self, account_id, datastore_id, data):
        record_id = self.next_record_id
        self.next_record_id += 1
        json_data = json.dumps(data)
        self.merkle_tree.add_leaf(json_data, True)
        sha256 = self.merkle_tree.get_leaf(self.merkle_tree.get_leaf_count() - 1)
        record = Record(record_id, account_id, datastore_id, RecordState.QUEUED, data, json_data, sha256)

        self.records[str(record_id)] = record
        self.queued_records[(str(record_id), record.sha256)] = record

        if self.merkle_tree.get_leaf_count() >= 3:
            self.merkle_tree.make_tree()

            if self.anchor.anchor("0x{}".format(self.merkle_tree.get_merkle_root())):
                for i in range(0, self.merkle_tree.get_leaf_count()):
                    rec = [self.records[_id] for _id, sha in self.queued_records if sha == self.merkle_tree.get_leaf(i)][0]
                    rec.set_proof(self.merkle_tree.get_proof(i))
                    rec.set_merkle_root(self.merkle_tree.get_merkle_root())
                    rec.status = RecordState.UNPUBLISHED
                    del self.queued_records[(str(rec.id), rec.sha256)]
                    if self.merkle_tree.get_merkle_root() not in self.pending_records:
                        self.pending_records[self.merkle_tree.get_merkle_root()] = []
                    self.pending_records[self.merkle_tree.get_merkle_root()].append(rec.id)

                self.merkle_tree = merkletools.MerkleTools()
                self.queued_records = {}
            else:
                # TODO: handle error case
                pass

        return record

    def pocess_pending_records(self):
        completed_anchorings = []
        for merkle_root in self.pending_records:
            anchors = self.anchor.confirm("0x{}".format(merkle_root))
            if anchors is not None:
                for rec_id in self.pending_records[merkle_root]:
                    rec = self.records[str(rec_id)]
                    receipt = chainpoint_util.build_v2_receipt_single(merkle_root, rec.proof, rec.sha256, anchors)
                    rec.set_receipt(receipt)
                    rec.status = RecordState.COMPLETE
                completed_anchorings.append(merkle_root)

        for tmp in completed_anchorings:
            del self.pending_records[tmp]

    def delete_record(self, record_id):
        if record_id not in self.records:
            return None

        record = self.records[str(record_id)]
        del self.records[str(record_id)]
        return record

    def get_record(self, record_id):
        if record_id not in self.records:
            return None
        return self.records[str(record_id)]
