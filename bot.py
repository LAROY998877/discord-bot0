import os
import random
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# قراءة التوكن بأمان من متغيرات البيئة في الاستضافة أو من ملف محلي إن وجد
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    try:
        from config import TOKEN
    except ImportError:
        TOKEN = None
