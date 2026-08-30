import os
import discord
from discord.ext import commands
from pymongo import MongoClient

# ==================== الاتصال السحابي بـ MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# إنشاء/تحديد قاعدة البيانات والمجموعات
db = client["discord_bot_db"]
users_col = db["users"]      # لبيانات اللاعبين والفلوس والحقيبة
guilds_col = db["guilds"]    # للنقابات والأنظمة المستقبلية

# ==================== إعدادات البوت ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ==================== دوال التعامل مع البيانات السحابية ====================

def get_user(user_id):
    """جلب بيانات اللاعب من السحابة"""
    return users_col.find_one({"_id": str(user_id)})

def register_user(user_id, username):
    """تسجيل لاعب جديد بنظام سحابي مرن للأوامر المستقبلية"""
    if get_user(user_id):
        return False
    
    # هيكل مرن يحفظ أي بيانات قديمة أو جديدة تلقائياً
    user_data = {
        "_id": str(user_id),
        "username": username,
        "coins": 1000,           # الكاش
        "bank": 0,               # البنك
        "level": 1,              # المستوى
        "xp": 0,                 # الخبرة
        "character": "مبتدئ",     # الشخصية
        "inventory": [],         # حقيبة المشتريات والمعدات
        "guild": None            # النقابة
    }
    users_col.insert_one(user_data)
    return True

# ==================== الأوامر الشاملة ====================

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في البوت")
async def register(interaction: discord.Interaction):
    user_id = interaction.user.id
    username = str(interaction.user)
    
    if register_user(user_id, username):
        await interaction.response.send_message(f"✅ تم تسجيلك بنجاح يا {interaction.user.mention}! حصلت على 1000 عملة مجانية.")
    else:
        await interaction.response.send_message("⚠️ حسابك مسجل بالفعل في قاعدة البيانات!")

@bot.tree.command(name="الملف", description="عرض الملف الشخصي والحقيبة والبنك")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ أنت غير مسجل! استخدم أمر `/تسجيل` أولاً.")
        return

    items_text = ", ".join(user.get("inventory", [])) if user.get("inventory") else "لا يوجد"
    
    embed = discord.Embed(title=f"👤 الملف الشخصي: {user['username']}", color=discord.Color.gold())
    embed.add_field(name="💰 الكاش", value=f"{user.get('coins', 0)} عملة", inline=True)
    embed.add_field(name="🏦 البنك", value=f"{user.get('bank', 0)} عملة", inline=True)
    embed.add_field(name="⭐ المستوى", value=f"{user.get('level', 1)}", inline=True)
    embed.add_field(name="⚔️ الشخصية", value=f"{user.get('character', 'مبتدئ')}", inline=True)
    embed.add_field(name="🛡️ النقابة", value=f"{user.get('guild') or 'لا يوجد'}", inline=True)
    embed.add_field(name="🎒 الحقيبة", value=items_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="شراء", description="شراء غرض أو تطبيق تطوير وحفظه فوراً")
async def buy(interaction: discord.Interaction, item: str, price: int):
    user_id = str(interaction.user.id)
    user = get_user(user_id)
    
    if not user:
        await interaction.response.send_message("❌ اكتب `/تسجيل` لإنشاء حساب أولاً.")
        return
        
    if user.get("coins", 0) < price:
        await interaction.response.send_message("❌ لا تملك رصيداً كافياً للشراء!")
        return

    # خصم المبلغ وإضافة العنصر للحقيبة فوراً في السحابة
    users_col.update_one(
        {"_id": user_id},
        {
            "$inc": {"coins": -price},
            "$push": {"inventory": item}
        }
    )
    await interaction.response.send_message(f"🎉 تم شراء **{item}** بنجاح وحفظه في حسابك السحابي!")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت يعمل كـ {bot.user} ومتصل بقاعدة بيانات MongoDB السحابية بنجاح!")

# تشغيل البوت عبر التوكن المسجل في Railway
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
