import os
import random
import asyncio
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta

# ==================== ضع السطرين هنا في البداية ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

db = client["discord_bot_db"]
users_col = db["users"]
guilds_col = db["guilds"]
# ==============================================================
