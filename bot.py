import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قواعد البيانات المؤقتة
REGISTERED_USERS = {}
USER_ECONOMY = {}          # {user_id: {"coins": int, "inventory": []}}
GUILDS_DATA = {}           # {guild_name: {"owner": id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [id]}}

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 1000, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"]}
    return USER_ECONOMY[user_id]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")


# ==================== 1. نظام التسجيل الإجباري ====================
class RegistrationModal(discord.ui.Modal, title="📝 استمارة التسجيل في اللعبة"):
    def __init__(self, gender: str):
        super().__init__()
        self.gender = gender

    name_input = discord.ui.TextInput(label="اسم الشخصية", placeholder="اكتب اسم شخصيتك هنا...", max_length=30)
    age_input = discord.ui.TextInput(label="العمر", placeholder="اكتب عمرك بالأرقام (مثال: 20)...", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age = int(self.age_input.value)
        except ValueError:
            await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً!", ephemeral=True)
            return

        REGISTERED_USERS[interaction.user.id] = {
            "name": self.name_input.value,
            "age": age,
            "gender": self.gender
        }
        get_user_economy(interaction.user.id) # منح رصيد ابتدائي وعوادات

        embed = discord.Embed(title="✅ تمت عملية التسجيل بنجاح!", description=f"أهلاً بك يا **{self.name_input.value}**!", color=0x2ECC71)
        embed.add_field(name="🏷️ الاسم", value=self.name_input.value, inline=True)
        embed.add_field(name="🎂 العمر", value=str(age), inline=True)
        embed.add_field(name="⚧️ الجنس", value=self.gender, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class GenderSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="اختر جنس الشخصية...",
        options=[
            discord.SelectOption(label="ذكر", description="شخصية ذكر", emoji="👦"),
            discord.SelectOption(label="أنثى", description="شخصية أنثى", emoji="👧"),
            discord.SelectOption(label="آخر", description="غير محدد", emoji="⭐")
        ]
    )
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = RegistrationModal(gender=select.values[0])
        await interaction.response.send_modal(modal)

@bot.tree.command(name="تسجيل", description="تسجيل حسابك الشخصي للبدء باللعبة")
async def register(interaction: discord.Interaction):
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل بالفعل مسبقاً!", ephemeral=True)
        return
    embed = discord.Embed(title="🎮 نظام التسجيل الإجباري", description="اختر جنس الشخصية من القائمة أدناه:", color=0x3498DB)
    await interaction.response.send_message(embed=embed, view=GenderSelectView(), ephemeral=True)


# ==================== 2. نظام النقابات المطور (تكلفة 299 + مستوى أقصى 500) ====================
@bot.tree.command(name="انشاء_نقابة", description="إنشاء نقابة جديدة بسعر 299 عملة")
@app_commands.describe(اسم_النقابة="اسم النقابة التي تريد تأسيسها")
async def create_guild(interaction: discord.Interaction, اسم_النقابة: str):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
        return

    user_id = interaction.user.id
    for g_name, g_info in GUILDS_DATA.items():
        if user_id in g_info["members"]:
            await interaction.response.send_message("❌ أنت منضم أو تمتلك نقابة بالفعل!", ephemeral=True)
            return

    if اسم_النقابة in GUILDS_DATA:
        await interaction.response.send_message("❌ اسم النقابة مستخدم مسبقاً، اختر اسماً آخر!", ephemeral=True)
        return

    eco = get_user_economy(user_id)
    if eco["coins"] < 299:
        await interaction.response.send_message(f"❌ رصيدك غير كافٍ! تحتاج إلى **299 عملة** لإنشاء نقابة (رصيدك الحالي: {eco['coins']} عملة).", ephemeral=True)
        return

    # خصم التكلفة وإنشاء النقابة
    eco["coins"] -= 299
    GUILDS_DATA[اسم_النقابة] = {
        "owner": user_id,
        "level": 1,
        "bank_coins": 0,
        "bank_items": [],
        "members": [user_id]
    }

    await interaction.response.send_message(f"🏰 تم تأسيس نقابة **{اسم_النقابة}** بنجاح مقابل خصم 299 عملة وأنت قائدها!", ephemeral=False)


# ==================== 3. تبرع بالعملات والعتاد للنقابة ====================
@bot.tree.command(name="تبرع_نقابة", description="التبرع بالعملات أو العتاد لخزينة نقابتك")
@app_commands.choices(نوع_التبرع=[
    app_commands.Choice(name="💰 تبرع بالعملات", value="coins"),
    app_commands.Choice(name="⚔️ تبرع بالعتاد (من حقيبتك)", value="item")
])
@app_commands.describe(نوع_التبرع="اختر نوع التبرع", القيمة_أو_الاسم="اكتب عدد العملات أو اسم العتاد المتبرع به")
async def donate_guild(interaction: discord.Interaction, نوع_التبرع: app_commands.Choice[str], القيمة_أو_الاسم: str):
    user_id = interaction.user.id
    if user_id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
        return

    # البحث عن النقابة التي ينتمي إليها اللاعب
    user_guild = None
    for g_name, g_info in GUILDS_DATA.items():
        if user_id in g_info["members"]:
            user_guild = g_name
            break

    if not user_guild:
        await interaction.response.send_message("❌ أنت لست منضماً لأي نقابة لكي تتبرع لها!", ephemeral=True)
        return

    guild_info = GUILDS_DATA[user_guild]
    eco = get_user_economy(user_id)

    if نوع_التبرع.value == "coins":
        try:
            amount = int(القيمة_أو_الاسم)
        except ValueError:
            await interaction.response.send_message("❌ يجيب أن تضع رقماً صحيحاً للعملات!", ephemeral=True)
            return

        if eco["coins"] < amount or amount <= 0:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي للتبرع بـ {amount} عملة!", ephemeral=True)
            return

        eco["coins"] -= amount
        guild_info["bank_coins"] += amount

        # نظام زيادة مستوى النقابة تلقائياً مع كل تبرع (بحد أقصى 500)
        exp_gain = amount // 10
        current_exp = guild_info.get("exp", 0) + exp_gain
        # كل 1000 نقطة خبرة ترفع مستوى النقابة
        while current_exp >= 1000 and guild_info["level"] < 500:
            current_exp -= 1000
            guild_info["level"] += 1
        guild_info["exp"] = current_exp

        await interaction.response.send_message(f"✅ تم التبرع بـ `{amount}` عملة لخزينة نقابة **{user_guild}** بنجاح! (مستوى النقابة الحالي: {guild_info['level']}/500)", ephemeral=False)

    elif نوع_التبرع.value == "item":
        item_name = القيمة_أو_الاسم.strip()
        if item_name not in eco["inventory"]:
            await interaction.response.send_message(f"❌ العنصر `{item_name}` غير موجود في حقيبتك الشخصية!", ephemeral=True)
            return

        eco["inventory"].remove(item_name)
        guild_info["bank_items"].append(item_name)

        await interaction.response.send_message(f"✅ تم التبرع بالقطعة `{item_name}` لخزينة نقابة **{user_guild}** بنجاح!", ephemeral=False)


# ==================== 4. أمر الملف الشخصي ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي المسجل")
async def profile(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك تسجيل حسابك أولاً باستخدام الأمر: `/تسجيل`!", ephemeral=True)
        return

    user_data = REGISTERED_USERS[interaction.user.id]
    eco = get_user_economy(interaction.user.id)
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {interaction.user.display_name}", color=0xE67E22)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🏷️ اسم الشخصية:", value=f"`{user_data['name']}`", inline=False)
    embed.add_field(name="🎂 العمر:", value=f"`{user_data['age']}` سنة", inline=True)
    embed.add_field(name="⚧️ الجنس:", value=f"`{user_data['gender']}`", inline=True)
    embed.add_field(name="💰 العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="🎒 الحقيبة:", value=f", ".join([f"`{i}`" for i in eco['inventory']]) if eco['inventory'] else "فارغة", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
