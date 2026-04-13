#!/bin/bash

last=""

while true; do

    status=$(docker ps -a --format '{{.Names}}: {{.State}}')
    if [[ "${status}" != "${last}" ]]; then
        /home/pi/bot/docker-ps/mandar.sh
        last="${status}"
    fi
    sleep 5
done
