import os
import random
import asyncio
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta

# ==================== الاتصال الآمن بـ MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI")
DEVELOPER_ID = 123456789012345678  # استبدله بآيدي حسابك

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["discord_bot_db"]
    users_col = db["users"]
    guilds_col = db["guilds"]
    # اختبار الاتصال الفعلي
    client.server_info()
    print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
except Exception as e:
    print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

def get_user(user_id):
    try:
        user = users_col.find_one({"userId": str(user_id)})
        if not user:
            user = {
                "userId": str(user_id),
                "isRegistered": False,
                "name": "",
                "age": 0,
                "gender": "",
                "job": "",
                "balance": 100,
                "titles": [],
                "activeTitle": "",
                "inventory": [],
                "guildId": None,
                "hero": None,
                "loan": {"amount": 0, "dueDate": None}
            }
            users_col.insert_one(user)
        return users_col.find_one({"userId": str(user_id)})
    except Exception as e:
        print(f"❌ خطأ أثناء جلب المستخدم: {e}")
        return None

# ==================== الأوامر الرئيسية ====================

@bot.tree.command(name="تسجيل", description="تسجيل شخصيتك الجديدة في الإمبراطورية")
async def register_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    if not user:
        return await interaction.followup.send("❌ حدث خطأ في الاتصال بقاعدة البيانات!", ephemeral=True)
    if user["isRegistered"]:
        return await interaction.followup.send("❌ أنت مسجل بالفعل مسبقاً!", ephemeral=True)
    
    # منيو الوظائف
    view = discord.ui.View()
    select = discord.ui.Select(placeholder="اختر وظيفتك الأساسية...", options=[
        discord.SelectOption(label="قاتل", emoji="🗡️"),
        discord.SelectOption(label="طباخ", emoji="🍲"),
        discord.SelectOption(label="دكتور", emoji="💉"),
        discord.SelectOption(label="مغامر", emoji="🧭"),
        discord.SelectOption(label="مزارع", emoji="🌾"),
        discord.SelectOption(label="حداد", emoji="⚒️"),
    ])
    
    async def select_callback(i: discord.Interaction):
        job = select.values[0]
        users_col.update_one({"userId": str(i.user.id)}, {"$set": {"isRegistered": True, "job": job}}, upsert=True)
        await i.response.send_message(f"✅ تم تسجيلك بنجاح كـ **{job}**!", ephemeral=True)

    select.callback = select_callback
    view.add_item(select)
    await interaction.followup.send("🛡️ اختر وظيفتك لبدء مغامرتك:", view=view, ephemeral=True)

@bot.tree.command(name="الحقيبة", description="عرض حقيبتك ومشترياتك")
async def inventory_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    if not user:
        return await interaction.followup.send("❌ حدث خطأ في الاتصال بقاعدة البيانات!", ephemeral=True)
    
    inv = user.get("inventory", [])
    desc = "\n".join([f"• {item.get('name')}" for item in inv]) if inv else "حقيبتك فارغة تماماً!"
    embed = discord.Embed(title=f"🎒 حقيبة المغامر: {user.get('name', 'غير مسجل')}", description=desc, color=discord.Color.green())
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="الابطال", description="قاعة الأبطال وقصصهم ومهاراتهم")
async def heroes_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="⚔️ قاعة الأبطال الأسطوريين",
        description="🌸 **إيليا (Ilia):** أميرة النور والرياح (مهارات سرعة وسحر هائل).\n+ 5 أبطال آخرين بانتظارك!",
        color=discord.Color.purple()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="البنك_الامبراطوري", description="البنك المركزي والقروض")
async def bank_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🏛️ البنك الامبراطوري الفخم", description="خدمات القروض والعقوبات الصارمة.", color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت {bot.user} يعمل بكفاءة وقاعدة البيانات مرتبطة بنجاح!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
