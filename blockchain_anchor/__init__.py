import logging
import blockchain_anchor.backends
import blockchain_anchor.strategies

from blockchain_anchor.cache import DocumentCache


class Anchoring:
    def __init__(self, strategies):
        self._strategies = strategies
        self._strategy_status = {x: None for x in self._strategies.keys()}

    def get_anchoring_strategies(self):
        return self._strategies.values()

    def anchor(self, strategy_name, doc, do_hash):
        if strategy_name is None:
            # TODO: implement a default strategy
            raise Exception("This should default to a default strategy tagged in the config")
        else:
            self._strategies[strategy_name].anchor(user, doc, do_hash)

    def get_strategy_backend_status(self, strategy=None):
        res = {strategy: self._strategies[strategy].test_backend_connections()}


def init_anchor(config: object) -> Anchoring:
    """
    This function creates an Anchoring object that is constructed according to the configuration supplied
    The configuration object is of the form
        config = {
            "backends": {
                "Ethereum": backends.EthereumIntegration,
                "Bitcoin": backends.BitcoinIntegration
            },
            "backend_config": {
                "Ethereum": {
                    "host": "localhost",
                    "port": 8079,
                },
                "Bitcoin": {
                    "user": "bitcoinrpc",
                    "secret": "c8805869db20730a2ddb7f62cfa2745c",
                    "host": "localhost",
                    "port": 18332,
                }
            },
            "anchoring_strategies": [strategies.BasicAnchoringStrategy],
            "caching": {
                "max_size": 10,
                "max_age": 2
            }
        }

    :param config: configuration object
    :return: Anchoring object initialised according to config
    """
    backends = {}
    strategies = {}
    for backend_name, backend_impl in config["backends"].items():
        if backend_name not in config["backend_config"]:
            logging.error("Couldn't find config for backend named %s", backend_name)
            raise Exception("Config invalid")
        backends[backend_name] = backend_impl(**config["backend_config"][backend_name])

    for strategy in config["anchoring_strategies"]:
        s = strategy(backends, DocumentCache(**config["caching"]))
        strategies[s.get_name()] = s

    if len(strategies) == 0:
        logging.error("No strategies configured, cannot create Anchoring instance")
        raise Exception("Config invalid")

    return Anchoring(strategies)




    # from bc_anchor.strategies import BasicAnchoringStrategy
    #
    # __STRATEGIES__ = BasicAnchoringStrategy()


    #
    # s = strategy.BasicAnchoringStrategy()
    # # s.register_backend(backends.EthereumIntegration(config["Ethereum"]["host"], config["Ethereum"]["port"]))
    # s.register_backend(backends.BitcoinIntegration(**config["Bitcoin"]))
    #
    # cp = chainpoint.ChainPoint(s)
    #
    #
    # def print_receipts(receipts):
    #     import pprint
    #     pp = pprint.PrettyPrinter(indent=4)
    #     for target_hash, receipt in receipts.items():
    #         print("{}:".format(target_hash))
    #         pp.pprint(receipt)
    #         print()
    #         print("-------------------")
    #         print()
    #
    #
    # cp.anchor(["Foo", "Bar", "Baz"], lambda res: print(res))
