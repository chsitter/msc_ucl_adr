import React, { Component } from "react";
import { Link } from 'react-router-dom'


export default class Home extends Component {
    render() {
        return (
            <ul>
                <li><Link to='/register'>Start disclosure for new dispute</Link></li>
                <li><Link to='/login'>Log-in and resume old ongoing discovery</Link></li>
            </ul>
        );
    }
}