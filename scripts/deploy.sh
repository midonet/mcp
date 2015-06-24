#!/usr/bin/env bash

SLAVE_LIST=./slaves
USER=ubuntu
MCP_TMP_DIR=/tmp
TIMEOUT=180
CONTAINERIZER_HOME=/usr/local/bin/mcp
CONTAINERIZER=mcpw

PSSH=`((which parallel-ssh > /dev/null) && which parallel-ssh) || \
 ((which pssh > /dev/null) && which pssh)`

if [ ! -f ./slaves ]; then
    echo "Slave hosts or addresses should be put in a file, slaves"
    exit 1
fi

if [ ! -d .deploy ]; then
    mkdir .deploy;
fi
tar cfz .deploy/mcp.tar.gz *

while read slave; do
    scp .deploy/mcp.tar.gz $USER@$slave:$MCP_TMP_DIR
done < $SLAVE_LIST

$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	sudo mkdir -p $CONTAINERIZER_HOME
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	sudo tar xfz $MCP_TMP_DIR/mcp.tar.gz -C $CONTAINERIZER_HOME
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	"if [ \`pip list | grep 'protobuf (2.6.1)' | wc -l\` -ne '1' ]; then \
         sudo $CONTAINERIZER_HOME/setup.sh; \
     fi"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
    "sudo chmod +x ${CONTAINERIZER_HOME}/${CONTAINERIZER}"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	"sudo sh -c 'echo ${CONTAINERIZER_HOME}/${CONTAINERIZER} > \
        /etc/mesos-slave/containerizer_path'"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	"sudo sh -c 'echo external > /etc/mesos-slave/isolation'"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	"sudo chmod 755 ${CONTAINERIZER_HOME}/${CONTAINERIZER}"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	"sudo rm -rf /tmp/mesos-test-containerizer/*"
$PSSH -h $SLAVE_LIST -l$USER -t $TIMEOUT -i \
	sudo service mesos-slave restart
