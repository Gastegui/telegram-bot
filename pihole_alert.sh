#!/bin/bash
TOKEN="$(cat /home/pi/bot/token)"
CHAT_ID="$(cat /home/pi/bot/group_id)"
DB_USER="$(cat /home/pi/docker/mariadb/user)"
DB_PASS="$(cat /home/pi/docker/mariadb/pass)"
DB_NAME="pihole"
DB_HOST="127.0.0.1"

while IFS= read -r line; do
    DOMINIO="$(echo $line | awk -F']: ' '{if (NF>1) print $2; else print $0}')"
    QUERY="CALL select_and_update('$DOMINIO');"
    if ! mariadb -h "$DB_HOST" -p$DB_PASS -u "$DB_USER" "$DB_NAME" -e "$QUERY" > /dev/null 2>&1; then
        curl -s -X POST https://api.telegram.org/bot$TOKEN/sendMessage -d chat_id=$CHAT_ID -d text="$line" -d reply_markup='{"inline_keyboard": [[ {"text": "No alertar de nuevo este dominio", "callback_data": "DAA"} ]] }' > /dev/null
    fi
done
