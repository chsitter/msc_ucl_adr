import json
from math import ceil
from time import time

from flask import request, abort

import tierion.util
from tierion import util


def setup(app, session):
    @app.route('/api/v1/accounts', methods=['POST'])
    @app.route('/api/v1/accounts/<account_name>', methods=['GET', 'DELETE'])
    def accounts(account_name=None):
        if request.method == 'POST':
            account_data = request.json
            tierion.create_account(session, account_data['name'], account_data['email'], account_data['full_name'], account_data['secret'])
            return "Account created"
        elif request.method == 'GET':
            # TODO: Add in Authentication - username and password
            acct = tierion.get_account(session, account_name)
            if acct is None:
                abort(404, "Error: Couldn't find account " + account_name)
            return acct.json_describe()
        elif request.method == "DELETE":
            # TODO: Add in Authentication - username and password
            acct = tierion.delete_account(session, account_name)
            if acct is None:
                abort(404, "Error: Couldn't find account " + account_name)
            return "Account deleted"

    @app.route('/api/v1/login', methods=['POST'])
    def login():
        if request.method == 'POST':
            account_data = request.json
            name = account_data['name']
            secret = account_data['secret']

            if tierion.login(session, name, secret):
                # TODO: need to generate a token and return it to the user
                return "Logged in"
            else:
                abort(403, "Wrong password")

    @app.route('/api/v1/datastores', methods=['GET', 'POST'])
    @app.route('/api/v1/datastores/<datastore_id>', methods=['GET', 'DELETE', "PUT"])
    def datastores(datastore_id=None):
        login_ok, account_id = tierion.login(session, account=request.headers["X-Username"], api_key=request.headers["X-Api-Key"])
        if login_ok is not True:
            abort(403, "User and API Key invalid")

        if request.method == 'GET':
            if datastore_id is None:
                datastores = tierion.get_datastore(session)
                return json.dumps([json.loads(ds.json_describe()) for ds in datastores])
            else:
                datastore = tierion.get_datastore(session, datastore_id)
                if datastore is None:
                    abort(404, "No datastore with ID " + datastore_id + " found")
                return datastore.json_describe()

        elif request.method == "POST":
            if datastore_id is not None:
                abort(401)

            if "name" not in request.json:
                abort(500)

            name = request.json["name"]
            groupname = request.json["groupName"] if "groupName" in request.json else None

            def get_indicator_and_field(indicator_name, field_name):
                indicator = request.json[indicator_name] if indicator_name in request.json else False
                if indicator:
                    if field_name not in request.json:
                        abort(500)
                    value = request.json[field_name]
                    return indicator, value
                return None, None

            redirect_enabled, redirect_url = get_indicator_and_field("redirectEnabled", "redirectUrl")
            email_notification_enabled, email_notification_address = get_indicator_and_field("emailNotificationEnabled",
                                                                                             "emailNotificationAddress")
            post_data_enabled, post_data_url = get_indicator_and_field("postDataEnabled", "postDataUrl")
            post_receipt_enabled, post_receipt_url = get_indicator_and_field("postReceiptEnabled", "postReceiptUrl")

            datastore = tierion.create_datastore(session, name, groupname, redirect_enabled, redirect_url,
                                                 email_notification_enabled, email_notification_address,
                                                 post_data_enabled, post_data_url, post_receipt_enabled,
                                                 post_receipt_url)
            return datastore.json_describe()
        elif request.method == "PUT":
            if datastore_id is None:
                abort(401)

            name = request.json["name"]
            groupname = request.json["groupName"] if "groupName" in request.json else None

            def get_indicator_and_field(indicator_name, field_name):
                indicator = request.json[indicator_name] if indicator_name in request.json else False
                if indicator:
                    if field_name not in request.json:
                        abort(500)
                    value = request.json[field_name]
                    return indicator, value
                return None, None

            redirect_enabled, redirect_url = get_indicator_and_field("redirectEnabled", "redirectUrl")
            email_notification_enabled, email_notification_address = get_indicator_and_field("emailNotificationEnabled",
                                                                                             "emailNotificationAddress")
            post_data_enabled, post_data_url = get_indicator_and_field("postDataEnabled", "postDataUrl")
            post_receipt_enabled, post_receipt_url = get_indicator_and_field("postReceiptEnabled", "postReceiptUrl")

            datastore = tierion.update_datastore(session, datastore_id, name, groupname, redirect_enabled, redirect_url,
                                                 email_notification_enabled, email_notification_address,
                                                 post_data_enabled, post_data_url, post_receipt_enabled,
                                                 post_receipt_url)
            if datastore is None:
                abort(500, "Update failed")
            return datastore.json_describe()

        elif request.method == "DELETE":
            if datastore_id is None:
                abort(401)

            datastore = tierion.delete_datastore(session, datastore_id)
            if datastore is None:
                abort(404)
            return datastore.json_describe()

        abort(501)

    @app.route('/api/v1/records', methods=['GET', 'POST'])
    @app.route('/api/v1/records/<string:record_id>', methods=['GET', 'POST', "DELETE"])
    def records(record_id=None):
        login_ok, account_id = tierion.login(session, account=request.headers["X-Username"], api_key=request.headers["X-Api-Key"])
        if login_ok is not True:
            abort(403, "User and API Key invalid")

        if request.method == "GET":
            if record_id is not None:
                record = tierion.get_record(session, id=record_id)
                if record is None:
                    abort(404, "Record with ID {} not found".format(record_id))
                else:
                    return record.json_describe()
            else:
                if "datastoreId" not in request.args:
                    abort(401, "Required argument datastoreId missing")
                datastore_id = int(request.args["datastoreId"])
                datastore = tierion.get_datastore(session, datastore_id)
                if datastore is None:
                    abort(500, "No datasstore with ID {} found".format(datastore_id))

                page = request.args["page"] if "page" in request.args else 1
                pageSize = int(request.args["pageSize"]) if "pageSize" in request.args else 100
                if pageSize < 1 or pageSize > 10000:
                    abort(401)
                startDate = int(request.args["startDate"] if "startDate" in request.args else "{}".format(int(datastore.timestamp.timestamp())))
                endDate = int(time())

                _records = tierion.get_record(session, datastoreId=datastore_id, page=page, pageSize=pageSize,
                                              startDate=startDate, endDate=endDate)

                response = {
                    "accountId": "TODO",
                    "datastoreId": datastore_id,
                    "page": page,
                    "pageCount": ceil(len(_records) / pageSize),
                    "pageSize": pageSize,
                    "recordCount": len(_records),
                    "startDate": startDate,
                    "endDate": endDate,
                    "records": [json.loads(x.json_describe()) for x in _records]
                }
                return json.dumps(response)

        elif request.method == "POST":
            if record_id is not None:
                abort(401)

            if "datastoreId" not in request.json:
                abort(500)

            datastore_id = request.json["datastoreId"]

            data = request.json
            del data["datastoreId"]
            record = tierion.create_record(session, account_id, datastore_id, data)
            if record is None:
                abort(500, "Something went wrong creating the record")
            return record.json_describe()

        elif request.method == "DELETE":
            if record_id is None:
                abort(401)

            record = tierion.delete_record(session, record_id)

            if record is not None:
                return record.json_describe()
            abort(500)

    @app.route('/api/v1/hashitems', methods=['POST'])
    def hashitems():
        login_ok, acct_id = tierion.login(session, account=request.headers["X-Username"], api_key=request.headers["X-Api-Key"])
        if login_ok is not True:
            abort(403, "User and API Key invalid")

        hex_data = request.json["hash"]
        item = tierion.create_hashitem(session, acct_id, hex_data)
        return item.json_describe()

    @app.route('/api/v1/receipts/<int:receipt_id>', methods=['GET'])
    def receipts(receipt_id):
        login_ok, acct_id = tierion.login(session, account=request.headers["X-Username"], api_key=request.headers["X-Api-Key"])
        if not login_ok:
            abort(403, "User and API Key invalid")

        item = tierion.get_hashitem(session, item_id=receipt_id)
        receipt = util.build_chainpoint_receipt(item)
        return json.dumps(receipt)

    # @app.route('/api/v1/anchor/<int:dsid>', methods=['GET', 'POST'])
    # def anchor(dsid):
    #     if dsid is None:
    #         abort(404)
    #     ds = ds_holder.get(dsid)
    #     if ds is None:
    #         abort(404)
    #
    #     if request.method == "GET":
    #         anchors = anchoring.confirm("0x{}".format(ds.get_merkle_root()))
    #         if anchors is None:
    #             return "Anchorings not yet confirmed"
    #         else:
    #             return json.dumps(chainpoint_util.build_v2_receipt(ds.get_merkle_tree(), anchors))
    #
    #     elif request.method == "POST":
    #         if anchoring.anchor("0x{}".format(ds.get_merkle_root())):
    #             return "Ok"
    #         else:
    #             return "Error"
