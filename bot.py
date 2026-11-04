import os
import discord
from discord.ext import commands
from discord.ui import Select, View

# إعداد الصلاحيات والبوت
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# القائمة المنسدلة للألعاب
class GamesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة X-O", description="لعبة التحدي الكلاسيكية", emoji="❌"),
            discord.SelectOption(label="حجر ورقة مقص", description="اللعبة السريعة الشهيرة", emoji="✂️"),
            discord.SelectOption(label="تخمين الرقم", description="اختبر حظك وذكائك", emoji="🔢"),
        
