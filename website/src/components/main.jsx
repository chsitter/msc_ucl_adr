import React, {Component} from "react";
import {Switch, Route} from 'react-router-dom'

import Home from './home'
import Login from './login'
import Disclose from './disclosure'
import Register from './register'

export default class Main extends Component {
    render() {
        let _this = this;
        return (
            <Switch>
                <Route exact path="/" component={Home}/>
                <Route exact path="/register" render={() => <Register setUser={this.props.setUser}/>}/>
                <Route exact path="/login" render={() => <Login setUser={_this.props.setUser}/>}/>
                <Route exact path="/disclosure" render={() => <Disclose getUser={_this.props.getUser}/>}/>
            </Switch>
        );
    }
}