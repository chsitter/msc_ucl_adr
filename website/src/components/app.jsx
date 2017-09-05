import React, { Component } from "react";
import Header from "./header"
import Main from "./main"

export default class App extends Component {
    constructor(props) {
        super(props);

        this.state = {
            user: null
        };

        this.setUser = this.setUser.bind(this);
        this.getUser = this.getUser.bind(this);
    }

    setUser(user) {
        console.log("set user to: " + JSON.stringify(user));
        this.setState({
            user: user
        });
    }

    getUser() {
        return this.state.user;
    }

    render() {
        return (
            <div>
                <Header/>
                <Main setUser={this.setUser} getUser={this.getUser}/>
            </div>
        );
    }
}