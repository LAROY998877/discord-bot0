import os
import discord
from discord import app_commands
from discord.ext import commands
import pymongo
from datetime import datetime

# ================== إعدادات الاتصال وقاعدة البيانات ==================
MONGO_URI = os.getenv("MONGO_URI", "رابط_الاتصال_الخاص_بـ_MongoDB")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col = db["users"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== دالة التحقق من التسجيل ==================
def is_user_registered(user_id: str) -> bool:
    """التحقق مما إذا كان المستخدم مسجلاً في قاعدة البيانات"""
    return users_col.find_one({"user_id": str(user_id)}) is not None


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✨ تم مزامنة {len(synced)} أمر بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")
    print(f"👑 البوت يعمل الآن بكامل قوته باسم: {bot.user}")


# ================== 1. أمر التسجيل الأسطوري ==================
@bot.tree.command(name="تسجيل", description="📜 التسجيل في عالم الإمبراطورية وإنشاء هوية جديدة")
@app_commands.describe(
    name="اسمك الخاص داخل عالم اللعبة",
    age="عمرك بالسنوات (من 1 إلى 3000)",
    gender="جنس الشخصية"
)
@app_commands.choices(gender=[
    app_commands.Choice(name="♂️ ذكر", value="ذكر"),
    app_commands.Choice(name="♀️ أنثى", value="أنثى")
])
async def register_command(
    interaction: discord.Interaction, 
    name: str, 
    age: int, 
    gender: app_commands.Choice[str]
):
    user_id = str(interaction.user.id)

    # 1. التحقق من التكرار
    if is_user_registered(user_id):
        embed_error = discord.Embed(
            title="⚠️ تنبيه من سجلات الإمبراطورية",
            description="**أنت مسجل بالفعل في النظام!** لا يمكنك إنشاء وثيقة هوية جديدة.",
            color=discord.Color.gold()
        )
        embed_error.set_thumbnail(url=interaction.user.display_avatar.url)
        return await interaction.response.send_message(embed=embed_error, ephemeral=True)

    # 2. التحقق من شرط العمر (حد أقصى 3000)
    if age < 1 or age > 3000:
        embed_age_error = discord.Embed(
            title="❌ خطأ في بيانات السن",
            description="يرجى إدخال عمر صحيح يقع بين **1** و **3000** سنة!",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed_age_error, ephemeral=True)

    # 3. إعداد بيانات المستخدم الجديد
    new_user = {
        "user_id": user_id,
        "name": name,
        "age": age,
        "gender": gender.value,
        "created_at": datetime.utcnow(),
        # الخصائص المالية والقتالية الأساسية
        "balance": 1000,
        "bank": 0,
        "diamonds": 10,
        "power": 100,
        "custom_title": "المبتدئ الأسطوري",
        "selected_hero": "لم يتم الاختيار",
        "inventory": []
    }

    # 4. حفظ البيانات
    users_col.insert_one(new_user)

    # 5. عرض بطاقة التسجيل الأنيقة
    embed_success = discord.Embed(
        title="🎉 مرحباً بك في إمبراطورية العظماء!",
        description="تم إصدار وثيقة هويتك بنجاح، وأصبحت الآن عضواً رسمياً في المملكة.",
        color=discord.Color.purple()
    )
    embed_success.add_field(name="🪪 الاسم المسجل", value=f"`{name}`", inline=True)
    embed_success.add_field(name="⏳ العمر", value=f"`{age}` سنة", inline=True)
    embed_success.add_field(name="👤 الجنس", value=f"`{gender.value}`", inline=True)
    
    embed_success.add_field(
        name="🎁 هدية الانضمام", 
        value="• `1,000` 🪙 عملة ذهبية\n• `10` 💎 جواهر ألماس\n• لقب: **المبتدئ الأسطوري**", 
        inline=False
    )
    
    embed_success.set_thumbnail(url=interaction.user.display_avatar.url)
    embed_success.set_footer(text="الآن يمكنك استخدام جميع أوامر البوت والتفاعل في العالم!", icon_url=interaction.guild.icon.url if interaction.guild else None)

    await interaction.response.send_message(embed=embed_success, ephemeral=False)


# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)

import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")
    
    # 1. حذف الأوامر العامة (Global Commands)
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    print("تم مسح الأوامر العامة بنجاح.")
    
    # 2. حذف الأوامر الخاصة بجميع السيرفرات التي يتواجد فيها البوت
    for guild in bot.guilds:
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"تم مسح الأوامر من السيرفر: {guild.name}")
        
    print("✨ تم تنظيف وحذف جميع الأوامر بالكامل! يمكنك الآن إيقاف البوت وإضافة الكود الجديد الذي تريده.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
