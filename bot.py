import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قواعد البيانات الشاملة
REGISTERED_USERS = {}
USER_ECONOMY = {}          # {user_id: {"coins": int, "inventory": [], "hero": str}}
GUILDS_DATA = {}           # {guild_name: {"owner": id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [id]}}

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 1000, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], "hero": None}
    return USER_ECONOMY[user_id]

# تعريف الأبطال (3 ذكور و3 إناث + السفاح)
HEROES_DATA = {
    "لونا": {"gender": "أنثى", "title": "حارسة النجوم", "story": "وُدت تحت ضوء نيزك أزرق نادر لإنقاذ عالمها.", "power": "الضوء القمري", "skills": "انفجار نيزكي", "art": "[ لونا 🌙 ]"},
    "فيكتوريا": {"gender": "أنثى", "title": "فارس العاصفة", "story": "امتزجت روحها بالبرق لتصبح عاصفة بشرية.", "power": "الكهرباء والسرعة", "skills": "صاعقة البرق", "art": "[ فيكتوريا ⚡ ]"},
    "سراب": {"gender": "أنثى", "title": "سيدة الظلال", "story": "تعلقت بفنون التخفي حتى أصبحت شبحاً لا يرى.", "power": "الانتقال الآني", "skills": "طعنة الظل", "art": "[ سراب 👥 ]"},
    "ثورن": {"gender": "ذكر", "title": "عملاق الجبال", "story": "محارب شجاع درعه مصنوع من حجر النيزك.", "power": "صلابة حديدية", "skills": "ضربة الأرض", "art": "[ ثورن 🏔️ ]"},
    "كايدن": {"gender": "ذكر", "title": "سياف اللهيب", "story": "أقسم على الانتقام بسيفه المشتعل بنيران التنين.", "power": "إشعال النيران", "skills": "سيف اللهيب", "art": "[ كايدن 🔥 ]"},
    "زيك": {"gender": "ذكر", "title": "مهندس الموت", "story": "استخدم التكنولوجيا المحرمة لدمج التروس بجسده.", "power": "التحكم التقني", "skills": "مدفع البلازما", "art": "[ زيك ⚙️ ]"},
    "السفاح": {"gender": "سري", "title": "حاصد الأرواح", "story": "كائن أسطوري مرعب مخصص للمطور حصرياً.", "power": "إفناء الوجود", "skills": "لمسة الموت", "art": "[ 💀 السفاح المرعب 💀 ]"}
}

# معدات متجر الظلام (أعلى 3 رتب: الشيطان، الجحيم، السفاح)
DARK_SHOP_ITEMS = {
    "خنجر الشيطان الأبدي": {"price": 150, "rank": "🔴 الشيطان", "power": "قوة تدميرية +999"},
    "درع لهيب الجحيم": {"price": 250, "rank": "🔥 الجحيم", "power": "دفاع مطلق +1500"},
    "عباءة السفاح الدموية": {"price": 400, "rank": "⚔️ السفاح", "power": "سرعة وتخفي خارق +3000"}
}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")


# ==================== 1. نظام التسجيل واختيار البطل ====================
class HeroSelectView(discord.ui.View):
    def __init__(self, gender: str, name_val: str, age_val: int):
        super().__init__(timeout=60)
        options = [discord.SelectOption(label=h_name, description=h_data["title"], emoji="⚔️") for h_name, h_data in HEROES_DATA.items() if h_data["gender"] == gender]
        self.add_item(HeroDropdown(options, name_val, age_val, gender))

class HeroDropdown(discord.ui.Select):
    def __init__(self, options, name_val, age_val, gender):
        super().__init__(placeholder="اختر بطلك الأسطوري...", options=options)
        self.name_val, self.age_val, self.gender = name_val, age_val, gender

    async def callback(self, interaction: discord.Interaction):
        chosen_hero = self.values[0]
        REGISTERED_USERS[interaction.user.id] = {"name": self.name_val, "age": self.age_val, "gender": self.gender, "hero": chosen_hero}
        get_user_economy(interaction.user.id)["hero"] = chosen_hero
        h_info = HEROES_DATA[chosen_hero]
        
        embed = discord.Embed(title="🎉 تم التسجيل واختيار البطل بنجاح!", description=f"أهلاً بك يا **{self.name_val}**!", color=0x9B59B6)
        embed.add_field(name="🛡️ البطل", value=f"**{chosen_hero}** ({h_info['title']})", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RegistrationModal(discord.ui.Modal, title="📝 استمارة التسجيل"):
    def __init__(self, gender: str):
        super().__init__()
        self.gender = gender

    name_input = discord.ui.TextInput(label="اسم الشخصية", placeholder="اكتب اسم شخصيتك...", max_length=30)
    age_input = discord.ui.TextInput(label="العمر", placeholder="اكتب عمرك بالأرقام...", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age = int(self.age_input.value)
        except ValueError:
            await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً!", ephemeral=True)
            return
        await interaction.response.send_message("🎮 اختر بطلك الأسطوري:", view=HeroSelectView(self.gender, self.name_input.value, age), ephemeral=True)

class GenderSelectView(discord.ui.View):
    @discord.ui.select(placeholder="اختر جنس الشخصية...", options=[discord.SelectOption(label="ذكر", emoji="👦"), discord.SelectOption(label="أنثى", emoji="👧")])
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(RegistrationModal(gender=select.values[0]))

@bot.tree.command(name="تسجيل", description="تسجيل حسابك واختيار بطلك")
async def register(interaction: discord.Interaction):
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل مسبقاً!", ephemeral=True)
        return
    await interaction.response.send_message("🎮 نظام التسجيل:", view=GenderSelectView(), ephemeral=True)


# ==================== 2. لوحة المطور بنظام المنيو المتطور ====================
class DevDashboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الحصول على عملات لا نهائية", description="إضافة 999,999 عملة لحسابك", emoji="💰"),
            discord.SelectOption(label="الحصول على عتاد سري", description="إضافة معدات نادرة لحقيبتك", emoji="⚔️"),
            discord.SelectOption(label="عرض إحصائيات النظام", description="معرفة عدد اللاعبين والنقابات", emoji="📊")
        ]
        super().__init__(placeholder="اختر أمراً من لوحة تحكم المطور...", options=options)

    async def callback(self, interaction: discord.Interaction):
        eco = get_user_economy(interaction.user.id)
        if self.values[0] == "الحصول على عملات لا نهائية":
            eco["coins"] += 999999
            await interaction.response.send_message("💰 تم إضافة 999,999 عملة بنجاح إلى رصيدك!", ephemeral=True)
        elif self.values[0] == "الحصول على عتاد سري":
            eco["inventory"].extend(["سيف المطور الأسطوري", "درع الإله المطلق"])
            await interaction.response.send_message("⚔️ تم إضافة عتاد سري وخارق إلى حقيبتك!", ephemeral=True)
        elif self.values[0] == "عرض إحصائيات النظام":
            await interaction.response.send_message(f"📊 اللاعبين: {len(REGISTERED_USERS)} | النقابات: {len(GUILDS_DATA)}", ephemeral=True)

class DevDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevDashboardSelect())

@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الخاصة بالمطور بنظام المنيو")
async def dev_dashboard(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر خاص بالمطور فقط!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🛠️ لوحة تحكم المطور المركزية", description="اختر من القائمة أدناه ما تحتاجه لتطوير اللعبة:", color=0xE74C3C)
    await interaction.response.send_message(embed=embed, view=DevDashboardView(), ephemeral=True)


# ==================== 3. متجر الظلام (Dark Shop) ====================
class DarkShopSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=item_name, description=f"السعر: {data['price']} عملة | الرتبة: {data['rank']}", emoji="🔥") for item_name, data in DARK_SHOP_ITEMS.items()]
        super().__init__(placeholder="اختر قطعة مظلمة لشرائها...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
            return

        item_name = self.values[0]
        item_data = DARK_SHOP_ITEMS[item_name]
        eco = get_user_economy(user_id)

        if eco["coins"] < item_data["price"]:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي! تحتاج إلى {item_data['price']} عملة.", ephemeral=True)
            return

        eco["coins"] -= item_data["price"]
        eco["inventory"].append(item_name)
        await interaction.response.send_message(f"🌑 تم شراء `{item_name}` بنجاح برتبة **{item_data['rank']}** وقوة `{item_data['power']}`!", ephemeral=True)

class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DarkShopSelect())

@bot.tree.command(name="متجر_الظلام", description="فتح متجر الظلام للمعدات الشيطانية والأسطورية")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🌑 متجر الظلام الأسطوري", description="معدات الرتب العليـا (الشيطان - الجحيم - السفاح):", color=0x111111)
    for name, data in DARK_SHOP_ITEMS.items():
        embed.add_field(name=f"{data['rank']} | {name}", value=ل={`السعر: ${data['price']} عملة`} + `\nقوة: ${data['power']}`, inline=False)
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)


# ==================== 4. باقي الأوامر القديمة (تغيير البطل، النقابات، الملف) ====================
class ChangeHeroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        options = [discord.SelectOption(label=h_name, description=h_data["title"]) for h_name in HEROES_DATA.keys() if h_name != "السفاح"]
        self.add_item(ChangeHeroDropdown(options))

class ChangeHeroDropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="اختر بطلك الجديد...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        eco = get_user_economy(user_id)
        if eco["coins"] < 200:
            await interaction.response.send_message(f"❌ تحتاج 200 عملة لتغيير البطل! رصيدك: {eco['coins']}", ephemeral=True)
            return
        new_hero = self.values[0]
        eco["coins"] -= 200
        REGISTERED_USERS[user_id]["hero"] = new_hero
        eco["hero"] = new_hero
        await interaction.response.send_message(f"🔄 تم تغيير البطل إلى **{new_hero}** مقابل 200 عملة!", ephemeral=True)

@bot.tree.command(name="تغيير_البطل", description="تغيير بطلك مقابل 200 عملة")
async def change_hero(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await interaction.response.send_message("🔄 اختر البطل الجديد:", view=ChangeHeroView(), ephemeral=True)

@bot.tree.command(name="انشاء_نقابة", description="إنشاء نقابة بسعر 299 عملة")
async def create_guild(interaction: discord.Interaction, اسم_النقابة: str):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً!", ephemeral=True)
        return
    eco = get_user_economy(interaction.user.id)
    if eco["coins"] < 299:
        await interaction.response.send_message("❌ رصيدك لا يكفي (تحتاج 299 عملة)!", ephemeral=True)
        return
    eco["coins"] -= 299
    GUILDS_DATA[اسم_النقابة] = {"owner": interaction.user.id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [interaction.user.id]}
    await interaction.response.send_message(f"🏰 تم تأسيس نقابة **{اسم_النقابة}** بنجاح!", ephemeral=False)

@bot.tree.command(name="تبرع_نقابة", description="التبرع بالعملات أو العتاد للنقابة")
@app_commands.choices(نوع_التبرع=[app_commands.Choice(name="عملات", value="coins"), app_commands.Choice(name="عتاد", value="item")])
async def donate_guild(interaction: discord.Interaction, نوع_التبرع: app_commands.Choice[str], القيمة_أو_الاسم: str):
    user_id = interaction.user.id
    if user_id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً!", ephemeral=True)
        return
    user_guild = next((g for g, info in GUILDS_DATA.items() if user_id in info["members"]), None)
    if not user_guild:
        await interaction.response.send_message("❌ لست منضماً لأي نقابة!", ephemeral=True)
        return
    eco = get_user_economy(user_id)
    guild_info = GUILDS_DATA[user_guild]

    if نوع_التبرع.value == "coins":
        amount = int(القيمة_أو_الاسم)
        if eco["coins"] < amount:
            await interaction.response.send_message("❌ رصيدك لا يكفي!", ephemeral=True)
            return
        eco["coins"] -= amount
        guild_info["bank_coins"] += amount
        guild_info["level"] = min(500, guild_info["level"] + (amount // 1000))
        await interaction.response.send_message(f"✅ تم تبرع {amount} عملة للنقابة بنجاح!", ephemeral=False)
    elif نوع_التبرع.value == "item":
        if القيمة_أو_الاسم not in eco["inventory"]:
            await interaction.response.send_message("❌ العنصر غير موجود بحقيبتك!", ephemeral=True)
            return
        eco["inventory"].remove(القيمة_أو_الاسم)
        guild_info["bank_items"].append(القيمة_أو_الاسم)
        await interaction.response.send_message(f"✅ تم تبرع القطعة للنقابة!", ephemeral=False)

@bot.tree.command(name="الملف", description="عرض ملفك الشخصي")
async def profile(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    user_data = REGISTERED_USERS[interaction.user.id]
    eco = get_user_economy(interaction.user.id)
    embed = discord.Embed(title=f"👑 الملف الشخصي | {interaction.user.display_name}", color=0xE67E22)
    embed.add_field(name="الشخصية", value=user_data['name'], inline=True)
    embed.add_field(name="البطل", value=user_data['hero'], inline=True)
    embed.add_field(name="العملات", value=f"{eco['coins']} عملة", inline=True)
    embed.add_field(name="الحقيبة", value=", ".join(eco['inventory']) if eco['inventory'] else "فارغة", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
