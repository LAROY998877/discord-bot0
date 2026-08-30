import os
import random
import asyncio
import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta

# ==================== الاتصال بـ MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]
guilds_col = db["guilds"]

# معرف المطور (ضع آيدي الحساب الخاص بك هنا)
DEVELOPER_ID = 123456789012345678  # استبدل الرقم بآيدي حسابك

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# دالة مساعدة لجلب أو إنشاء المستخدم
def get_user(user_id):
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

# ==================== 1. نظام التسجيل ====================
class RegisterModal(discord.ui.Modal, title="📋 استمارة التسجيل الإمبراطوري"):
    name_input = discord.ui.TextInput(label="الاسم", placeholder="اكتب اسم شخصيتك...", required=True)
    age_input = discord.ui.TextInput(label="العمر", placeholder="اكتب عمرك (أرقام فقط)...", required=True)
    gender_input = discord.ui.TextInput(label="الجنس", placeholder="ذكر / أنثى", required=True)

    def __init__(self, job):
        super().__init__()
        self.job = job

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age = int(self.age_input.value)
        except ValueError:
            return await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً!", ephemeral=True)

        users_col.update_one(
            {"userId": str(interaction.user.id)},
            {"$set": {
                "isRegistered": True,
                "name": self.name_input.value,
                "age": age,
                "gender": self.gender_input.value,
                "job": self.job
            }},
            upsert=True
        )
        await interaction.response.send_message(f"✅ تم تسجيل شخصيتك بنجاح كـ **{self.job}** يا {self.name_input.value}!", ephemeral=True)

class RegisterSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="قاتل", description="متخصص في الاغتيالات والقتال السريع", emoji="🗡️"),
            discord.SelectOption(label="طباخ", description="يصنع أكلات تزيد من طاقة الفريق", emoji="🍲"),
            discord.SelectOption(label="دكتور", description="يعالج الحلفاء ويزيد من معدلات البقاء", emoji="💉"),
            discord.SelectOption(label="مغامر", description="استكشاف الأبراج المحصنة والكنوز", emoji="🧭"),
            discord.SelectOption(label="مزارع", description="إنتاج الموارد وإدارة الإمدادات", emoji="🌾"),
            discord.SelectOption(label="حداد", description="صناعة وتطوير العتاد والأسلحة", emoji="⚒️"),
        ]
        super().__init__(placeholder="اختر وظيفتك الأساسية...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        job = self.values[0]
        modal = RegisterModal(job=job)
        await interaction.response.send_modal(modal)

class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RegisterSelect())


# ==================== 2. لوحة المطور ====================
class DeveloperPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="💰 عملات لا نهائية", style=discord.ButtonStyle.success)
    async def infinite_money(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != DEVELOPER_ID:
            return await interaction.response.send_message("⛔ هذا الزر للمطور فقط!", ephemeral=True)
        users_col.update_one({"userId": str(interaction.user.id)}, {"$inc": {"balance": 999999999}}, upsert=True)
        await interaction.response.send_message("💎 تم إضافة رصيد لا نهائي إلى حسابك!", ephemeral=True)

    @discord.ui.button(label="🩸 تفعيل السفاح", style=discord.ButtonStyle.danger)
    async def unlock_saffah(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != DEVELOPER_ID:
            return await interaction.response.send_message("⛔ هذا الزر للمطور فقط!", ephemeral=True)
        users_col.update_one(
            {"userId": str(interaction.user.id)},
            {"$set": {"hero": "السفاح"}, "$push": {"titles": "ملك الدماء - السفاح"}},
            upsert=True
        )
        embed = discord.Embed(
            title="🩸 شخصية الأسطورة: السفاح",
            description="**القصة:** كيان مرعب خرج من أعمق سجون الظلام، لا يرحم أحداً ويقطف الأرواح بلمح البصر.\n\n⚡ **المعدلات الخارقة:** الهجوم ∞ | الدفاع حصن مطلق | السرعة سرعة البرق.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== 3. نظام نقابتي ====================
class GuildView(discord.ui.View):
    def __init__(self, user_data):
        super().__init__(timeout=180)
        self.user_data = user_data

    @discord.ui.button(label="🏗️ إنشاء نقابة (400 عملة)", style=discord.ButtonStyle.primary)
    async def create_guild(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_data["balance"] < 400:
            return await interaction.response.send_message("❌ لا تملك 400 عملة لإنشاء نقابة!", ephemeral=True)
        
        await interaction.response.send_message("✍️ اكتب اسم النقابة الجديدة خلال 30 ثانية في الشات:", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", timeout=30.0, check=check)
            guild_name = msg.content
            
            if guilds_col.find_one({"name": guild_name}):
                return await interaction.followup.send("❌ هذا الاسم مستخدم بالفعل لنقابة أخرى!", ephemeral=True)
            
            users_col.update_one({"userId": str(interaction.user.id)}, {"$inc": {"balance": -400}})
            guild_id = guilds_col.insert_one({
                "name": guild_name,
                "leaderId": str(interaction.user.id),
                "members": [str(interaction.user.id)],
                "treasury": 0,
                "warehouse": []
            }).inserted_id
            
            users_col.update_one({"userId": str(interaction.user.id)}, {"$set": {"guildId": str(guild_id)}})
            await interaction.followup.send(f"🎉 تمت الإمبراطورية بنجاح! تم تأسيس نقابة **{guild_name}**.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ انتهى الوقت ولم تقم بكتابة اسم النقابة.", ephemeral=True)


# ==================== 4. نظام الحقيبة ====================
class InventoryView(discord.ui.View):
    def __init__(self, inventory):
        super().__init__(timeout=180)
        self.inventory = inventory

    @discord.ui.button(label="🛡️ ارتداء أغراض", style=discord.ButtonStyle.success)
    async def equip_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.inventory:
            return await interaction.response.send_message("❌ حقيبتك فارغة تماماً!", ephemeral=True)
        await interaction.response.send_message("✨ ميزة ارتداء الأغراض مفعلة وجاهزة لتجهيز العتاد القوي.", ephemeral=True)


# ==================== 5. نظام الأبطال ====================
class HeroesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="🌸 إيليا (Ilia)", style=discord.ButtonStyle.primary)
    async def show_ilia(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🌸 البطلة الأسطورية: إيليا (Ilia)",
            description="**القصة:** ولدت وسط عواصف السحر الأبدي، وتتحكم بالرياح والضوء النقي.\n\n✨ **المهارات:** عصف النور الأبدي، درع الرياح المتألقة.\n💪 **المعدلات:** هجوم خارق ورشاقة مطلقة.",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== 6. البنك الامبراطوري ====================
class ImperialBankView(discord.ui.View):
    def __init__(self, user_data):
        super().__init__(timeout=180)
        self.user_data = user_data

    @discord.ui.button(label="📜 نظام القروض", style=discord.ButtonStyle.danger)
    async def take_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_data["loan"]["amount"] > 0:
            return await interaction.response.send_message("⚠️ لديك قرض سابق لم تقم بسداده بعد!", ephemeral=True)
        
        due = datetime.utcnow() + timedelta(days=1)
        users_col.update_one(
            {"userId": str(interaction.user.id)},
            {"$set": {"loan.amount": 500, "loan.dueDate": due}, "$inc": {"balance": 500}}
        )
        await interaction.response.send_message("🏛️ **تم منحك قرض بقيمة 500 عملة!**\n⚠️ تحذير: إن لم تسدده في موعده، سيقوم البنك ببيع كل معدات وأغراض حقيبتك تلقائياً!", ephemeral=True)


# ==================== الأوامر الرئيسية (Slash Commands) ====================

@bot.tree.command(name="تسجيل", description="تسجيل شخصيتك الجديدة في الإمبراطورية")
async def register_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if user["isRegistered"]:
        return await interaction.response.send_message("❌ أنت مسجل بالفعل مسبقاً!", ephemeral=True)
    await interaction.response.send_message("🛡️ اختر وظيفتك لبدء مغامرتك:", view=RegisterView(), ephemeral=True)

@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطور الحصرية")
async def dev_panel_cmd(interaction: discord.Interaction):
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.response.send_message("⛔ هذا الأمر مخصص للمطور حصراً!", ephemeral=True)
    embed = discord.Embed(title="⚡ لوحة تحكم المطور السيادية", description="اختر العملية المطلوبة:", color=discord.Color.red())
    await interaction.response.send_message(embed=embed, view=DeveloperPanelView(), ephemeral=True)

@bot.tree.command(name="نقابتي", description="إدارة النقابة والمستودع المشترك")
async def guild_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    embed = discord.Embed(title="🏰 نظام النقابة الامبراطورية", description="إدارة الخزانة، التبرعات، والمستودع المشترك.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=GuildView(user), ephemeral=True)

@bot.tree.command(name="الحقيبة", description="عرض حقيبتك ومشترياتك وارتداء العتاد")
async def inventory_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    inv = user.get("inventory", [])
    desc = "\n".join([f"• {item.get('name')}" for item in inv]) if inv else "حقيبتك فارغة تماماً!"
    embed = discord.Embed(title=f"🎒 حقيبة المغامر: {user.get('name', 'غير مسجل')}", description=desc, color=discord.Color.green())
    await interaction.response.send_message(embed=embed, view=InventoryView(inv), ephemeral=True)

@bot.tree.command(name="الابطال", description="قاعة الأبطال وقصصهم ومهاراتهم")
async def heroes_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="⚔️ قاعة الأبطال الأسطوريين", description="اختر بطلاً لاستعراض قصته ومهاراته الخارقة (تضم إيليا وباقي الأبطال).", color=discord.Color.purple())
    await interaction.response.send_message(embed=embed, view=HeroesView(), ephemeral=True)

@bot.tree.command(name="البنك_الامبراطوري", description="البنك المركزي، القروض، وتحويل العملات")
async def bank_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    embed = discord.Embed(title="🏛️ البنك الامبراطوري الفخم", description="خدمات القروض والعقوبات الصارمة وتحويل العملات بين المغامرين.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=ImperialBankView(user), ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت {bot.user} يعمل بكفاءة وقاعدة البيانات مرتبطة بنجاح!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
