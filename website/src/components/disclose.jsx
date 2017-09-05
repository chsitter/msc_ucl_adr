import React, {Component} from "react";

export default class Disclose extends Component {
    constructor(props) {
        super(props);

        this.state = {
            datastoreId: props.datastoreId,
            title: '',
            file: null,
            privkey: JSON.stringify({
                kty: "EC",
                crv: "P-256",
                d: "Ffa8MYI2t0orcRh-EhlY9izq0rUtdMFfnJO-q9GSleU",
                x: "JOWAdwUcjO1XkVs4ODoGERQTnd_9tBJJ2BZMLICI0FM",
                y: "B7TQnpt-JoWVNSY5IB5SIlpZOwmadzm15ng8ADE4H58",
                ext: true
            }),
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleFileChange = this.handleFileChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        const name = event.target.name;

        this.setState({
            [name]: event.target.value
        });
    }

    handleFileChange(event) {
        let file = event.target.files[0];
        this.setState({
            file: file
        });
    }

    handleSubmit(event) {
        event.preventDefault();
        let reader = new FileReader();
        let file = this.state.file;
        let dsId = this.props.store.id;
        let title = this.state.title;
        let discloseCb = this.props.discloseCb;
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
            reader.onloadend = function (evt) {
                let fileContent = evt.target.result;
                let data = btoa(String.fromCharCode.apply(null, new Uint8Array(fileContent)));
                let signData = new TextEncoder('utf-8').encode(title + data + pubkey);
                window.crypto.subtle.sign({
                    name: "ECDSA",
                    hash: {name: "SHA-256"},
                }, key, signData).then(function (signature) {
                    discloseCb(dsId, title, data, btoa(String.fromCharCode.apply(null, new Uint8Array(signature))), pubkey)
                }).catch(function (err) {
                    alert(err);
                });
            };
            reader.readAsArrayBuffer(file);
        }).catch(function (err) {
            alert(err);
        });
    }

    render() {
        return (
            <div id={"datastore" + this.props.store.id}>
                <h3>Disclose Documents below</h3>
                <form onSubmit={this.handleSubmit} method="POST" encType="multipart/form-data">
                    <table>
                        <tbody>
                        <tr>
                            <td>Title:</td>
                            <td><input type="text" name="title" value={this.state.title}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>File:</td>
                            <td><input type="file" name="file" onChange={this.handleFileChange} autoComplete="off"/>
                            </td>
                        </tr>
                        <tr>
                            <td>Private key:</td>
                            <td><input type="text" name="privkey" value={this.state.privkey}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td><input type="submit" value="Disclose"/></td>
                        </tr>
                        </tbody>
                    </table>
                </form>
            </div>

        );
    }
}