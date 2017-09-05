import React, {Component} from "react";
import { Redirect } from 'react-router-dom'

import Modal from "./modal"

export default class Register extends Component {
    constructor(props) {
        super(props);
        this.state = {
            data: {
                name: '',
                full_name: '',
                email: '',
                secret: '',
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

        xhttp.open("POST", "http://localhost:5000/api/v1/accounts", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
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
            return (<Redirect to="/login"/>);
        }

        const showModal = this.state.control.showModal;

        let modal = null;
        if (showModal) {
            modal = <Modal text={this.state.control.modalText}/>;
        }

        return (
            <div>
                <form onSubmit={this.handleSubmit}>
                    <table>
                        <tbody>
                        <tr>
                            <td>Name:</td>
                            <td><input type="text" name="name" value={this.state.data.name}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>Email:</td>
                            <td><input type="email" name="email" value={this.state.data.email} onChange={this.handleChange}/>
                            </td>
                        </tr>
                        <tr>
                            <td>Full Name:</td>
                            <td><input type="text" name="full_name" value={this.state.data.full_name}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td>Secret:</td>
                            <td><input type="password" name="secret" value={this.state.data.password}
                                       onChange={this.handleChange}/></td>
                        </tr>
                        <tr>
                            <td><input type="submit" value="Register"/></td>
                        </tr>
                        </tbody>
                    </table>
                </form>
                {modal}
            </div>

        );
    }
}