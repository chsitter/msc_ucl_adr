# from unittest import TestCase
#
# from blockchain_anchor import datastore
#
#
# class TestDataStores(TestCase):
#     def setUp(self):
#         self.ds = datastore.DataStores(None)
#
#     def test_create_datastore(self):
#         ds1 = self.ds.create_datastore("Test1")
#         ds2 = self.ds.create_datastore("Test2")
#
#         assert ds1.id != ds2.id
#
#     def test_get_merkle_root(self):
#         ds = self.ds.create_datastore("Test")
#         ds.add_document("Doc1", True)
#         ds.add_document("Doc2", True)
#
#         assert ds.get_merkle_root() == ds.get_merkle_root()
#
#     def test_get_datastore(self):
#         ds = self.ds.create_datastore("Test")
#
#         assert self.ds.get(ds.id) == ds
#         assert self.ds.get(-1) is None
#
#     def test_get_merkle_tree_count_leaves(self):
#         ds = self.ds.create_datastore("Test")
#         ds.add_document("Doc1", True)
#         ds.add_document("Doc2", True)
#
#         mt = ds.get_merkle_tree()
#         assert mt.get_leaf_count() == 2
#
#     def test_get_documents(self):
#         ds = self.ds.create_datastore("Test")
#
#         ds.add_document("Doc1", True)
#         ds.add_document("Doc2", True)
#
#         assert len(ds.documents) == 2