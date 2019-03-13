import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

import openSocket from 'socket.io-client';
const socket = openSocket('http://localhost:3001');

class Form extends Component {
  state = {
    query : "",
    site : ""
  }
  submit = (e) => {
    socket.emit('data', {site: this.state.site, text: this.state.query});
    e.preventDefault();
  }
  searchChanged = (e) => {
    this.setState({query: e.target.value});
  }
  siteChanged = (e) => {
    this.setState({site: e.target.value});
  }
  render() {
    return(
      <div className="columns is-centered">
        <div className="form column centered-form">
          <form className="" onSubmit={this.submit}>
            <div className="field">
              <label className="label">Search Query:</label>
              <div className="control is-expanded">
                <input className="input" type="text" value={this.state.query} onChange={this.searchChanged} />
              </div>
            </div>
            <div className="field">
              <label className="label">Floorplan Link:</label>
              <div className="control is-expanded">
                <input className="input" type="text" value={this.state.site} onChange={this.siteChanged} />
              </div>
              <p className="help">Should be in the form of https://something.mapyourshow.com/7_0/search.cfm</p>
            </div>
            <input className="button" type="submit" />
        </form>
          </div>
      </div>
    );
  }
}

class Output extends Component {
  constructor(props) {
    super(props)
    this.output = React.createRef();
  }
  render () {
    this.text = ""
    for (var msg of this.props.text) {
      if (msg != "") {
        this.text += msg + "\n"
      }
    }
    return(
      <div className="Output">
        <textarea className="output" ref={this.output} value={this.text} readonly/>
      </div>
    );
  }
  componentDidUpdate() {
    if (this.output) {
      this.output.current.scrollTop = this.output.current.scrollHeight;
    }
  }
}

class Dashboard extends Component {
  state = {
    currentTab : 1
  }
  sel = (tab) => {this.setState({currentTab: tab})}
  mklink = (tab) => <a onClick={() => this.sel(tab)}>{tab}</a>
  makeHalls = () => {
    var components = []
    for (var i = 1; i <= this.props.halls; i++) {
      var classn = (i === this.state.currentTab) ? "is-active" : ""
      components.push(<li className={classn}>{this.mklink(i)}</li>)
    }
    return (
      <div className="tabs">
      <ul>
        {components}
      </ul>
      </div>
    )
  }
  mkimg = () => {
    if (this.props.images[this.state.currentTab - 1] !== undefined) {
      return <img src={"data:image/png;base64," + this.props.images[this.state.currentTab - 1]} />
    }
  }
  render() {
    return(
      <div className="section">
        <div className="images">
          Halls:
          {this.makeHalls()}
          {this.mkimg()}
        </div>
        <Output text={this.props.messages} />
      </div>
    );
  }
}

class App extends Component {
  state = {
    websocket: false,
    hasSubmitted: false,
    messages: [],
    images: [],
    halls: 1,
  }
  constructor(props) {
    super(props);
    socket.on('connected', this.on_connected);
    socket.on('received', this.on_query_received);
    socket.on('output', this.on_output_sent);
    socket.on('image', this.on_image);
  }
  on_connected = () => {
    this.setState({websocket: true});
  }
  on_query_received = () => {
    this.setState({hasSubmitted: true});
  }
  on_output_sent = (data) => {
    var hall_code = '@!';
    var lines = data.split("\n");
    for (var line of lines) {
      console.log(line);
      if (line.slice(0, 2) === hall_code) {
        this.setState({halls: parseInt(line.slice(2))});
      }
      else {
        this.setState({messages: [...this.state.messages, line]});
      }
    }
  }
  on_image = (buf) => {
    this.setState({images: [...this.state.images, buf]});
  }
  draw = () => {
    if (!this.state.websocket) {
      return <p>No web socket connected.</p>;
    }
    if (this.state.hasSubmitted) {
      return <Dashboard 
        messages={this.state.messages} 
        halls={this.state.halls}
        images={this.state.images}
      />;
    } else {
      return <Form />
    }
  }
  render() {
    return (
      <div className="App section">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.4/css/bulma.min.css" type="text/css" />
        <div className="content title-heading">
          <h2>Annotated map generator for events ran through MapYourShow</h2>
        </div>
        {this.draw()}    
      </div>
    );
  }
}

  export default App;
