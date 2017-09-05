import React, {Component} from "react";


export default class Ack extends Component {
    constructor(props) {
        super(props);
        this.state = {
            datastoreId: props.datastoreId,
            recordId: '',
            privkey: JSON.stringify({
                kty: "EC",
                crv: "P-256",
                d: "CyLEU5wQdeL1-Th4l3IQZtDAevIMJYJuckYScyBD2mA",
                x: "wA53IuoOYYR_myqMqQTGaoCWqIGJy5XBhgsoWqOGzhg",
                y: "A0DBTVj4MYaKSh6I9bLHH-pk4aU1zC4zpssLSdemOOE",
                ext: true
            }),
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        const name = event.target.name;

        this.setState({
            [name]: event.target.value
        });
    }

    handleSubmit(event) {
        let dsId = this.props.store.id;
        let recordId = this.state.recordId;
        let ackCb = this.props.ackCb;
        let pubkey = JSON.parse(this.state.privkey);
        delete pubkey.d;
        pubkey = JSON.stringify(pubkey);

        window.crypto.subtle.importKey(
            "jwk", JSON.parse(this.state.privkey),
            {
                name: "ECDSA", namedCurve: "P-256",
            },
            true, ["sign"]
        ).then(function (key) {
            let signData = new TextEncoder('utf-8').encode(recordId + pubkey);

            window.crypto.subtle.sign({
                name: "ECDSA",
                hash: {name: "SHA-256"},
            }, key, signData).then(function (signature) {
                ackCb(dsId, recordId, btoa(String.fromCharCode.apply(null, new Uint8Array(signature))), pubkey);
            }).catch(function (err) {
                alert(err);
            });

        }).catch(function (err) {
            alert(err);
        });

        event.preventDefault();
    }

    render() {
        return (
            <div id={"datastore" + this.props.store.id}>
                <h3>Acknowledge documents below</h3>
                <form onSubmit={this.handleSubmit}>
                    <table>
                        <tbody>
                        <tr>
                            <td>Document ID:</td>
                            <td><input type="text" name="recordId" value={this.state.recordId}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>Private key:</td>
                            <td><input type="text" name="privkey" value={this.state.privkey}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td><input type="submit" value="Acknowledge"/></td>
                        </tr>
                        </tbody>
                    </table>
                </form>
            </div>

        );
    }
}