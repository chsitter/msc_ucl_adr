import React, {Component} from "react";
import {Redirect} from 'react-router-dom'
import Disclose from "./disclose";
import Ack from "./ack";
import RecordList from "./recordlist";


export default class Disclosure extends Component {
    constructor(props) {
        super(props);

        this.state = {
            datastoreDisclosure: null,
            datastoreAck: null,
            recordsDisclose: {},
            recordsAck: {}
        };

        this.user = null;
        if (this.props.getUser() !== null) {
            this.user = this.props.getUser().email;
            this.apiKey = this.props.getUser().api_key;
            this.getOrCreateDatastores();
        }

        this.loadRecords = this.loadRecords.bind(this);
        this.discloseDocument = this.discloseDocument.bind(this);
        this.ackDocument = this.ackDocument.bind(this);
        this.buildAdrReceipt = this.buildAdrReceipt.bind(this);
    }

    createDatastore(_this, name) {
        let xhttp = new XMLHttpRequest();

        let json_data = {
            name: name,
            groupName: ""
        };

        xhttp.open("POST", "http://localhost:5000/api/v1/datastores", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.setRequestHeader("X-Username", this.user);
        xhttp.setRequestHeader("X-Api-Key", this.apiKey);
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let store = JSON.parse(this.responseText);
                    if (store.name === 'disclose') {
                        _this.setState({
                            datastoreDisclosure: store,
                        });
                    } else {
                        _this.setState({
                            datastoreAck: store,
                        });
                    }
                } else {
                    alert(this.response)
                }
            }
        };

        xhttp.send(JSON.stringify(json_data));
    }

    getOrCreateDatastores() {
        let xhttp = new XMLHttpRequest();
        let _this = this;

        xhttp.open("GET", "http://localhost:5000/api/v1/datastores", true);
        xhttp.setRequestHeader("X-Username", this.user);
        xhttp.setRequestHeader("X-Api-Key", this.apiKey);
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let stores = JSON.parse(this.responseText);
                    if (stores.length === 0) {
                        _this.createDatastore(_this, "disclose");
                        _this.createDatastore(_this, "ack");
                    } else {
                        let discStore = stores.find((e) => {
                            return e.name === 'disclose'
                        });
                        let ackStore = stores.find((e) => {
                            return e.name === 'ack'
                        });
                        _this.setState({
                            datastoreDisclosure: discStore,
                            datastoreAck: ackStore
                        });

                        _this.loadRecords("disclose", discStore.id);
                        _this.loadRecords("ack", ackStore.id)
                    }
                } else {
                    alert(this.response)
                }
            }
        };

        xhttp.send();
    }

    loadRecords(storeType, storeId) {
        let xhttp = new XMLHttpRequest();
        let _this = this;
        xhttp.open("GET", "http://localhost:5000/api/v1/records?datastoreId=" + storeId, true);
        xhttp.setRequestHeader("X-Username", this.user);
        xhttp.setRequestHeader("X-Api-Key", this.apiKey);
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let records = JSON.parse(this.responseText);
                    let recDict = {};

                    records.records.forEach(function (record) {
                        recDict[record.id] = record;
                    });

                    if (storeType === "disclose") {
                        _this.setState({
                            recordsDisclose: recDict
                        })
                    } else {
                        _this.setState({
                            recordsAck: recDict
                        })
                    }
                } else {
                    console.log(this.status)
                }
            }
        };

        xhttp.send();
    }

    discloseDocument(datastoreId, title, data, signature, pubkey) {
        console.log("Adding disclosed document: " + title);
        let record = {
            datastoreId: datastoreId,
            title: title,
            data: data,
            signature: signature,
            pubkey: pubkey
        };

        let xhttp = new XMLHttpRequest();
        let _this = this;
        xhttp.open("POST", "http://localhost:5000/api/v1/records", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.setRequestHeader("X-Username", this.user);
        xhttp.setRequestHeader("X-Api-Key", this.apiKey);
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let record = JSON.parse(this.responseText);
                    let newRecords = JSON.parse(JSON.stringify(_this.state.recordsDisclose));
                    newRecords[record.id] = record;
                    _this.setState({
                        recordsDisclose: newRecords
                    });
                } else {
                    alert(this.response)
                }
            }
        };

        xhttp.send(JSON.stringify(record));
    }

    ackDocument(datastoreId, recordId, signature, pubkey) {
        console.log("Acknowledging doc receipt: " + recordId);
        let record = {
            datastoreId: datastoreId,
            recordId: recordId,
            signature: signature,
            pubkey: pubkey
        };


        let xhttp = new XMLHttpRequest();
        let _this = this;
        xhttp.open("POST", "http://localhost:5000/api/v1/records", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.setRequestHeader("X-Username", this.user);
        xhttp.setRequestHeader("X-Api-Key", this.apiKey);
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let record = JSON.parse(this.responseText);
                    let newRecords = JSON.parse(JSON.stringify(_this.state.recordsAck));
                    newRecords[record.id] = record;
                    _this.setState({
                        recordsAck: newRecords
                    });
                } else {
                    alert(this.response)
                }
            }
        };

        xhttp.send(JSON.stringify(record));
    }

    buildAdrReceipt(record) {
        if ("recordId" in record.data) {
            let tmp = JSON.parse(JSON.stringify(record.data));
            tmp["document"] = this.state.recordsDisclose[tmp.recordId].data;
            delete tmp["recordId"];
            alert(JSON.stringify([record.blockchain_receipt, tmp]))
        } else {
            alert(JSON.stringify([record.blockchain_receipt, record.data]))
        }
    }


    render() {
        if (this.user === null) {
            return (<Redirect to="/"/>);
        }

        if (this.state.datastoreDisclosure === null || this.state.datastoreAck === null) {
            return (<div></div>)
        }

        let disclosedRecords = JSON.parse(JSON.stringify(this.state.recordsDisclose));
        let acknowledgedRecords = JSON.parse(JSON.stringify(this.state.recordsAck));
        let acknowledgedRecordIds = [];
        let disclosedRecordIds = [];
        for (let key in acknowledgedRecords) {
            if (acknowledgedRecords.hasOwnProperty(key)) {
                let record = acknowledgedRecords[key];
                acknowledgedRecordIds.push(record.data.recordId);
            }
        }
        for (let key in disclosedRecords) {
            if (disclosedRecords.hasOwnProperty(key)) {
                let record = disclosedRecords[key];
                disclosedRecordIds.push(record.id);
            }
        }

        console.log("Rendering disclosure");
        console.log("Disclosed: " + disclosedRecordIds);
        console.log("Acked: " + acknowledgedRecordIds);
        return (
            <table className="disclosureTable">
                <tbody>
                <tr>
                    <td>
                        <Disclose key={"ds" + this.state.datastoreDisclosure.id}
                                  store={this.state.datastoreDisclosure}
                                  discloseCb={this.discloseDocument}/>
                    </td>
                    <td>
                        <Ack key={"ds" + this.state.datastoreAck.id} store={this.state.datastoreAck}
                             ackCb={this.ackDocument}/>
                    </td>
                </tr>
                <tr>
                    <td>
                        <RecordList records={disclosedRecords} buildAdrReceipt={this.buildAdrReceipt}
                                    ackedRecords={acknowledgedRecordIds}/>
                    </td>
                    <td>
                        <RecordList records={acknowledgedRecords} buildAdrReceipt={this.buildAdrReceipt}/>
                    </td>
                </tr>
                </tbody>
            </table>
        );
    }
}