# Installation

Noteefi requires MongoDB and Python3. Regarding installation of MongoDB please see [Here](https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-16-04)

Installaion of Python dependencies
```
sudo apt-get update
sudo apt-get -y install python3 python3-pip
sudo pip3 install requests websocket-client
```

Noteefi communicated with steemd, so make sure you are running steemd on your local server (if you want to connect public ws server, you may want to edit the code `ws = create_connection("ws://127.0.0.1:8090")`).

To obtain the telegram bot token, please see [Here](https://core.telegram.org/bots)
