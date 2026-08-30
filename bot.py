import discord
from discord import app_commands
from discord.ext import commands

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة الأوامر مع سيرفرات ديسكورد
        await self.tree.sync()
        print("تم مزامنة الأوامر العربية بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"البوت يعمل الآن باسم: {bot.user}")

# أمر المتجر العادي
@bot.tree.command(name="المتجر_العادي", description="عرض وتصفح أقسام المتجر العادي")
@app_commands.describe(القسم="اختر القسم الذي تريد عرضه في المتجر العادي")
@app_commands.choices(القسم=[
    app_commands.Choice(name="الأسلحة", value="weapons"),
    app_commands.Choice(name="الدروع", value="armors"),
    app_commands.Choice(name="المواد العامة", value="items")
])
async def normal_shop(interaction: discord.Interaction, القسم: str):
    await interaction.response.send_message(f"🛒 أهلاً بك في **المتجر العادي**. القسم المختار: **{القسم}**", ephemeral=True)


# أمر المتجر المظلم
@bot.tree.command(name="المتجر_المظلم", description="عرض وتصفح أقسام المتجر المظلم")
@app_commands.describe(القسم="اختر القسم الذي تريد عرضه في المتجر المظلم")
@app_commands.choices(القسم=[
    app_commands.Choice(name="المواد المحرمة", value="forbidden_items"),
    app_commands.Choice(name="السموم", value="poisons"),
    app_commands.Choice(name="الأسلحة السرية", value="secret_weapons")
])
async def dark_shop(interaction: discord.Interaction, القسم: str):
    await interaction.response.send_message(f"🏴‍☠️ أهلاً بك في **المتجر المظلم**. القسم المختار: **{القسم}**", ephemeral=True)


# ضع التوكن الخاص ببوتك هنا
bot.run("YOUR_BOT_TOKEN")
