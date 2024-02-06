from logging import basicConfig, log, INFO, WARN, ERROR, CRITICAL
from pathlib import Path
from random import randbytes
from requests import get
from urllib.parse import quote, unquote
from ctypes import c_ulong, pythonapi, py_object
from typing import Any, Awaitable, Callable
from motor.motor_tornado import MotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tzlocal import get_localzone
from database.db import DataBase
import asyncio

basicConfig(format="[%(levelname)s]: %(message)s", level=INFO, force=True)
log(INFO, "Initializing...")

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.enums.parse_mode import ParseMode
from os import system, unlink
from time import sleep, time
from datetime import datetime
import bot_cfg

bot: Client = Client("bot",api_id=bot_cfg.tg_api_id,api_hash=bot_cfg.tg_api_hash,bot_token=bot_cfg.tg_bot_token)

bot_database = MotorClient(bot_cfg.database_url,serverSelectionTimeoutMS=999999)

str_localzone = str(get_localzone())
scheduler = AsyncIOScheduler(timezone=str_localzone,event_loop=bot.loop,misfire_grace_time=600)

def async_e(func: Callable) -> Awaitable:
  async def run_cancellable(*args, **kwargs) -> Any:
    def worker() -> Any:
      context["thread"] = current_thread().ident
      return func(*args, **kwargs)
    
    context: dict = {"thread": None}
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    future: asyncio.Future = asyncio.ensure_future(loop.run_in_executor(None, worker))
    while not future.done():
      try:
        await asyncio.wait([future])
      except asyncio.CancelledError:
        thread_id: c_ulong = c_ulong(context["thread"])
        exception: py_object = py_object(asyncio.CancelledError)
        ret: int = pythonapi.PyThreadState_SetAsyncExc(thread_id, exception)
        if ret > 1:  # This should NEVER happen, but shit happens
          pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
    return future.result()
  
  return run_cancellable

@bot.on_message(filters.command("start") & filters.private)
async def welcome(client: Client, message: Message):
  user_id = message.from_user.id
  first_name = message.from_user.first_name
  username = message.from_user.username
  data = DataBase(bot_database)
  await data.new_user(user_id,first_name,username)
  await data.set_new_key("join_date",datetime.now(),user_id)
  await message.reply("🤖 Bienvenido al bot de administración de suscripciones del canal **🥇 SEASON PREMIUM 🥇**")

@bot.on_message(filters.chat(-1002061583172))
async def chat_group(client: Client, message: Message):
  if message.from_user:
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    data = DataBase(bot_database)
    await data.new_user(user_id,first_name,username)
    user = await data.get_user(user_id)
    if username != user.get("username"):
      await data.set_new_key("username",username,user_id)

@bot.on_chat_member_updated(filters.chat(-1002099762277))
async def register(client: Client, message: Message):
  if message.new_chat_member:
    if message.new_chat_member.user:
      user_id = message.new_chat_member.user.id
      username = message.new_chat_member.user.username
      first_name = message.new_chat_member.user.first_name
      data = DataBase(bot_database)
      await data.new_user(user_id,first_name,username)
      await data.set_new_key("join_date",datetime.now(),user_id)
  if message.old_chat_member:
    if message.old_chat_member.user:
      user_id = message.old_chat_member.user.id
      data = DataBase(bot_database)
      await data.set_new_key("join_date",None,user_id)

async def verify_not_expire_user():
  data = DataBase(bot_database)
  users = await data.verify()
  print(users)
  for user_id in users:
    user = await data.get_user(user_id)
    first_name = user["firstname"]
    user_name = user["username"]
    if user_name == None:
      user_profile = f"<a href='tg://user?id={user_id}'><b>{first_name}</b></a>"
    else:
      user_profile = f"**@{user_name}**"
    await bot.send_message(-1002061583172,f"🤖 Admin **@CiberV** ya han pasado 30 días desde que el usuario {user_profile} se unió al canal!")
    await bot.send_message(-1002061583172,f"⛔️ Usuario {user_profile} ya ha completado su mes en nuestro canal 🤖, tendrá que contratar una nueva suscripción mensual en nuestro bot **@SeasonPremium_bot** si desea continuar en el canal.")
  
@async_e
def heartbeat():
  log(INFO, "Starting heartbeat each 10 minutes")
  while True:
    try:
      log(INFO, "Heartbeat")
      get(f"https://{bot_cfg.render_url}/HEARTBEAT/")
    except:
      pass
    sleep(10 * 60)


log(INFO, "Starting...")
bot.loop.create_task(heartbeat())
scheduler.add_job(verify_not_expire_user,"interval",seconds=300)
scheduler.start()
bot.run()