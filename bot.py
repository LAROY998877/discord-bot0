import os
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# الاتصال بقاعدة البيانات وتعريف المتغيرات لتجنب خطأ NameError
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://botuser:bot12345@laroy998877.makaovo.mongodb.net/discord_bot_db?retryWrites=true&w=majority&authSource=admin")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]  # هذا السطر يحل مشكلة users_col is not defined

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f"✅ و قاعدة البيانات مرتبطة بنجاح البوت {bot.user}!")

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في النظام")
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    try:
        existing_user = users_col.find_one({"user_id": user_id})
        if existing_user:
            await interaction.response.send_message("❌ أنت مسجل مسبقاً بالفعل!", ephemeral=True)
            return
        
        users_col.insert_one({
            "user_id": user_id,
            "username": interaction.user.name,
            "balance": 0
        })
        await interaction.response.send_message("✅ تم تسجيلك بنجاح في قاعدة البيانات!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("❌ حدث خطأ في الاتصال بقاعدة البيانات!", ephemeral=True)
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")

@bot.tree.command(name="الابطال", description="عرض قاعة الأبطال")
async def heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة الأبطال الأسطوريين",
        description="🌸 إيليا (Ilia): أميرة النور والرياح\n(مهارات سرعة وسحر هائل).\n+ 5 أبطال آخرين بانتظارك!",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
