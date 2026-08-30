import os
import discord
from discord.ext import commands
from pymongo import MongoClient

# ==================== الاتصال السحابي بـ MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

# ==================== إعدادات البوت ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ==================== دوال الحفظ والبيانات ====================

def get_user(user_id):
    """جلب بيانات اللاعب"""
    return users_col.find_one({"_id": str(user_id)})

def register_user(user_id, username):
    """تسجيل لاعب جديد"""
    if get_user(user_id):
        return False
    
    user_data = {
        "_id": str(user_id),
        "username": username,
        "coins": 1000,
        "bank": 0,
        "level": 1,
        "inventory": []
    }
    users_col.insert_one(user_data)
    return True

# ==================== الأوامر الجديدة المعتمدة ====================

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في النظام السحابي")
async def register(interaction: discord.Interaction):
    if register_user(interaction.user.id, str(interaction.user)):
        await interaction.response.send_message(f"✅ تم تسجيلك بنجاح يا {interaction.user.mention}! حصلت على 1000 عملة.")
    else:
        await interaction.response.send_message("⚠️ حسابك مسجل بالفعل!")

@bot.tree.command(name="الملف", description="عرض ملفك الشخصي ورصيدك")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ أنت غير مسجل! استخدم `/تسجيل` أولاً.")
        return

    embed = discord.Embed(title=f"👤 الملف الشخصي: {user['username']}", color=discord.Color.green())
    embed.add_field(name="💰 الكاش", value=f"{user.get('coins', 0)} عملة", inline=True)
    embed.add_field(name="🏦 البنك", value=f"{user.get('bank', 0)} عملة", inline=True)
    await interaction.response.send_message(embed=embed)

# ==================== دالة التطهير والمزامنة ====================

@bot.event
async def on_ready():
    print("🔄 جاري مسح كافة الأوامر السابقة وتنظيف ذاكرة ديسكورد...")
    
    # 1. تفريغ شجرة الأوامر المحلية
    bot.tree.clear_commands(guild=None)
    
    # 2. إعادة إضافات الأوامر الجديدة المعتمدة فقط
    bot.tree.add_command(register)
    bot.tree.add_command(profile)
    
    # 3. إرسال الشجرة المحدثة إلى ديسكورد لحذف القديم واعتماد الجديد
    await bot.tree.sync()
    
    print(f"✨ تم تنظيف البوت بنجاح! يعمل الآن كـ {bot.user} بأوامر جديدة ونظيفة.")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
