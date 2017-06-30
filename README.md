The Library is implemented using python3 and the requirements are specified in requirements.txt
    - install requirements with pip3 install -r requirements.txt

The main.py file does the wiring up as well as configuring the anchoring library, default implementations depend on running a geth with the ipc interface enabled and bitcoind running with the rpc interface enabled
Default config points to my regtest backend accounts, will need to be changed

REST API Spec:
 - HTTP Authentication or user management not yet implemented, so all requests default to the same user
 - supported URLS and operations are taken from https://tierion.com/docs/dataapi with most operations being supported as specified by their API
    - http://127.0.0.1:5000/api/v1/datastores                   -- [GET, POST]
    - http://127.0.0.1:5000/api/v1/datastores/<int:datastoreId> -- [GET, DELETE]
    - http://127.0.0.1:5000/api/v1/records                      -- [GET, POST]
    - http://127.0.0.1:5000/api/v1/records/<string:recordId>    -- [GET, POST, DELETE]
- message spec is exactly as is defined in the Tierion Data API


Current Library behaviour:
    - creating a document queues the document for anchoring at a later point in time
    - on the 3rd (hard coded as of now) document in the queue anchoring the three documents in one transaction (merkle tree with 3 leafs) is triggered
        - once documents are sent, they enter the state unpublished (not sure what the states exactly mean in the tierion api)
    - all documents that are unpublished get checked for anchor confirmations on every get request
        - if confirmations are available (depending on strategy) the receipt will be generated and associated with the record
        - if confirmations are not yet available then documents remain in the pending list and get checked again on the next get request


The anchoring library is designed in a way such that it supports:
    - changing the blockchain integrations easily (interfaces between components need clearer definition still)
    - strategies can be implemented and added, currently only available strategy is 'all' meaning that it only confirms once the hash has been anchored with all available backends
        - can easily be extended via configuration
