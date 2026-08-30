import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://botuser:bot12345@laroy998877.makaovo.mongodb.net/discord_bot_db?retryWrites=true&w=majority&authSource=admin")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f"✅ قاعدة البيانات مرتبطة بنجاح البوت {bot.user}!")

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في النظام")
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    if existing_user:
        await interaction.response.send_message("❌ أنت مسجل مسبقاً بالفعل!", ephemeral=True)
        return
    
    users_col.insert_one({
        "user_id": user_id,
        "username": interaction.user.name,
        "balance": 100,  # هدية ترحيبية 100 عملة
        "inventory": []
    })
    await interaction.response.send_message("✅ تم تسجيلك بنجاح وحصلت على 100 عملة هدية ترحيبية!", ephemeral=True)

@bot.tree.command(name="بروفايل", description="عرض ملفك الشخصي ورصيدك")
async def profile(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user = users_col.find_one({"user_id": user_id})
    if not user:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"👤 ملف اللاعب: {interaction.user.name}", color=0x3498db)
    embed.add_field(name="💰 الرصيد", value=f"{user.get('balance', 0)} عملة", inline=False)
    inventory = user.get('inventory', [])
    items_text = ", ".join(inventory) if inventory else "لا توجد مقتنيات حالياً"
    embed.add_field(name="🎒 المقتنيات", value=items_text, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="الابطال", description="عرض قاعة الأبطال الأسطوريين")
async def heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة الأبطال الأسطوريين",
        description="🌸 **إيليا (Ilia):** أميرة النور والرياح\n(مهارات سرعة وسحر هائل).\n\n⚡ **المقاتل الظلي:** بطل هجمات الخفاء والسرعة.\n🛡️ **حارس القلعة:** مدافع لا يُقهر.",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر", description="عرض المتجر لشراء الأسلحة والأدوات")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 المتجر العجيب",
        description="استخدم رصيدك لشراء الأدوات المميزة:\n\n1️⃣ **سيف أسطوري** - السعر: 50 عملة\n2️⃣ **درع حماية** - السعر: 40 عملة",
        color=0xf1c40f
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="لعبة", description="لعبة حظ سريعة لمضاعفة رصيدك أو خسارته")
@app_commands.describe(مبلغ="المبلغ المراد المراهنة به")
async def game(interaction: discord.Interaction, مبلغ: int):
    user_id = str(interaction.user.id)
    user = users_col.find_one({"user_id": user_id})
    
    if not user:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`", ephemeral=True)
        return
        
    if مبلغ <= 0:
        await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
        return
        
    current_balance = user.get("balance", 0)
    if current_balance < مبلغ:
        await interaction.response.send_message(f"❌ رصيدك غير كافي! رصيدك الحالي: {current_balance} عملة", ephemeral=True)
        return

    win = random.choice([True, False])
    if win:
        new_balance = current_balance + مبلغ
        users_col.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
        await interaction.response.send_message(f"🎉 مبروك! لقد فزت في اللعبة وربحت {مبلغ} عملة!\n💰 رصيدك الجديد: {new_balance} عملة")
    else:
        new_balance = current_balance - مبلغ
        users_col.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
        await interaction.response.send_message(f"😢 حظ أوفر في المرة القادمة! لقد خسرت {مبلغ} عملة.\n💰 رصيدك الحالي: {new_balance} عملة")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
