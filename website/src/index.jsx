import React from 'react'
import { render } from 'react-dom'
import { BrowserRouter } from 'react-router-dom'
import App from './components/app';

require('./stylesheets/base.scss');
require('./stylesheets/modal.scss');
require('./stylesheets/recordlist.scss');
require('./stylesheets/disclosure.scss');

render((
    <BrowserRouter>
        <App />
    </BrowserRouter>
), document.querySelector('#app'));
