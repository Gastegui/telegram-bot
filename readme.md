# Bot de Telegram para Raspberry PI

Un bot de Telegram para Raspberry PI que proporciona monitoreo a tiempo real y administracion de Docker, [Pi-hole](https://github.com/pi-hole/pi-hole) y recursos del sistema.

## Características

### Administración de contenedores de Docker
- Notificaciones a tiempo real de cambios de estado de los contenedores
- Lista todos los contenedores y sus estados
- Arranca y detiene cualquier contenedor de forma remota

### Monitoreo de Pi-Hole
- Notificaciones a tiempo real de solicitudes DNS bloqueadas
- Usando MariaDB:
    - Marca dominios para que no se vuelvan a alertar en Telegram
    - Colecciona estadísticas de los dominios bloqueados

### Administración del sistema
- Notificaciones de encendido y apagado del sistema
- Notificaciones de sobrecalentamiento (desactivables)
- Notificaciones de uso de CPU alto (desactivables)
- Visualización de estado del sistema

## Requisitos

- Python3.8+
- Docker
- MariaDB
- Pi-Hole
- lm-sensors

### Dependencias de Python

- python-telegram-bot
- mariadb
- docker
- psutil

## Configuración / Instalación

1. Crea un bot de Telegram con los siguientes comandos:
    | Comando        | Descripción                                                                                        |
    | -------------- | -------------------------------------------------------------------------------------------------- |
    | `piholedb`     | Muestra todos los dominios que se han bloqueado más de 10 veces                                    |
    | `docker_ps`    | Muesta el estado de todos los contenedores de forma parecida a `docker ps`                         |
    | `docker_start` | Crea un botón por cada contenedor para poder arrancarlos                                           |
    | `docker_stop`  | Crea un botón por cada contenedor para poder pararlos                                              |
    | `docker_logs`  | Crea un botón por cada contenedor para poder ver sus últimas 10 líneas de logs                     |
    | `logs_cpu`     | Detiene o reactiva las notificaciones de uso de CPU alto                                           |
    | `logs_temps`   | Detiene o reactiva las notificaciones de temperatura de CPU alta                                   |
    | `status`       | Muesta el uso y temperatura de la CPU, uso de RAM, uptime, y los 5 procesos que usan más CPU y RAM |

1. Crea los siguientes archivos

    - `/home/pi/bot/token`: Archivo con el token del bot de Telegram
    - `/home/pi/bot/group_id`: Archivo con el group_id del grupo en el que está en bot
    - `/home/pi/docker/mariadb/user`: Archivo con el nombre de usuario de MariaDB
    - `/home/pi/docker/mariadb/pass`: Archivo con la contraseña de MariaDB

1. Todos los paths en el proyecto son absolutos, por lo que seguramente haga falta cambiarlos
1. Crea la base de datos usando el archivo [pihole.sql](./pihole.sql)
1. Crea un `python -m venv` en el directorio de python y descarga las dependencias de python
1. Para que el bot arranque de forma automática, las notificaciones de encendido y apagado, añade y activa los siguientes servicios de systemd:
    - [Arranque del bot](./services/bot_start.service)
    - [Notificación de encendido](./services/notificacion-encendido.service)
    - [Notificación de apagado](./services/notificacion-apagado.service)
