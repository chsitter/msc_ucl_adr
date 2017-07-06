import logging


class BlockchainIntegration:
    _name = None

    def __init__(self, name):
        self._name = name

    def anchor(self, hex_data):
        """
        Anchors hex_data into the blockchain that this integration integrates with

        :param hex_data: hex string to be anchored into the blockchain without leading 0x
        :return: transaction id of the TX containing the data or None on error
        """
        logging.info("%s: Embedding data %s", self._name, hex_data)

    def confirm(self, tx_hash):
        """
        Retrieves the block hash of the block the transaction is in as well as additional data, returned as a tuple of
        the form (<block_hash>, <extra_data>)

        How confirmations are defined is defined by the implementation of this interface
        e.g. number of confirmations in Bitcoin

        :param tx_hash: The hash string identifying the transaction returned by the method anchor on the same object
        :return: None on error or (<block_hash>, <optional_extra_data>)
        """
        logging.info("%s: Confirming transaction %s got embedded", self._name, tx_hash)

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name
