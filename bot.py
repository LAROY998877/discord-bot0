import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

# ================== الكلاسات والأوامر (تأتي بعد الاستيرادات) ==================
class BattleView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id

    @discord.ui.button(label="معركة ضد وحش 👹", style=discord.ButtonStyle.danger)
    async def fight_monster(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ هذه المعركة ليست لك!", ephemeral=True)
        await interaction.response.edit_message(content="⚔️ تم إقحامك في معركة شرسة ضد وحش الأعماق!", embed=None, view=None)

    @discord.ui.button(label="مبارزة لاعب ⚔️", style=discord.ButtonStyle.primary)
    async def fight_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ هذه المعركة ليست لك!", ephemeral=True)
        await interaction.response.edit_message(content="🛡️ جاري البحث عن خصم عشوائي للمبارزة...", embed=None, view=None)

@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى")
async def battle_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not users_col.find_one({"user_id": user_id}):
        return await interaction.response.send_message("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    embed = discord.Embed(
        title="🏟️ ساحة المعارك الكبرى",
        description="اختر نوع التحدي من الأزرار أدناه:",
        color=discord.Color.dark_gold()
    )
    view = BattleView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

bot.run(DISCORD_TOKEN)
