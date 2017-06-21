import logging


class BlockchainIntegration:
    _name = None

    def __init__(self, name):
        self._name = name

    def test_connection(self):
        logging.info("%s: Testing connection", self._name)

    def embed(self, hex_data):
        """
        Embeds the data hex_data with the Blockchain this integration integrates with

        :param hex_data: hex data to be anchored into the blockchain
        :return: transaction id of the TX containing the data
        """
        logging.info("%s: Embedding data %s", self._name, hex_data)

    def confirm(self, tx_hash):
        logging.info("%s: Confirming transaction %s got embedded", self._name, tx_hash)

    def get_name(self):
        return self._name
