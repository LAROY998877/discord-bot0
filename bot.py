import os
import random
import asyncio
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
devs_col = db["devs"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

OWNER_ID = 1103985971638325269

def is_developer(user_id):
    if user_id == OWNER_ID:
        return True
    return devs_col.find_one({"user_id": str(user_id)}) is not None

# ================== قاعدة بيانات الأبطال والطوابق ==================
HEROES_DATA = {
    "assassin_dev": {"name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)", "emoji": "🩸", "power_boost": 999999}
}

# ================== موديل إهداء عتاد ==================
class DevGiftModal(discord.ui.Modal, title="إهداء عتاد لعضو"):
    user_id_input = discord.ui.TextInput(label="معرف المستخدم (ID)", placeholder="مثال: 123456789012345678", required=True)
    gear_name = discord.ui.TextInput(label="اسم قطعة العتاد أو السلاح", placeholder="مثال: سيف التنين الاسطوري", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = self.user_id_input.value.strip()
            users_col.update_one({"user_id": target_id}, {"$push": {"inventory": self.gear_name.value}}, upsert=True)
            await interaction.followup.send(f"🎁 **تم إرسال العتاد بنجاح!** حصل المستخدم `<@{target_id}>` على القطعة: `{self.gear_name.value}` ⚔️", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ: تأكد من صحة معرف المستخدم.", ephemeral=True)

# ================== موديل إضافة رصيد ==================
class DevAddBalanceModal(discord.ui.Modal, title="إضافة رصيد لعضو"):
    user_id_input = discord.ui.TextInput(label="معرف المستخدم (ID)", placeholder="مثال: 123456789012345678", required=True)
    amount = discord.ui.TextInput(label="المبلغ المراد إضافته", placeholder="مثال: 500000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = self.user_id_input.value.strip()
            val = int(self.amount.value)
            users_col.update_one({"user_id": target_id}, {"$inc": {"balance": val}}, upsert=True)
            await interaction.followup.send(f"✅ تم إضافة `{val:,}` 🪙 إلى محفظة المستخدم `<@{target_id}>` بنجاح!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح ومتاكد من المعرف!", ephemeral=True)

# ================== موديل إضافة مطور جديد ==================
class DevAddModal(discord.ui.Modal, title="إضافة مطور جديد"):
    user_id_input = discord.ui.TextInput(label="معرف المستخدم (ID) للعضو المراد ترقيته", placeholder="مثال: 123456789012345678", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = self.user_id_input.value.strip()
            devs_col.update_one({"user_id": target_id}, {"$set": {"user_id": target_id}}, upsert=True)
            await interaction.followup.send(f"🛠️ **تمت الترقية بنجاح!** أصبح المستخدم `<@{target_id}>` مطوراً معتمداً في النظام الإمبراطوري.", ephemeral=True)
        except:
            await interaction.followup.send("❌ حدث خطأ أثناء إضافة المطور.", ephemeral=True)


# ================== لوحة أزرار المطور الفورية ==================
class DevControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="تفعيل السفاح", style=discord.ButtonStyle.danger, emoji="🩸", row=0)
    async def assassin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        assassin = HEROES_DATA["assassin_dev"]
        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "selected_hero": assassin['name'],
                    "power": assassin['power_boost'],
                    "max_floor": 999,
                    "kills": 99999,
                    "custom_title": "💀 حاكم الأبعاد ومالك السفاح"
                }
            },
            upsert=True
        )
        await interaction.followup.send("🩸 **تم تفعيل طاقة السفاح المطلقة وإحصائياتك المرعبة بنجاح!**", ephemeral=True)

    @discord.ui.button(label="ثرواتانهائية", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def wealth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": 999999999, "diamonds": 999999999}},
            upsert=True
        )
        await interaction.followup.send("💎 **تم ضخ الثروات اللانهائية!** حصلت على عملات عادية والنادرة بلا حدود في خزنتك.", ephemeral=True)

    @discord.ui.button(label="أقصى عتاد", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def max_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "aim": 9999999999, "evasion": 9999999999,
                    "attack": 9999999999, "accuracy": 9999999999,
                    "defense": 9999999999, "critical": 9999999999,
                    "magic": 9999999999, "intelligence": 9999999999
                }
            },
            upsert=True
        )
        await interaction.followup.send("⚡ **تمت ترقية كافة المعدلات والعتاد للأقصى المطلق!**", ephemeral=True)

    @discord.ui.button(label="إهداء عتاد", style=discord.ButtonStyle.secondary, emoji="🎁", row=1)
    async def gift_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DevGiftModal())

    @discord.ui.button(label="إضافة رصيد", style=discord.ButtonStyle.secondary, emoji="🪙", row=1)
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DevAddBalanceModal())

    @discord.ui.button(label="إضافة مطور", style=discord.ButtonStyle.secondary, emoji="🛠️", row=1)
    async def add_dev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DevAddModal())


@bot.tree.command(name="المطور", description="لوحة السيطرة والتحكم العليا للمطورين")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة السيطرة والتحكم العليا للمطورين",
        description="أهلاً بك أيها الحاكم المطلق. استخدم الأزرار أدناه لتنفيذ الأوامر الخارقة بشكل فوري:",
        color=discord.Color.dark_embed()
    )
    await interaction.response.send_message(embed=embed, view=DevControlView(), ephemeral=True)


# ================== أمر الملف والتسجيل ==================
@bot.tree.command(name="الملف", description="عرض السجل الأسطوري والمعدلات القتالية الشاملة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    selected_hero = user_data.get("selected_hero", "لم يتم اختيار بطل بعد")
    power = user_data.get("power", 100)
    kills = user_data.get("kills", 0)
    
    aim = user_data.get("aim", 10)
    evasion = user_data.get("evasion", 10)
    attack = user_data.get("attack", 10)
    accuracy = user_data.get("accuracy", 10)
    defense = user_data.get("defense", 10)
    critical = user_data.get("critical", 10)
    magic = user_data.get("magic", 10)
    intelligence = user_data.get("intelligence", 10)
    
    embed_color = discord.Color.dark_red() if "السفاح" in selected_hero else discord.Color.gold()
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=embed_color
    )
    embed.add_field(name="👑 اللقب الحالي", value=custom_title, inline=True)
    embed.add_field(name="🦸‍♂️ البطل المختار", value=selected_hero, inline=True)
    embed.add_field(name="⚡ طاقة القتال", value=f"{power:,}", inline=True)
    
    stats_text = (
        f"🎯 **التصويب:** `{aim:,}` | 💨 **المراوغة:** `{evasion:,}`\n"
        f"🗡️ **الهجوم:** `{attack:,}` | 👁️ **الدقة:** `{accuracy:,}`\n"
        f"🛡️ **الدفاع:** `{defense:,}` | 💥 **القاتلة:** `{critical:,}`\n"
        f"🔮 **السحر:** `{magic:,}` | 🧠 **الذكاء:** `{intelligence:,}`"
    )
    embed.add_field(name="📊 ترسانة المعدلات القتالية المطلقة", value=stats_text, inline=False)
    
    embed.add_field(name="🏢 أعلى طابق متجاوز", value=str(max_floor), inline=True)
    embed.add_field(name="💀 الخصوم المقضي عليهم", value=str(kills), inline=True)
    embed.add_field(name="💰 المحفظة والبنك", value=f"{balance:,} 🪙 | 💳 {bank:,} 🪙", inline=False)
    embed.add_field(name="💎 الألماس والنقاد", value=f"{diamonds:,} 💎", inline=True)

    embed.set_footer(text=f"معرف المستخدم: {user_id}", icon_url=interaction.user.display_avatar.url)
    await interaction.followup.send(embed=embed, ephemeral=False)

@bot.tree.command(name="تسجيل", description="التسجيل في نظام اللعبة والحصول على لقب المبتدئ")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    if existing_user:
        return await interaction.response.send_message("❌ أنت مسجل بالفعل في قاعدة البيانات!", ephemeral=True)
    
    new_user = {
        "user_id": user_id,
        "balance": 1000,
        "bank": 0,
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "battles_played": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "unlocked_titles": ["المبتدئ"],
        "selected_hero": "لم يتم اختيار بطل بعد",
        "inventory": [],
        "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
        "defense": 10, "critical": 10, "magic": 10, "intelligence": 10
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

bot.run(DISCORD_TOKEN)
