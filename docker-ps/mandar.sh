#!/bin/bash

TOKEN="$(cat /home/pi/bot/token)"
CHAT_ID="$(cat /home/pi/bot/group_id)"

curl -s -X POST https://api.telegram.org/bot$TOKEN/sendMessage -d chat_id=$CHAT_ID -d text="DOCKER UPDATE: %0A$(docker ps -a --format '{{.Names}}: {{.Status}}')" > /dev/null
