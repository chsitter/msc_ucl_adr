class MerkleNode:
    _hash = None

    def __init__(self):
        self._hash = "0x0000"

    def get_hash(self):
        return self._hash


def build_tree(documents):
    return MerkleNode()
