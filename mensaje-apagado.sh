#!/bin/bash

TOKEN="$(cat /home/pi/bot/token)"
CHAT_ID="$(cat /home/pi/bot/group_id)"

/bin/curl -s -X POST https://api.telegram.org/bot$TOKEN/sendMessage -d chat_id=$CHAT_ID -d text="APAGANDO" > /dev/null
