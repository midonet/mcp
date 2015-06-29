#!/usr/bin/env bash

sudo aptitude -y install python-pip unzip
sudo pip install protobuf
curl -o /tmp/python-midonetclient.zip https://codeload.github.com/midonet/python-midonetclient/zip/master
unzip -d /tmp /tmp/python-midonetclient.zip
cd /tmp/python-midonetclient-master
sudo python setup.py install
