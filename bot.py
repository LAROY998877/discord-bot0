import sqlite3
import discord
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجدول إذا لم يكن موجوداً
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        points INTEGER DEFAULT 0
    )
"""
)
db_connection.commit()

# 2. إعداد البوت
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")


# 3. أمر لحفظ أو تحديث بيانات المستخدم في قاعدة البيانات
@bot.command(name="حفظ", help="يقوم بحفظ أو تحديث نقاطك في قاعدة بيانات SQLite")
async def save_data(ctx, points: int):
    user_id = ctx.author.id
    username = str(ctx.author)

    # التحقق من وجود المستخدم مسبقاً أو تحديث بياناته
    cursor.execute(
        """
        INSERT INTO user_data (user_id, username, points) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) 
        DO UPDATE SET points = ?, username = ?
    """,
        (user_id, username, points, points, username),
    )
    db_connection.commit()

    await ctx.send(
        f"تم حفظ بياناتك بنجاح يا {ctx.author.mention}! النقاط المسجلة: {points}"
    )


# 4. أمر لاسترجاع البيانات المخزنة من قاعدة البيانات
@bot.command(name="بياناتي", help="يعرض بياناتك المخزنة في قاعدة البيانات")
async def get_data(ctx):
    user_id = ctx.author.id

    cursor.execute("SELECT points FROM user_data WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        await ctx.send(f"رصيدك المحفوظ في قاعدة البيانات هو: {result[0]} نقطة.")
    else:
        await ctx.send("لا توجد بيانات مخزنة لك حتى الآن. استخدم أمر `!حفظ` أولاً.")


# ضع التوكن الخاص بك هنا
# bot.run("YOUR_BOT_TOKEN")
