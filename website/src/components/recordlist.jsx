import React, {Component} from "react";

export default class RecordList extends Component {
    render() {
        let recordDict = this.props.records;
        let buildReceipt = this.props.buildAdrReceipt;
        let records = [];
        let acked = null;
        if ("ackedRecords" in this.props) {
            acked = this.props.ackedRecords;
        }

        Object.keys(recordDict).map(function (key) {
            let element = recordDict[key];
            let className = "disclosed";
            if (acked !== null && acked.indexOf(key) >= 0) {
                className = "acknowledged";
            }
            records.push(<tr key={"el" + element.id}>
                <td className={className}>{element.id}</td>
                <td>{element.data.title}</td>
                <td>
                    <button onClick={() => buildReceipt(element)}>Receipt</button>
                </td>
            </tr>);
        });

        return (
            <table className="documentList">
                <thead>
                <tr>
                    <th>Document ID</th>
                    <th>Document Title</th>
                    <th>Receipt</th>
                </tr>
                </thead>
                <tbody>
                {records}
                </tbody>
            </table>
        );
    }
}