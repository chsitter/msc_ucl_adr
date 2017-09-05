import React, {Component} from "react";
import {Redirect} from 'react-router-dom'

import Modal from "./modal"

export default class Login extends Component {
    constructor(props) {
        super(props);
        this.state = {
            data: {
                name: '',
                secret: ''
            },
            control: {
                showModal: false,
                modalText: "Modal text"
            }
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        const name = event.target.name;

        let data = this.state.data;
        data[name] = event.target.value;
        this.setState({data});
    }

    handleSubmit(event) {
        let xhttp = new XMLHttpRequest();
        let json_data = JSON.stringify(this.state.data);
        let _this = this;
        this.setState({
            control: {
                showModal: true,
                modalText: "One moment please",
                submitted: false
            }
        });

        xhttp.open("POST", "http://localhost:5000/api/v1/login", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    _this.props.setUser(JSON.parse(this.responseText));
                    _this.setState({
                        control: {
                            submitted: true,
                            showModal: false
                        }
                    });
                } else {
                    _this.setState({
                        control: {
                            showModal: true,
                            modalText: <div>
                                <span>Something went wrong, please refresh and try again</span>
                                <p>{this.statusText}</p>
                            </div>
                        }
                    })
                }
            }
        };

        xhttp.send(json_data);
        event.preventDefault();
    }

    render() {
        if (this.state.control.submitted) {
            return (<Redirect to="/disclosure" />);
        }

        let modal = null;
        if (this.state.control.showModal) {
            modal = <Modal text={this.state.control.modalText}/>;
        }

        return (
            <div>
                <form onSubmit={this.handleSubmit}>
                    <table>
                        <tbody>
                        <tr>
                            <td>Username:</td>
                            <td><input type="text" name="name" value={this.state.data.name}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>Password:</td>
                            <td><input type="password" name="secret" value={this.state.data.secret}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td><input type="submit" value="Login"/></td>
                        </tr>
                        </tbody>
                    </table>
                </form>
                {modal}
            </div>
        );
    }
}