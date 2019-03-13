//const express = require("express");
const io = require("socket.io")();
const spawn = require("child_process").spawn;
const fs = require('fs')

function connected(client) {
  client.emit('connected');
}

function onQuery(query, client) {
  console.log('received query: ', query);
  client.emit('received');
  client.script_process = spawn('python3', ["./generator.py", query.site, query.text])
  client.script_process.stdout.on('data', (data) => {
    var lines = data.toString('utf8').split("\n");
    var not_image = true;
    for (var line of lines) {
      image_code = "@@";
      if (line.slice(0, 2) === image_code) {
        not_image = false;
        var path = line.slice(2);
        fs.readFile(path, (err, buf) => {
          // https://stackoverflow.com/questions/26331787/socket-io-node-js-simple-example-to-send-image-files-from-server-to-client
          client.emit('image', buf.toString('base64'));
        });
      }
    }
    if (not_image)
      client.emit('output', data.toString('utf8'));
  });
  client.script_process.stderr.on('data', (data) => {
    console.log(data.toString('utf8'));
  });
  client.script_process.on('exit', (code) => {
    console.log(code);
  });
  client.script_process.on('error', (error) => {
    console.log(error);
  });
  client.on('disconnect', (reason) => {
    if (client.script_process !== undefined) {
      client.script_process.kill();
    }
  });
}

io.on('connection', (client) => {
  connected(client); 
  client.on('data', (query) => {
    onQuery(query, client);
  });
});


const port = 3001;
io.listen(port);
