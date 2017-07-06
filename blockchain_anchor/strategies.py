import logging


class AnchoringStrategy:
    def __init__(self, name: str, description: str):
        logging.debug("Initialising AnchoringStrategy")
        self._name = name
        self._description = description

    def anchor(self, hex_data, backends):
        pass

    def confirm(self, hex_data):
        pass

    def describe(self):
        return "{}: {}".format(self._name, self._description)

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description


class AllAnchorStrategy(AnchoringStrategy):
    def __init__(self):
        super().__init__("all", "This strategy anchors the document to all registered integrations")

    def embed(self, hex_data):
        pass

    def confirm(self, hex_data):
        pass


class AnyAnchorStrategy(AnchoringStrategy):
    def get_name(self):
        return super().get_name()

    def anchor(self, hex_data, backends):
        super().anchor(hex_data, backends)

    def describe(self):
        return super().describe()

    def __init__(self, name: str, description: str):
        super().__init__(name, description)

    def get_description(self):
        return super().get_description()

    def confirm(self, hex_data):
        super().confirm(hex_data)
