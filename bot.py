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
        print("✅ تم مزامنة الأوامر ونظام الألقاب بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

# ================== نظام فحص ومنح الألقاب تلقائياً ==================
def check_and_update_titles(user_id):
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return ["المبتدئ"]
    
    unlocked = user_data.get("unlocked_titles", [])
    
    # 1. المبتدئ (يُمنح عند التسجيل تلقائياً)
    if "المبتدئ" not in unlocked:
        unlocked.append("المبتدئ")
        
    # 2. الامبراطور (اجتاز 100 طابق أو أكثر)
    max_floor = user_data.get("max_floor", 0)
    if max_floor >= 100 and "الامبراطور" not in unlocked:
        unlocked.append("الامبراطور")
        
    # 3. الملك (وصل 500 طابق أو أكثر)
    if max_floor >= 500 and "الملك" not in unlocked:
        unlocked.append("الملك")
        
    # 4. القاتل (قتل 20 لاعب في المعارك)
    kills = user_data.get("kills", 0)
    if kills >= 20 and "القاتل" not in unlocked:
        unlocked.append("القاتل")
        
    # 5. السفاح (قتل 50 لاعب في المعارك)
    if kills >= 50 and "السفاح" not in unlocked:
        unlocked.append("السفاح")
        
    # 6. اسطورة القتال (خاض 20 قتال في المعارك)
    battles_played = user_data.get("battles_played", 0)
    if battles_played >= 20 and "اسطورة القتال" not in unlocked:
        unlocked.append("اسطورة القتال")
        
    # 7. الغني (الأول في الترتيب على مستوى الثراء)
    top_rich = list(users_col.find().sort("balance", -1).limit(1))
    if top_rich and top_rich[0]["user_id"] == user_id:
        if "الغني" not in unlocked:
            unlocked.append("الغني")
    
    # 8. اقوى الاقوياء (الأول في الترتيب على مستوى القوة)
    top_power = list(users_col.find().sort("power", -1).limit(1))
    if top_power and top_power[0]["user_id"] == user_id:
        if "اقوى الاقوياء" not in unlocked:
            unlocked.append("اقوى الاقوياء")
            
    users_col.update_one({"user_id": user_id}, {"$set": {"unlocked_titles": unlocked}})
    return unlocked

# ================== نظام التسجيل ==================
@bot.tree.command(name="تسجيل", description="التسجيل في نظام اللعبة والحصول على لقب المبتدئ")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    
    if existing_user:
        return await interaction.response.send_message("❌ أنت مسجل بالفعل في قاعدة البيانات!", ephemeral=True)
    
    new_user = {
        "user_id": user_id,
        "balance": 1000,
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "battles_played": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "unlocked_titles": ["المبتدئ"],
        "inventory": []
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` وردافتك الأولية.", ephemeral=True)

# ================== قائمة اختيار الألقاب المتاحة فقط ==================
class TitleSelect(discord.ui.Select):
    def __init__(self, unlocked_titles):
        # رموز تعبيرية لكل لقب لتزيين القائمة
        title_emojis = {
            "المبتدئ": "🟢",
            "الامبراطور": "👑",
            "الملك": "🔱",
            "الغني": "💰",
            "القاتل": "🗡️",
            "السفاح": "🩸",
            "اسطورة القتال": "⚡",
            "اقوى الاقوياء": "🔥"
        }
        
        options = [
            discord.SelectOption(
                label=title, 
                value=title, 
                emoji=title_emojis.get(title, "✨")
            ) for title in unlocked_titles
        ]
        super().__init__(placeholder="اختر لقباً من ألقابك المتاحة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_title = self.values[0]
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$set": {"custom_title": selected_title}})
        await interaction.response.edit_message(content=f"✨ **تم تفعيل لقبك الجديد بنجاح:** `{selected_title}`", view=None)

class TitleSelectView(discord.ui.View):
    def __init__(self, unlocked_titles):
        super().__init__(timeout=60)
        self.add_item(TitleSelect(unlocked_titles))

class ProfileView(discord.ui.View):
    def __init__(self, author_id, unlocked_titles):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.unlocked_titles = unlocked_titles

    @discord.ui.button(label="اختر اللقب", style=discord.ButtonStyle.blurple, emoji="👑")
    async def change_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TitleSelectView(self.unlocked_titles)
        await interaction.response.send_message("📌 الألقاب المتاحة لك بناءً على إنجازاتك:", view=view, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

# ================== أمر الملف الشخصي ==================
@bot.tree.command(name="الملف", description="عرض الملف الشخصي والإنجازات والألقاب")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    
    # تحديث وفحص الألقاب المتاحة تلقائياً قبل عرض الملف
    unlocked_titles = check_and_update_titles(user_id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    kills = user_data.get("kills", 0)
    battles = user_data.get("battles_played", 0)
    
    embed = discord.Embed(title="📜 الملف الشخصي للمقاتل", color=discord.Color.dark_gold())
    embed.add_field(name="اللقب الحالي", value=f"`{custom_title}`", inline=False)
    embed.add_field(name="الأرصدة", value=f"`{balance:,}` 🪙 | `💎 {diamonds:,}`", inline=False)
    embed.add_field(name="الإحصائيات", value=f"🗼 أعلى طابق: `{max_floor}`\n⚔️ المعارك: `{battles}`\n💀 القتلات: `{kills}`", inline=False)
    embed.add_field(name="الألقاب المتاحة", value=", ".join([f"`{t}`" for t in unlocked_titles]), inline=False)
    
    view = ProfileView(interaction.user.id, unlocked_titles)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# ================== أمر البنك ==================
@bot.tree.command(name="بنك", description="فتح الحساب البنكي")
async def bank_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    bal = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    
    embed = discord.Embed(title="🏦 البنك المركزي", description=f"رصيدك الحالي: `{bal:,}` 🪙\nالألماس: `{diamonds:,}` 💎", color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

# ================== أمر المعارك ==================
@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى")
async def battle_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not users_col.find_one({"user_id": user_id}):
        return await interaction.response.send_message("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    embed = discord.Embed(title="🏟️ ساحة المعارك", description="اختر نوع التحدي من القائمة:", color=discord.Color.dark_gold())
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(DISCORD_TOKEN)
