import React, {Component} from "react";

export default class Modal extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div className="modal">
                <div className="modal-content">
                    {this.props.text}
                </div>
            </div>
        );
    }
}
