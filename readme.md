# Telegram bot for RPI

A Telegram bot for a Raspberry Pi that provides real-time monitoring and management of system resources, Docker, and [Pi-hole](https://github.com/pi-hole/pi-hole).

## Features

### Docker container management
- Real-time updates of container status changes
- List all containers and their status
- Remotely start and stop containers

### Pi-Hole monitoring
- Real-time notifications of blocked DNS request
- Using MariaDB:
    - Mark domains not to be alerted again
    - Collect statistics of blocked requests
    - Get statistics of blocked domains

### System management
- System power-on and power-off notifications
- Over-heating notifications (toggleable)
- High CPU usage notifications (toggleable)
- System status command

## Requirements

- Python3.8+
- Docker
- MariaDB
- Pi-Hole
- lm-sensors

### Python dependencies

- python-telegram-bot
- mariadb
- docker
- psutil

## Configuration

1. Create a bot on Telegram with the next commands:
    - `piholedb`: Prints all the domains added the DAA table with more than 10 blocks
    - `docker_ps`: Prints a `docker ps`-like text
    - `docker_start`: Creates a button for each container to start them
    - `docker_stop`: Creates a button for each container to stop them
    - `docker_logs`: Creates a button for each container that prints its last 10 lines of logs
    - `logs_cpu`: Toggles on and off the high CPU usage notifications
    - `logs_temps`: Toggles on and off the high CPU temperature notifications
    - `status`: Prints CPU usage and temperature, RAM usage, Disk usage, uptime, and the top 5 CPU and RAM consuming processes

1. Create the next files

    - `/home/pi/bot/token`: File with the Telegram bot token
    - `/home/pi/bot/group_id`: File with the Telegram group id where the bot will be used
    - `/home/pi/docker/mariadb/user`: File with the username of MariaDB
    - `/home/pi/docker/mariadb/pass`: File with the password of MariaDB

1. All the paths are absolute on the project, so they will probably need to be changed
1. Create the SQL database from the [pihole.sql](./pihole.sql) file
1. For automatic start-up of the bot, and the power-on and power-off messages, add the next systemd services:
    - [Bot startup](./services/bot_start.service)
    - [Power-on notification](./services/notificacion-encendido.service)
    - [Power-off notification](./services/notificacion-apagado.service)
1. Create a `python -m venv` under the python directory and install the python deps