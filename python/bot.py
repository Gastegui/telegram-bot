#!/usr/bin/env python3

from pathlib import Path
import asyncio
import subprocess
import mariadb
import docker
import psutil
import shutil
import time
import re

from telegram import Update, ReactionTypeEmoji, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    CallbackContext
)

TOKEN = Path("/home/pi/bot/token").read_text().strip()
CHAT_ID = int(Path("/home/pi/bot/group_id").read_text().strip())

DB_USER = Path("/home/pi/docker/mariadb/user").read_text().strip()
DB_PASS = Path("/home/pi/docker/mariadb/pass").read_text().strip()

DB_NAME = "pihole"
DB_HOST = "127.0.0.1"

docker = docker.from_env()

logs_cpu: bool = True
logs_temps: bool = True

def clean_domain(text: str):
    if "]: " in text:
        return text.split("]: ", 1)[1]
    return text


async def piholedb(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != CHAT_ID:
        return

    conn = mariadb.connect(
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        database=DB_NAME
    )

    cur = conn.cursor()

    cur.execute(
        "SELECT dominio, accesos FROM DAA WHERE accesos>10 ORDER BY accesos ASC"
    )

    rows = cur.fetchall()

    text = ""
    for domain, hits in rows:
        domain = domain.replace("gravity blocked ", "").replace(" is 0.0.0.0", "")
        text += f"{domain} {hits}\n"

    text = '\n'.join(text.split('\n')[-100:])

    await update.message.reply_text(text if text else "No results")

    cur.close()
    conn.close()


async def meter_en_daa(
    token: str,
    callback_query_id: str,
    message_id: int,
    dominio: str,
    context: ContextTypes.DEFAULT_TYPE):

    bot = context.bot
    error = ""

    await bot.answer_callback_query(callback_query_id=callback_query_id)

    await bot.edit_message_reply_markup(
        chat_id=CHAT_ID,
        message_id=message_id,
        reply_markup=None
    )

    success = False
    conn = None
    cursor = None
    
    try:
        conn = mariadb.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        query = "INSERT INTO DAA(dominio) VALUES(%s);"
        cursor.execute(query, (dominio,))
        conn.commit()

        success = True
    except Exception as e:
        error = e
        print(e)
        success = False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if success:
        await bot.set_message_reaction(
            chat_id=CHAT_ID,
            message_id=message_id,
            reaction=[ReactionTypeEmoji("👍")]
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="Alertar este dominio otra vez",
                callback_data="AA"
            )]
        ])

        await bot.edit_message_reply_markup(
            chat_id=CHAT_ID,
            message_id=message_id,
            reply_markup=keyboard
        )

    else:
        await bot.set_message_reaction(
            chat_id=CHAT_ID,
            message_id=message_id,
            reaction=[ReactionTypeEmoji("😢")]
        )

        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"No se ha podido guardar en la BBDD la entrada: '{dominio}'\n{error}"
        )

async def sacar_de_daa(
    token: str,
    callback_query_id: str,
    message_id: int,
    dominio: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    bot = context.bot
    error = ""

    await bot.answer_callback_query(callback_query_id=callback_query_id)

    await bot.edit_message_reply_markup(
        chat_id=CHAT_ID,
        message_id=message_id,
        reply_markup=None
    )

    success = False
    conn = None
    cursor = None
    
    try:
        conn = mariadb.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        query = "DELETE FROM DAA WHERE dominio=%s;"
        cursor.execute(query, (dominio,))
        conn.commit()

        success = True
    except Exception as e:
        error = e
        success = False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if success:
        await bot.set_message_reaction(
            chat_id=CHAT_ID,
            message_id=message_id,
            reaction=[ReactionTypeEmoji("👌")]
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="No alertar de nuevo este dominio",
                callback_data="DAA"
            )]
        ])

        await bot.edit_message_reply_markup(
            chat_id=CHAT_ID,
            message_id=message_id,
            reply_markup=keyboard
        )

    else:
        await bot.set_message_reaction(
            chat_id=CHAT_ID,
            message_id=message_id,
            reaction=[ReactionTypeEmoji("👍")]
        )

        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"No se ha podido borrar de la BBDD la entrada: '{dominio}'\n{error}"
        )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.message.chat.id != CHAT_ID:
        return

    await query.answer()


    data = query.data
    message_id = query.message.message_id
    message_text = query.message.text

    domain = clean_domain(message_text)

    if data == "DAA":
        await meter_en_daa(TOKEN, query.id, str(message_id), domain, context)
    elif data == "AA":
        await sacar_de_daa(TOKEN, query.id, str(message_id), domain, context)
    elif "docker_start_" in data:
        try:
            container = docker.containers.get(data.split('_')[-1])
            container.start()
            await query.message.reply_text(f"Contenedor {data.split('_')[-1]} arrancado")
        except Exception as e:
            await query.message.reply_text(f"No se ha podido arrancar el contenedor {data.split('_')[-1]}: {e}")
    elif "docker_stop_" in data:
        try:
            container = docker.containers.get(data.split('_')[-1])
            container.stop()
            await query.message.reply_text(f"Contenedor {data.split('_')[-1]} parado")
        except Exception as e:
            await query.message.reply_text(f"No se ha podido parar el contenedor {data.split('_')[-1]}: {e}")
    elif "docker_logs_" in data:
        try:
            container = docker.containers.get(data.split('_')[-1])
            logs = container.logs(tail=10).decode()
            await query.message.reply_text(logs)
        except Exception as e:
            await query.message.reply_text(f"No se han podido sacar los logs del contenedor {data.split('_')[-1]}: {e}")

async def docker_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != CHAT_ID:
        return

    text = ""

    containers = docker.containers.list(all=True)
    for c in containers:
        text += f"{c.name} | {c.status}\n"

    await update.message.reply_text(text if text else "No results")

async def docker_action(action: str, context: ContextTypes.DEFAULT_TYPE):
    text = f"docker {action} ..."
    callback = f"docker_{action}_"

    containers = docker.containers.list(all=True)
    buttons = []
    for i in range((int)(len(containers) / 2)):
        buttons.append([InlineKeyboardButton(containers[i*2].name, callback_data=f"{callback}{containers[i*2].name}"),
                        InlineKeyboardButton(containers[i*2+1].name, callback_data=f"{callback}{containers[i*2+1].name}")])

    if len(containers) % 2 != 0:
        buttons.append([InlineKeyboardButton(containers[-1].name, callback_data=f"{callback}{containers[-1].name}")])

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def docker_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != CHAT_ID:
        return

    await docker_action("start", context)

async def docker_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != CHAT_ID:
        return

    await docker_action("stop", context)

async def docker_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != CHAT_ID:
        return

    await docker_action("logs", context)

async def send_temps(context: CallbackContext):
    output = subprocess.run(["sensors"], capture_output=True, text=True).stdout
    temp = [float(t) for t in re.findall(r'temp1.*?\+([\d.]+)°C', output, re.IGNORECASE)][0]
    if temp >= 70 and logs_temps:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"Temperatura alta: {temp}"
        )

async def send_cpu(context: CallbackContext):
    cpu = psutil.cpu_percent()
    if cpu >= 70 and logs_cpu:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"CPU alta: {cpu}"
        )

async def toggle_cpu(update: Update, context: CallbackContext):
    if update.effective_chat.id != CHAT_ID:
        return
        
    global logs_cpu
    logs_cpu = not logs_cpu
    if logs_cpu:
        await update.message.reply_text("Mensajes de uso de CPU activados")
    else:
        await update.message.reply_text("Mensajes de uso de CPU desactivados")


async def toggle_temps(update: Update, context: CallbackContext):
    if update.effective_chat.id != CHAT_ID:
        return
        
    global logs_temps
    logs_temps = not logs_temps
    if logs_temps:
        await update.message.reply_text("Mensajes de uso de temperatura activados")
    else:
        await update.message.reply_text("Mensajes de uso de temperatura desactivados")


async def status(update: Update, context: CallbackContext):
    if update.effective_chat.id != CHAT_ID:
        return

    cpu = psutil.cpu_percent(interval=1)
    
    ram_total = psutil.virtual_memory().total / 1024**3
    ram_available = psutil.virtual_memory().available / 1024**3
    
    disk_root_total = shutil.disk_usage("/").total / 1024**3
    disk_root_used = shutil.disk_usage("/").used / 1024**3
    disk_data_total = shutil.disk_usage("/mnt/data").total / 1024**3
    disk_data_used = shutil.disk_usage("/mnt/data").used / 1024**3
    
    uptime_seconds = int(time.time() - psutil.boot_time())

    days, rem = divmod(uptime_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    uptime_str = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

    top_procs_cpu = sorted(
        [(p.info['name'], p.info['pid'], p.cpu_percent(interval=0)) 
            for p in psutil.process_iter(attrs=['pid', 'name'])],
        key=lambda x: x[2],
        reverse=True
        )

    top_procs_ram = sorted(
        [(p.info['name'], p.info['pid'], p.info['memory_info']) 
            for p in psutil.process_iter(attrs=['pid', 'name', 'memory_info'])],
        key=lambda x: x[2],
        reverse=True
        )

    text = f"""
Sistema:
CPU: {cpu}% / 400%
RAM: {ram_available:.2f}GB / {ram_total:.2f}GB
Uso /: {disk_root_used:.2f}GB / {disk_root_total:.2f}GB
Uso /mnt/data: {disk_data_used:.2f}GB / {disk_data_total:.2f}GB
Uptime: {uptime_str}

Top 5 procs (CPU):
"""

    for name, pid, cpu in top_procs_cpu[:5]:
        text += f"{name} ({pid}): {cpu}%\n"

    text += "\nTop 5 procs (RAM):\n"

    for name, pid, ram in top_procs_ram[:5]:
        text += f"{name} ({pid}): {ram.rss / 1024**2:.2f}MB\n"

    await update.message.reply_text(text)


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("piholedb", piholedb))
    app.add_handler(CommandHandler("docker_ps", docker_ps))
    app.add_handler(CommandHandler("docker_start", docker_start))
    app.add_handler(CommandHandler("docker_stop", docker_stop))
    app.add_handler(CommandHandler("docker_logs", docker_logs))
    app.add_handler(CommandHandler("logs_cpu", toggle_cpu))
    app.add_handler(CommandHandler("logs_temps", toggle_temps))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(callback))

    app.job_queue.run_repeating(
        send_temps,
        interval=5,
        first=0
    )

    app.job_queue.run_repeating(
        send_cpu,
        interval=5,
        first=0
    )

    app.run_polling()


if __name__ == "__main__":
    main()

# mariadb -h "127.0.0.1" -p$(cat ~/docker/mariadb/pass) -u $(cat ~/docker/mariadb/user) -e "INSERT INTO DAA VALUES (1, 'gravity blocked api2.amplitude.com is 0.0.0.0', '2025-08-09 15:21:03', NOW(), 35746)" "pihole"
# mariadb -h "127.0.0.1" -p$(cat ~/docker/mariadb/pass) -u $(cat ~/docker/mariadb/user) -e "INSERT INTO DAA VALUES (2, 'gravity blocked ads.mozilla.com is 0.0.0.0', '2025-08-09 15:21:03', NOW(), 20720)" "pihole"