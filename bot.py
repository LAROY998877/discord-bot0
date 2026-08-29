import os
import sqlite3
import discord
from discord.ext.commands import Bot

# 1. التأكد من إنشاء مجلد الـ Volume تلقائياً
os.makedirs("/data", exist_ok=True)

# 2. إعداد قاعدة البيانات داخل الـ Volume
DB_FILE = "/data/database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الأساسية
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        hero TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS economy (
        user_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')

conn.commit()

# 3. إعدادات ديسكورد بوت
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--- البوت متصل الآن بنجاح باسم {bot.user} ---")

# تشغيل البوت
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN) في المتغيرات!")
