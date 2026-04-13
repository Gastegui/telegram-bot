#!/bin/bash

set -e

tail -f  /home/pi/docker/pihole/var-log/pihole/pihole.log | grep --line-buffered "0\.0\.0\.0" | /home/pi/bot/pihole_alert.sh &
/home/pi/bot/python/.venv/bin/python /home/pi/bot/python/bot.py &
/home/pi/bot/docker-ps/loop.sh
