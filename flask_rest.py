import json
from time import time

from flask import request, abort
from math import ceil

from blockchain_anchor import Anchoring, chainpoint_util
from blockchain_anchor.datastore import DataStores


def setup(app, anchoring: Anchoring, ds_holder: DataStores):
    @app.route('/api/v1/strategies', methods=['GET'])
    def strategies():
        if request.method == 'GET':
            return json.dumps({x.get_name(): x.get_description() for x in anchoring.get_anchoring_strategies()})

    @app.route('/api/v1/datastores', methods=['GET', 'POST'])
    @app.route('/api/v1/datastores/<int:dsid>', methods=['GET', 'DELETE', "PUT"])
    def datastores(dsid=None):
        if request.method == 'GET':
            ds_holder.pocess_pending_records()  # TODO: this should really be done on a timer
            if dsid is None:
                return json.dumps([ds_holder.get(_id).json_describe() for _id in ds_holder.get()])
            ds = ds_holder.get(dsid)
            if ds is None:
                abort(404)
            return ds.json_describe()

        elif request.method == "POST":
            if dsid is not None:
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

            ds = ds_holder.create_datastore(name, groupname, redirect_enabled, redirect_url, email_notification_enabled,
                                            email_notification_address, post_data_enabled, post_data_url,
                                            post_receipt_enabled, post_receipt_url)
            return ds.json_describe()
        elif request.method == "DELETE":
            if dsid is None:
                abort(401)

            ds = ds_holder.delete(dsid)
            if ds is None:
                abort(404)
            return ds.json_describe()

        abort(501)

    @app.route('/api/v1/records', methods=['GET', 'POST'])
    @app.route('/api/v1/records/<string:record_id>', methods=['GET', 'POST', "DELETE"])
    def records(record_id=None):
        if request.method == "GET":
            ds_holder.pocess_pending_records()  # TODO: this should really be done on a timer

            if record_id is not None:
                # TODO: gotta find the record in the DS - need some sort of mapping?
                record = ds_holder.get_record(record_id)
                if record is None:
                    abort(404)
                else:
                    return record.json_describe()
            else:
                if "datastoreId" not in request.args:
                    abort(401)
                dsid = int(request.args["datastoreId"])
                ds = ds_holder.get(dsid)
                if ds is None:
                    abort(500)

                page = request.args["page"] if "page" in request.args else 1
                pageSize = int(request.args["pageSize"]) if "pageSize" in request.args else 100
                if pageSize < 1 or pageSize > 10000:
                    abort(401)
                startDate = request.args["startDate"] if "startDate" in request.args else ds.created_timestamp
                endDate = time()

                docs = ds.get_records(page, pageSize, startDate, endDate)

                response = {
                    "accountId": 1,
                    "datastoreId": dsid,
                    "page": page,
                    "pageCount": ceil(len(ds.get_records()) / pageSize),
                    "pageSize": pageSize,
                    "recordCount": len(ds.get_records()),
                    "startDate": startDate,
                    "endDate": endDate,
                    "records": [json.loads(x.json_describe()) for x in docs]
                }
                return json.dumps(response)

        elif request.method == "POST":
            if record_id is not None:
                abort(401)

            if "datastoreId" not in request.json:
                abort(500)

            datastore_id = request.json["datastoreId"]
            if datastore_id not in ds_holder.datastores:
                abort(404)

            ds = ds_holder.datastores[datastore_id]
            data = request.json
            del data["datastoreId"]

            # TODO: use real acct no instead of 42
            record = ds_holder.create_record(42, datastore_id, data)
            record = ds.add_record(record)
            return record.json_describe()

        elif request.method == "DELETE":
            if record_id is None:
                abort(401)

            record = ds_holder.delete_record(record_id)

            if record is not None:
                return record.json_describe()
            abort(500)

    @app.route('/api/v1/anchor/<int:dsid>', methods=['GET', 'POST'])
    def anchor(dsid):
        if dsid is None:
            abort(404)
        ds = ds_holder.get(dsid)
        if ds is None:
            abort(404)

        if request.method == "GET":
            anchors = anchoring.confirm("0x{}".format(ds.get_merkle_root()))
            if anchors is None:
                return "Anchorings not yet confirmed"
            else:
                return json.dumps(chainpoint_util.build_v2_receipt(ds.get_merkle_tree(), anchors))

        elif request.method == "POST":
            if anchoring.anchor("0x{}".format(ds.get_merkle_root())):
                return "Ok"
            else:
                return "Error"
