import logging

import blockchain_anchor.backends
from blockchain_anchor.strategies import AnchoringStrategy


class Anchoring:
    _pending_anchorings = {}

    def __init__(self, strategies, default_strategy=None):
        self._strategies = strategies
        self._default_strategy = self._strategies[default_strategy] if default_strategy is not None else None
        if self._default_strategy is None:
            logging.warning("No default strategy specified")

    def get_anchoring_strategies(self):
        return self._strategies.values()

    def anchor(self, hex_data, strategy_name=None):
        strategy = self._default_strategy if strategy_name is None else self._strategies[strategy_name]
        assert isinstance(strategy, AnchoringStrategy)

        if hex_data not in self._pending_anchorings:
            self._pending_anchorings[hex_data] = strategy.get_name()
            strategy.embed(hex_data)
            return True
        else:
            logging.warning("Ignoring anchoring attempt for data %s as it's already pending anchoring", hex_data)
            return False

    def confirm(self, hex_data):
        if hex_data not in self._pending_anchorings:
            logging.error("Can't confirm anchoring for %s as it's not pending confirmation")
        else:
            strategy = self._strategies[self._pending_anchorings[hex_data]]
            confirmations = strategy.confirm(hex_data)

            if None not in confirmations.values():
                del self._pending_anchorings[hex_data]
                return confirmations

        return None


def init_anchor(config: dict, default_strategy: str = None) -> Anchoring:
    _integrations = {}
    _strategies = {}

    for name, (cls, args) in config["backends"].items():
        _integrations[name] = cls(**args)

    for name, cls in config["strategies"].items():
        _strategies[name] = cls(_integrations)

    return Anchoring(_strategies, default_strategy)
