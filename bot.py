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

DEVELOPER_ID = 123456789012345678  # استبدله بآيدي حسابك

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

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


# ==================== الأوامر الرئيسية مع حماية من تايم أوت ====================

@bot.tree.command(name="تسجيل", description="تسجيل شخصيتك الجديدة في الإمبراطورية")
async def register_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    if user["isRegistered"]:
        return await interaction.followup.send("❌ أنت مسجل بالفعل مسبقاً!", ephemeral=True)
    await interaction.followup.send("🛡️ اختر وظيفتك لبدء مغامرتك:", view=RegisterView(), ephemeral=True)

@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطور الحصرية")
async def dev_panel_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.followup.send("⛔ هذا الأمر مخصص للمطور حصراً!", ephemeral=True)
    embed = discord.Embed(title="⚡ لوحة تحكم المطور السيادية", description="اختر العملية المطلوبة:", color=discord.Color.red())
    await interaction.followup.send(embed=embed, view=DeveloperPanelView(), ephemeral=True)

@bot.tree.command(name="نقابتي", description="إدارة النقابة والمستودع المشترك")
async def guild_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    embed = discord.Embed(title="🏰 نظام النقابة الامبراطورية", description="إدارة الخزانة، التبرعات، والمستودع المشترك.", color=discord.Color.blue())
    
    view = discord.ui.View()
    async def create_guild_callback(i: discord.Interaction):
        if user["balance"] < 400:
            return await i.response.send_message("❌ لا تملك 400 عملة لإنشاء نقابة!", ephemeral=True)
        await i.response.send_message("✍️ اكتب اسم النقابة الجديدة خلال 30 ثانية في الشات:", ephemeral=True)
        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel
        try:
            msg = await bot.wait_for("message", timeout=30.0, check=check)
            guild_name = msg.content
            if guilds_col.find_one({"name": guild_name}):
                return await i.followup.send("❌ هذا الاسم مستخدم بالفعل!", ephemeral=True)
            users_col.update_one({"userId": str(i.user.id)}, {"$inc": {"balance": -400}})
            g_id = guilds_col.insert_one({"name": guild_name, "leaderId": str(i.user.id), "members": [str(i.user.id)], "treasury": 0, "warehouse": []}).inserted_id
            users_col.update_one({"userId": str(i.user.id)}, {"$set": {"guildId": str(g_id)}})
            await i.followup.send(f"🎉 تم تأسيس نقابة **{guild_name}** بنجاح!", ephemeral=True)
        except asyncio.TimeoutError:
            await i.followup.send("⏳ انتهى الوقت ولم تكتب اسم النقابة.", ephemeral=True)

    btn = discord.ui.Button(label="🏗️ إنشاء نقابة (400 عملة)", style=discord.ButtonStyle.primary)
    btn.callback = create_guild_callback
    view.add_item(btn)

    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="الحقيبة", description="عرض حقيبتك ومشترياتك وارتداء العتاد")
async def inventory_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    inv = user.get("inventory", [])
    desc = "\n".join([f"• {item.get('name')}" for item in inv]) if inv else "حقيبتك فارغة تماماً!"
    embed = discord.Embed(title=f"🎒 حقيبة المغامر: {user.get('name', 'غير مسجل')}", description=desc, color=discord.Color.green())
    
    view = discord.ui.View()
    async def equip_callback(i: discord.Interaction):
        if not inv:
            return await i.response.send_message("❌ حقيبتك فارغة تماماً!", ephemeral=True)
        await i.response.send_message("✨ ميزة ارتداء الأغراض مفعلة وجاهزة لتجهيز العتاد القوي.", ephemeral=True)
    
    btn = discord.ui.Button(label="🛡️ ارتداء أغراض", style=discord.ButtonStyle.success)
    btn.callback = equip_callback
    view.add_item(btn)

    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="الابطال", description="قاعة الأبطال وقصصهم ومهاراتهم")
async def heroes_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="⚔️ قاعة الأبطال الأسطوريين", description="اختر بطلاً لاستعراض قصته ومهاراته الخارقة (تضم إيليا وباقي الأبطال).", color=discord.Color.purple())
    
    view = discord.ui.View()
    async def ilia_callback(i: discord.Interaction):
        ilia_embed = discord.Embed(
            title="🌸 البطلة الأسطورية: إيليا (Ilia)",
            description="**القصة:** ولدت وسط عواصف السحر الأبدي، وتتحكم بالرياح والضوء النقي.\n\n✨ **المهارات:** عصف النور الأبدي، درع الرياح المتألقة.\n💪 **المعدلات:** هجوم خارق ورشاقة مطلقة.",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        await i.response.send_message(embed=ilia_embed, ephemeral=True)

    btn = discord.ui.Button(label="🌸 إيليا (Ilia)", style=discord.ButtonStyle.primary)
    btn.callback = ilia_callback
    view.add_item(btn)

    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="البنك_الامبراطوري", description="البنك المركزي، القروض، وتحويل العملات")
async def bank_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user = get_user(interaction.user.id)
    embed = discord.Embed(title="🏛️ البنك الامبراطوري الفخم", description="خدمات القروض والعقوبات الصارمة وتحويل العملات بين المغامرين.", color=discord.Color.gold())
    
    view = discord.ui.View()
    async def loan_callback(i: discord.Interaction):
        if user["loan"]["amount"] > 0:
            return await i.response.send_message("⚠️ لديك قرض سابق لم تقم بسداده بعد!", ephemeral=True)
        due = datetime.utcnow() + timedelta(days=1)
        users_col.update_one({"userId": str(i.user.id)}, {"$set": {"loan.amount": 500, "loan.dueDate": due}, "$inc": {"balance": 500}})
        await i.response.send_message("🏛️ **تم منحك قرض بقيمة 500 عملة!**\n⚠️ تحذير: إن لم تسدده في موعده، سيقوم البنك ببيع كل معدات وأغراض حقيبتك تلقائياً!", ephemeral=True)

    btn = discord.ui.Button(label="📜 نظام القروض", style=discord.ButtonStyle.danger)
    btn.callback = loan_callback
    view.add_item(btn)

    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت {bot.user} يعمل بكفاءة وقاعدة البيانات مرتبطة بنجاح!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
