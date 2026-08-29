import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قواعد البيانات
REGISTERED_USERS = {}
USER_ECONOMY = {}          # {user_id: {"coins": int, "inventory": [], "hero": str}}
GUILDS_DATA = {}           # {guild_name: {"owner": id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [id]}}

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 1000, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], "hero": None}
    return USER_ECONOMY[user_id]

# تعريف الأبطال (3 ذكور و3 إناث + السفاح السري للمطور)
HEROES_DATA = {
    "لونا": {
        "gender": "أنثى",
        "title": "حارسة النجوم",
        "story": "وُدت تحت ضوء نيزك أزرق نادر، وشرعت في رحلة طويلة لجمع شظايا الكون المفقودة وإنقاذ عالمها.",
        "power": "قوة الضوء القمري والتلاعب بالجاذبية",
        "skills": "1. انفجار نيزكي\n2. درع النجوم\n3. ومضة قمرية",
        "art": "[ البطلة: لونا - حارسة النجوم 🌙 ]"
    },
    "فيكتوريا": {
        "gender": "أنثى",
        "title": "فارس العاصفة",
        "story": "قائدة عسكرية سابقة امتزجت روحها بالبرق لتصبح عاصفة بشرية لا تُطهر.",
        "power": "التحكم المطلق بالكهرباء والسرعة الخارقة",
        "skills": "1. صاعقة البرق\n2. درع البلازما\n3. سرعة الإعصار",
        "art": "[ البطلة: فيكتوريا - فارس العاصفة ⚡ ]"
    },
    "سراب": {
        "gender": "أنثى",
        "title": "سيدة الظلال",
        "story": "نشأت في أعمق كهوف القارة المنسية، وتعلقت بفنون التخفي حتى أصبحت شبحاً لا يرى.",
        "power": "الانتقال الآني والتلاعب بالأوهام",
        "skills": "1. طعنة الظل\n2. اختفاء مطلق\n3. استنساخ الوهم",
        "art": "[ البطلة: سراب - سيدة الظلال 👥 ]"
    },
    "ثورن": {
        "gender": "ذكر",
        "title": "عملاق الجبال",
        "story": "محارب شجاع دافع عن بوابات الشتاء لمئات السنين، درعه مصنوع من حجر النيزك.",
        "power": "صلابة حديدية وقوة بدنية هائلة",
        "skills": "1. ضربة الأرض\n2. جدار الحجر\n3. غضب العمالقة",
        "art": "[ البطل: ثورن - عملاق الجبال 🏔️ ]"
    },
    "كايدن": {
        "gender": "ذكر",
        "title": "سياف اللهيب",
        "story": "حارق الممالك القديمة، أقسم على الانتقام لعائلته بسيفه المشتعل بنيران التنين.",
        "power": "إشعال النيران القرمزية وقطع الدروع",
        "skills": "1. سيف اللهيب\n2. دائرة النار\n3. انفجار السوبرنوفا",
        "art": "[ البطل: كايدن - سياف اللهيب 🔥 ]"
    },
    "زيك": {
        "gender": "ذكر",
        "title": "مهندس الموت الأبدي",
        "story": "عالم عبقري استخدم التكنولوجيا المحرمة لدمج التروس الميكانيكية بجسده.",
        "power": "التحكم بالأنظمة التقنية ونشر النبضات",
        "skills": "1. مدفع البلازما\n2. درع النانو\n3. اختراق الأنظمة",
        "art": "[ البطل: زيك - مهندس الموت ⚙️ ]"
    },
    "السفاح": {
        "gender": "سري",
        "title": "حاصد الأرواح المرعب",
        "story": "كائن أسطوري مرعب هبط من عوالم مظلمة، مخصص لصانع هذا النظام حصرياً.",
        "power": "إفناء الوجود وبث الرعب المطلق",
        "skills": "1. لمسة الموت الفوري\n2. هالة الرعب الأبدي\n3. محو الوجود",
        "art": "[ 💀 البطل السري للمطور: السفاح المرعب 💀 ]"
    }
}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")


# ==================== 1. نظام التسجيل واختيار البطل ====================
class HeroSelectView(discord.ui.View):
    def __init__(self, gender: str, name_val: str, age_val: int):
        super().__init__(timeout=60)
        self.gender = gender
        self.name_val = name_val
        self.age_val = age_val

        options = []
        for h_name, h_data in HEROES_DATA.items():
            if h_data["gender"] == gender:
                options.append(discord.SelectOption(label=h_name, description=h_data["title"], emoji="⚔️"))
        
        self.add_item(HeroDropdown(options, self.name_val, self.age_val, self.gender))

class HeroDropdown(discord.ui.Select):
    def __init__(self, options, name_val, age_val, gender):
        super().__init__(placeholder="اختر بطلك الأسطوري...", options=options)
        self.name_val = name_val
        self.age_val = age_val
        self.gender = gender

    async def callback(self, interaction: discord.Interaction):
        chosen_hero = self.values[0]
        REGISTERED_USERS[interaction.user.id] = {
            "name": self.name_val,
            "age": self.age_val,
            "gender": self.gender,
            "hero": chosen_hero
        }
        eco = get_user_economy(interaction.user.id)
        eco["hero"] = chosen_hero

        h_info = HEROES_DATA[chosen_hero]
        embed = discord.Embed(title="🎉 تم التسجيل واختيار البطل بنجاح!", description=f"أهلاً بك يا **{self.name_val}** في عالم المغامرات!", color=0x9B59B6)
        embed.add_field(name="🛡️ البطل المختار", value=f"**{chosen_hero}** ({h_info['title']})", inline=False)
        embed.add_field(name="📖 القصة", value=h_info["story"], inline=False)
        embed.add_field(name="⚡ القوة الخاصة", value=h_info["power"], inline=True)
        embed.add_field(name="⚔️ المهارات", value=h_info["skills"], inline=True)
        embed.add_field(name="🎨 الشكل", value=h_info["art"], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class RegistrationModal(discord.ui.Modal, title="📝 استمارة التسجيل واختيار البطل"):
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

        view = HeroSelectView(self.gender, self.name_input.value, age)
        await interaction.response.send_message("🎮 اختر بطلك الأسطوري من القائمة أدناه:", view=view, ephemeral=True)

class GenderSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="اختر جنس الشخصية للبدء...",
        options=[
            discord.SelectOption(label="ذكر", description="عرض الأبطال الذكور", emoji="👦"),
            discord.SelectOption(label="أنثى", description="عرض الأبطال الإناث", emoji="👧")
        ]
    )
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = RegistrationModal(gender=select.values[0])
        await interaction.response.send_modal(modal)

@bot.tree.command(name="تسجيل", description="تسجيل حسابك الشخصي واختيار بطلك الأسطوري")
async def register(interaction: discord.Interaction):
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل بالفعل مسبقاً! يمكنك تغيير بطلك عبر `/تغيير_البطل`", ephemeral=True)
        return
    embed = discord.Embed(title="🎮 نظام التسجيل الأسطوري", description="اختر جنس الشخصية أولاً:", color=0x3498DB)
    await interaction.response.send_message(embed=embed, view=GenderSelectView(), ephemeral=True)


# ==================== 2. شخصية "السفاح" السرية للمطور فقط ====================
@bot.tree.command(name="البطل_السري", description="أمر خاص بالمطور لفتح شخصية السفاح المرعبة")
async def secret_developer_hero(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر خاص بالمطور فقط ولا يمكن لأحد الوصول إليه!", ephemeral=True)
        return

    if interaction.user.id not in REGISTERED_USERS:
        REGISTERED_USERS[interaction.user.id] = {"name": "المطور العظيم", "age": 999, "gender": "سري", "hero": "السفاح"}
    else:
        REGISTERED_USERS[interaction.user.id]["hero"] = "السفاح"

    eco = get_user_economy(interaction.user.id)
    eco["hero"] = "السفاح"

    h_info = HEROES_DATA["السفاح"]
    embed = discord.Embed(title="💀 تم تفعيل شخصية المطور السرية: السفاح!", description=h_info["story"], color=0x000000)
    embed.add_field(name="⚡ القوة الخاصة", value=h_info["power"], inline=False)
    embed.add_field(name="⚔️ المهارات", value=h_info["skills"], inline=False)
    embed.add_field(name="🎨 الشكل", value=h_info["art"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== 3. تغيير الشخصية بسعر 200 عملة ====================
class ChangeHeroView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

        options = [
            discord.SelectOption(label="لونا", description="حارسة النجوم (أنثى)", emoji="🌙"),
            discord.SelectOption(label="فيكتوريا", description="فارس العاصفة (أنثى)", emoji="⚡"),
            discord.SelectOption(label="سراب", description="سيدة الظلال (أنثى)", emoji="👥"),
            discord.SelectOption(label="ثورن", description="عملاق الجبال (ذكر)", emoji="🏔️"),
            discord.SelectOption(label="كايدن", description="سياف اللهيب (ذكر)", emoji="🔥"),
            discord.SelectOption(label="زيك", description="مهندس الموت (ذكر)", emoji="⚙️")
        ]
        self.add_item(ChangeHeroDropdown(options))

class ChangeHeroDropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="اختر بطلك الجديد...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if eco["coins"] < 200:
            await interaction.response.send_message(f"❌ رصيد 200 عملة مطلوب لتغيير الشخصية! رصيدك الحالي: {eco['coins']} عملة.", ephemeral=True)
            return

        new_hero = self.values[0]
        eco["coins"] -= 200
        REGISTERED_USERS[user_id]["hero"] = new_hero
        eco["hero"] = new_hero

        h_info = HEROES_DATA[new_hero]
        embed = discord.Embed(title="🔄 تم تغيير البطل بنجاح مقابل 200 عملة!", description=f"بطلك الجديد الآن هو: **{new_hero}** ({h_info['title']})", color=0xE67E22)
        embed.add_field(name="🎨 الشكل", value=h_info["art"], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="تغيير_البطل", description="تغيير بطلك الحالي مقابل 200 عملة")
async def change_hero(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
        return

    view = ChangeHeroView(interaction.user.id)
    await interaction.response.send_message("🔄 اختر البطل الجديد الذي ترغب بالانتقال إليه (التكلفة 200 عملة):", view=view, ephemeral=True)


# ==================== 4. إنشاء نقابة بسعر 299 عملة ====================
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

    eco["coins"] -= 299
    GUILDS_DATA[اسم_النقابة] = {
        "owner": user_id,
        "level": 1,
        "bank_coins": 0,
        "bank_items": [],
        "members": [user_id]
    }

    await interaction.response.send_message(f"🏰 تم تأسيس نقابة **{اسم_النقابة}** بنجاح مقابل خصم 299 عملة وأنت قائدها!", ephemeral=False)


# ==================== 5. تبرع بالعملات والعتاد للنقابة (بحد أقصى مستوى 500) ====================
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
            await interaction.response.send_message("❌ يجب أن تضع رقماً صحيحاً للعملات!", ephemeral=True)
            return

        if eco["coins"] < amount or amount <= 0:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي للتبرع بـ {amount} عملة!", ephemeral=True)
            return

        eco["coins"] -= amount
        guild_info["bank_coins"] += amount

        exp_gain = amount // 10
        current_exp = guild_info.get("exp", 0) + exp_gain
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


# ==================== 6. أمر الملف الشخصي ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وبطلك المسجل")
async def profile(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك تسجيل حسابك أولاً باستخدام الأمر: `/تسجيل`!", ephemeral=True)
        return

    user_data = REGISTERED_USERS[interaction.user.id]
    eco = get_user_economy(interaction.user.id)
    hero_name = user_data.get("hero", "غير محدد")
    hero_info = HEROES_DATA.get(hero_name, {})
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {interaction.user.display_name}", color=0xE67E22)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🏷️ اسم الشخصية:", value=f"`{user_data['name']}`", inline=True)
    embed.add_field(name="🎂 العمر:", value=f"`{user_data['age']}` سنة", inline=True)
    embed.add_field(name="⚧️ الجنس:", value=f"`{user_data['gender']}`", inline=True)
    embed.add_field(name="⚔️ البطل الأسطوري:", value=f"**{hero_name}** ({hero_info.get('title', 'بدون لقب')})", inline=False)
    embed.add_field(name="💰 العملات:", value=f"`{eco['coins']}` عملة", inline=True)
    embed.add_field(name="🎒 الحقيبة:", value=f", ".join([f"`{i}`" for i in eco['inventory']]) if eco['inventory'] else "فارغة", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
