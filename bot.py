import os
import json
import random
import asyncio
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== إعداد قاعدة بيانات SQLite الدائمة ====================
DB_FILE = "database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        hero TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS economy (
        user_id TEXT PRIMARY KEY,
        coins INTEGER,
        gems INTEGER,
        inventory TEXT,
        gear_level INTEGER,
        max_floor INTEGER,
        loan_debt INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS guilds (
        guild_name TEXT PRIMARY KEY,
        owner TEXT,
        level INTEGER,
        exp INTEGER,
        bank_coins INTEGER,
        bank_items TEXT,
        members TEXT
    )
''')
conn.commit()

# دوال إدارة البيانات عبر SQLite
def get_user_profile(user_id):
    cursor.execute("SELECT name, age, gender, hero FROM users WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if row:
        return {"name": row[0], "age": row[1], "gender": row[2], "hero": row[3]}
    return None

def save_user_profile(user_id, name, age, gender, hero):
    cursor.execute("INSERT OR REPLACE INTO users (user_id, name, age, gender, hero) VALUES (?, ?, ?, ?, ?)",
                   (str(user_id), name, age, gender, hero))
    conn.commit()

def get_user_economy(user_id):
    cursor.execute("SELECT coins, gems, inventory, gear_level, max_floor, loan_debt FROM economy WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if not row:
        default_inv = json.dumps(["سيف التدريب الخشبي", "درع الجلد الطبيعي"])
        cursor.execute("INSERT OR REPLACE INTO economy (user_id, coins, gems, inventory, gear_level, max_floor, loan_debt) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (str(user_id), 1000, 20, default_inv, 1, 1, 0))
        conn.commit()
        return {"coins": 1000, "gems": 20, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], "gear_level": 1, "max_floor": 1, "loan_debt": 0}
    return {
        "coins": row[0],
        "gems": row[1],
        "inventory": json.loads(row[2]),
        "gear_level": row[3],
        "max_floor": row[4],
        "loan_debt": row[5] if row[5] is not None else 0
    }

def update_economy(user_id, eco):
    cursor.execute("UPDATE economy SET coins = ?, gems = ?, inventory = ?, gear_level = ?, max_floor = ?, loan_debt = ? WHERE user_id = ?",
                   (eco["coins"], eco["gems"], json.dumps(eco["inventory"]), eco["gear_level"], eco["max_floor"], eco.get("loan_debt", 0), str(user_id)))
    conn.commit()

# تعريف الأبطال
HEROES_DATA = {
    "ثورن": {"gender": "ذكر", "title": "عملاق الجبال", "story": "محارب شجاع درعه مصنوع من حجر النيزك.", "power": "صلابة حديدية", "skills": "ضربة الأرض", "art": "[ ثورن 🏔️ ]"},
    "كايدن": {"gender": "ذكر", "title": "سياف اللهيب", "story": "أقسم على الانتقام بسيفه المشتعل بنيران التنين.", "power": "إشعال النيران", "skills": "سيف اللهيب", "art": "[ كايدن 🔥 ]"},
    "زيك": {"gender": "ذكر", "title": "مهندس الموت", "story": "استخدم التكنولوجيا المحرمة لدمج التروس بجسده.", "power": "التحكم التقني", "skills": "مدفع البلازما", "art": "[ زيك ⚙️ ]"},
    "لونا": {"gender": "أنثى", "title": "حارسة النجوم", "story": "وُدت تحت ضوء نيزك أزرق نادر لإنقاذ عالمها.", "power": "الضوء القمري", "skills": "انفجار نيزكي", "art": "[ لونا 🌙 ]"},
    "فيكتوريا": {"gender": "أنثى", "title": "فارس العاصفة", "story": "امتزجت روحها بالبرق لتصبح عاصفة بشرية.", "power": "الكهرباء والسرعة", "skills": "صاعقة البرق", "art": "[ فيكتوريا ⚡ ]"},
    "سراب": {"gender": "أنثى", "title": "سيدة الظلال", "story": "تعلقت بفنون التخفي حتى أصبحت شبحاً لا يرى.", "power": "الانتقال الآني", "skills": "طعنة الظل", "art": "[ سراب 👥 ]"},
    "أوريرا": {"gender": "أنثى", "title": "أميرة الفجر", "story": "ابنة الشمس الأولى التي تستمد قوتها من خيوط الفجر الأولى.", "power": "شعاع الشمس الأبدي", "skills": "تطهير النور المقدس", "art": "[ أوريرا ☀️ ]"},
    "ساكورا": {"gender": "أنثى", "title": "زهرة الساموراي", "story": "مقاتلة شرسة تدمج رقة بتلات الكرز بحد السيف القاتل.", "power": "رياح البتلات القاتلة", "skills": "رقصة الكرز القاتلة", "art": "[ ساكورا 🌸 ]"},
    "ميرال": {"gender": "أنثى", "title": "ساحرة الزمن", "story": "تتحكم في نسيج الزمن لتلعب بأعصاب أعدائها في المعارك.", "power": "إبطاء وتجميد الزمن", "skills": "شق الأبعاد والزمن", "art": "[ ميرال ⏳ ]"},
    "السفاح": {"gender": "سري", "title": "حاصد الأرواح السري", "story": "كائن أسطوري مرعب مخصص للمطور حصرياً بقوة مطلقة.", "power": "إفناء الوجود المطلق", "skills": "لمسة الموت والدمار", "art": "[ 💀 السفاح المرعب 💀 ]"}
}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح مع نظام البنك وقاعدة بيانات SQLite!")
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
        super().__init__(placeholder="اختر بطلك الأسطوري المفضّل...", options=options)
        self.name_val, self.age_val, self.gender = name_val, age_val, gender

    async def callback(self, interaction: discord.Interaction):
        chosen_hero = self.values[0]
        save_user_profile(interaction.user.id, self.name_val, self.age_val, self.gender, chosen_hero)
        get_user_economy(interaction.user.id) # إنشاء محفظة افتراضية
        
        h_info = HEROES_DATA[chosen_hero]
        embed = discord.Embed(title="🎉 تم التسجيل واختيار البطل بنجاح!", description=f"أهلاً بك في عالم المغامرة يا **{self.name_val}**!", color=0x9B59B6)
        embed.add_field(name="🛡️ البطل المختار", value=f"**{chosen_hero}** ({h_info['title']})\n{h_info['art']}", inline=False)
        embed.add_field(name="⚡ القدرة", value=h_info['power'], inline=True)
        embed.add_field(name="🌀 المهارة", value=h_info['skills'], inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RegistrationModal(discord.ui.Modal, title="📝 استمارة التسجيل الأسطورية"):
    def __init__(self, gender: str):
        super().__init__()
        self.gender = gender

    name_input = discord.ui.TextInput(label="اسم الشخصية", placeholder="اكتب اسم شخصيتك هنا...", max_length=30)
    age_input = discord.ui.TextInput(label="العمر", placeholder="اكتب عمرك بالأرقام...", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age = int(self.age_input.value)
        except ValueError:
            await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً!", ephemeral=True)
            return
        await interaction.response.send_message(f"🎮 ممتاز! اختر بطلك من فئة ({'الذكور' if self.gender == 'ذكر' else 'الإناث'}):", view=HeroSelectView(self.gender, self.name_input.value, age), ephemeral=True)

class GenderSelectView(discord.ui.View):
    @discord.ui.select(placeholder="اختر جنس الشخصية لعرض الأبطال...", options=[
        discord.SelectOption(label="ذكر", description="عرض أبطال الذكور الشجعان", emoji="👦"),
        discord.SelectOption(label="أنثى", description="عرض بطلات الإناث الأسطوريات", emoji="👧")
    ])
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(RegistrationModal(gender=select.values[0]))

@bot.tree.command(name="تسجيل", description="تسجيل حسابك واختيار بطلك الأسطوري")
async def register(interaction: discord.Interaction):
    if get_user_profile(interaction.user.id):
        await interaction.response.send_message("⚠️ أنت مسجل مسبقاً بالفعل!", ephemeral=True)
        return
    await interaction.response.send_message("🎮 مرحباً بك! يرجى اختيار جنس الشخصية للبدء:", view=GenderSelectView(), ephemeral=True)

# ==================== 2. نظام البنك (تحويل، قروض، سداد، بيع عتاد عند التخلف) ====================
class LoanModal(discord.ui.Modal, title="🏦 طلب قرض مصرفي"):
    loan_amount_input = discord.ui.TextInput(label="مبلغ القرض المطلوب", placeholder="أدخل المبلغ (الحد الأقصى 20,000 عملة)...", max_length=6)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.loan_amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب إدخال رقم صحيح!", ephemeral=True)
            return

        if not (100 <= amount <= 20000):
            await interaction.response.send_message("❌ مبلغ القرض يجب أن يكون بين **100 و 20,000** عملة!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if eco.get("loan_debt", 0) > 0:
            await interaction.response.send_message(f"❌ لديك قرض سابق لم تقم بسداده بقيمة `{eco['loan_debt']:,}` عملة! يجب سداده أولاً.", ephemeral=True)
            return

        eco["loan_debt"] = amount
        eco["coins"] += amount
        update_economy(user_id, eco)

        warning_text = (
            f"⚠️ **تحذير مصرفي هام وخطير جداً!**\n"
            f"لقد استلمت قرضاً بقيمة **{amount:,}** عملة.\n"
            f"**تنبيه:** إذا لم تقم بسداد هذا القرض بالكامل قبل خوضك لأي معركة أو استخدام عتادك، **سيقوم البنك ببيع معداتك وعتادك بالكامل ومصادرة مستواك لتسوية الدين** فوراً دون إنذار آخر!"
        )

        embed = discord.Embed(title="🏦 تمت الموافقة على القرض الإمبراطورية", description=warning_text, color=0xE74C3C)
        embed.add_field(name="🪙 الرصيد المضاف", value=f"+{amount:,} عملة", inline=True)
        embed.add_field(name="💳 الدين المترتب عليك", value=f"{amount:,} عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TransferModal(discord.ui.Modal, title="💸 تحويل عملات لشخص آخر"):
    target_id_input = discord.ui.TextInput(label="آي دي (ID) المستلم", placeholder="الصق ايدي الشخص هنا...", max_length=25)
    amount_input = discord.ui.TextInput(label="المبلغ المراد تحويله", placeholder="أدخل المبلغ...", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_id = self.target_id_input.value.strip()
            amount = int(self.amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ تأكد من صحة الآي دي والمبلغ المدخل!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
            return

        if str(interaction.user.id) == target_id:
            await لنفسه = True # تعبير مجازي
            await interaction.response.send_message("❌ لا يمكنك تحويل العملات لنفسك!", ephemeral=True)
            return

        sender_id = interaction.user.id
        sender_eco = get_user_economy(sender_id)

        if sender_eco["coins"] < amount:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي! رصيدك الحالي: `{sender_eco['coins']:,}` عملة.", ephemeral=True)
            return

        # التحقق من وجود المستلم
        target_eco = get_user_economy(target_id)
        if not get_user_profile(target_id):
            await interaction.response.send_message("❌ هذا المستخدم غير مسجل في النظام البنكي أو الأسطوري!", ephemeral=True)
            return

        # تنفيذ التحويل
        sender_eco["coins"] -= amount
        target_eco["coins"] += amount

        update_economy(sender_id, sender_eco)
        update_economy(target_id, target_eco)

        embed = discord.Embed(title="💸 تم التحويل بنجاح!", description=f"تم إرسال `{amount:,} عملة` بنجاح إلى المغامر صاحب الآي دي: `{target_id}`", color=0x2ECC71)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="طلب قرض مصرفي", style=discord.ButtonStyle.danger, emoji="💳")
    async def request_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لاستخدام البنك!", ephemeral=True)
            return
        await interaction.response.send_modal(LoanModal())

    @discord.ui.button(label="سداد القرض بالكامل", style=discord.ButtonStyle.green, emoji="💵")
    async def repay_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        profile = get_user_profile(user_id)
        if not profile:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
            return

        eco = get_user_economy(user_id)
        debt = eco.get("loan_debt", 0)

        if debt <= 0:
            await interaction.response.send_message("🎉 ليس لديك أي ديون معلقة في البنك!", ephemeral=True)
            return

        if eco["coins"] < debt:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي لسداد القرض! ديونك: `{debt:,}` عملة | رصيدك: `{eco['coins']:,}` عملة.", ephemeral=True)
            return

        eco["coins"] -= debt
        eco["loan_debt"] = 0
        update_economy(user_id, eco)

        embed = discord.Embed(title="🎉 تم سداد القرض بنجاح!", description=f"لقد قمت بسداد كامل ديونك للبنك بقيمة `{debt:,}` عملة. أصبح سجلك المالي نظيفاً!", color=0x2ECC71)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="تحويل عملات لشخص", style=discord.ButtonStyle.blurple, emoji="💸")
    async def transfer_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
            return
        await interaction.response.send_modal(TransferModal())

@bot.tree.command(name="البنك", description="فتح واجهة البنك الإمبراطورية (قروض، سداد، وتحويل)")
async def bank(interaction: discord.Interaction):
    user_id = interaction.user.id
    eco = get_user_economy(user_id)
    
    embed = discord.Embed(
        title="🏦 ⟪ المـَصـْرِف الإمـْبـرَاطـُوري الـْمـَرْكَزِي ⟫ 🏦",
        description="مرحباً بك في بنك الأبراج العظيم. يمكنك هنا إدارة رصيدك، طلب القروض، سداد الديون، أو تحويل العملات للمغامرين الآخرين.",
        color=0xF1C40F
    )
    embed.add_field(name="🪙 رصيدك الحالي", value=f"`{eco['coins']:,}` عملة", inline=True)
    embed.add_field(name="💳 الديون / القروض المعلقة", value=f"`{eco.get('loan_debt', 0):,}` عملة", inline=True)
    embed.set_footer(text="⚠️ تذكير: عدم سداد القروض يعرض معداتك وعتادك للبيع الفوري والمصادرة!")
    
    await interaction.response.send_message(embed=embed, view=BankView(), ephemeral=False)

@bot.tree.command(name="تحويل", description="تحويل عملات مباشرة إلى مستخدم آخر عبر الآي دي")
@app_commands.describe(member="الشخص المراد التحويل له", amount="المبلغ المراد تحويله")
async def transfer_slash(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = interaction.user.id
    target_id = member.id

    if not get_user_profile(sender_id):
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    if not get_user_profile(target_id):
        await interaction.response.send_message(f"❌ المستخدم {member.mention} غير مسجل في النظام الأسطوري!", ephemeral=True)
        return

    if sender_id == target_id:
        await interaction.response.send_message("❌ لا يمكنك تحويل العملات لنفسك!", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
        return

    sender_eco = get_user_economy(sender_id)
    if sender_eco["coins"] < amount:
        await interaction.response.send_message(f"❌ رصيدك الحالي لا يكفي! لديك `{sender_eco['coins']:,}` عملة فقط.", ephemeral=True)
        return

    target_eco = get_user_economy(target_id)

    sender_eco["coins"] -= amount
    target_eco["coins"] += amount

    update_economy(sender_id, sender_eco)
    update_economy(target_id, target_eco)

    embed = discord.Embed(title="💸 تمت عملية التحويل بنجاح", description=f"قمت بتحويل `{amount:,}` عملة إلى {member.mention} بكل سلاسة!", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, ephemeral=False)

# ==================== 3. نظام الطوابق والمعارك (مع فحص القروض وبيع العتاد عند التخلف) ====================
class FloorInputModal(discord.ui.Modal, title="⚔️ بوابة صعود الطوابق الإمبراطورية"):
    floor_input = discord.ui.TextInput(label="أدخل رقم الطابق المطلوب صعوده", placeholder="اكتب رقماً من 1 إلى 10000...", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_floor = int(self.floor_input.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب أن تدخل رقماً صحيحاً للطابق!", ephemeral=True)
            return

        if not (1 <= target_floor <= 10000):
            await interaction.response.send_message("❌ رقم الطابق يجب أن يكون محصوراً حصرياً بين **1 و 10,000**!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        # 🚨 فحص القرض غير السداد (تفعيل العقوبة: بيع المعدات والعتاد لتسوية الدين)
        if eco.get("loan_debt", 0) > 0:
            debt = eco["loan_debt"]
            # عقوبة المصادرة وبيع العتاد
            eco["gear_level"] = 1  # إعادة مستوى العتاد للصفر/الأساس
            eco["inventory"] = ["سيف التدريب الخشبي (تم بيعه لتسوية الدين)", "درع الجلد الطبيعي"]
            eco["loan_debt"] = 0  # تسوية الدين مقابل بيع العتاد
            update_economy(user_id, eco)

            punish_embed = discord.Embed(
                title="🚨 تنبيه مصرفي إمبراطوري: مصادرة وبيع العتاد!",
                description=f"لقد حاولت دخول المعركة وعليك قرض متأخر بقيمة `{debt:,}` عملة ولم تقم بسداده!\n\n"
                            f"⚖️ **تم تطبيق العقوبة:** تدخل البنك الإمبراطوري وقام ببيع عتادك بالكامل ومصادرة مستواك لتسوية الدين المترتب عليك. تم إعادة عتادك للمستوى `1`.",
                color=0xE74C3C
            )
            await interaction.response.send_message(embed=punish_embed, ephemeral=True)
            return

        if 1 <= target_floor <= 500:
            difficulty = "🟢 سهل"
            monsters = ["زومبي مبتدئ متفسخ", "هيكل عظمي تايه", "عنكبوت الكهف السام"]
        elif 501 <= target_floor <= 2000:
            difficulty = "🟡 متوسط"
            monsters = ["محارب زومبي منبوذ", "وحش المستنقع المظلم", "ذئب الظلال الشرس"]
        elif 2001 <= target_floor <= 5000:
            difficulty = "🟠 صعب"
            monsters = ["شيطان الحمم البركانية", "عملاق الحجارة الفولاذي", "فارس الظلام الدموي"]
        else:
            difficulty = "🔴 مستحيل / أسطوري"
            monsters = ["تنين الأبعاد الأبدي", "حاصد الأرواح الملكي المرعب", "ملك الشياطين الأبدي"]

        monster_name = random.choice(monsters)
        gear_lv = eco.get("gear_level", 1)
        hero_max_hp = 1000 + (gear_lv * 50)
        monster_max_hp = 800 + (target_floor * 35)

        hero_hp = hero_max_hp
        monster_hp = monster_max_hp

        await interaction.response.send_message(
            f"⚔️ **جارٍ فتح بوابة الطابق `{target_floor}` ({difficulty})...**\n"
            f"الخصم الحالي في ساحة المعركة: **{monster_name}**\n"
            f"استعد لتلاحم السيوف والضربات المباشرة!", 
            ephemeral=False
        )
        msg = await interaction.original_response()

        for round_num in range(1, 5):
            await asyncio.sleep(1.8)
            hero_dmg = random.randint(200, 500) + (gear_lv * 15)
            monster_hp = max(0, monster_hp - hero_dmg)
            
            monster_dmg = random.randint(100, 300) + (target_floor * 5)
            hero_hp = max(0, hero_hp - monster_dmg)

            hero_bar = "█" * int((hero_hp / hero_max_hp) * 10) + "░" * (10 - int((hero_hp / hero_max_hp) * 10))
            monster_bar = "█" * int((monster_hp / monster_max_hp) * 10) + "░" * (10 - int((monster_hp / monster_max_hp) * 10))

            battle_embed = discord.Embed(title=f"🔥 معركة شرسة في الطابق {target_floor} (الجولة {round_num}/4)", description=f"الساحة مشتعلة بين البطل والوحش **{monster_name}**!", color=0x992D22)
            battle_embed.add_field(name=f"🛡️ صحة البطل ({interaction.user.display_name})", value=f"`{hero_bar}`\n❤️ الدم المتبقي: **{hero_hp:,} / {hero_max_hp:,}**\n💥 ضربتك: `-{hero_dmg:,}`", inline=False)
            battle_embed.add_field(name=f"👹 صحة الوحش ({monster_name})", value=f"`{monster_bar}`\n🩸 الدم المتبقي: **{monster_hp:,} / {monster_max_hp:,}**\n⚡ ضربته: `-{monster_dmg:,}`", inline=False)
            await msg.edit(embed=battle_embed)

            if monster_hp <= 0 or hero_hp <= 0:
                break

        await asyncio.sleep(1.5)
        is_victory = monster_hp <= monster_max_hp * 0.5 or hero_hp > monster_hp or hero_hp > 200

        if is_victory:
            coins_reward = target_floor * 150
            gems_reward = random.randint(1, max(2, target_floor // 200 + 1))
            eco["coins"] += coins_reward
            eco["gems"] += gems_reward
            if target_floor > eco.get("max_floor", 1):
                eco["max_floor"] = target_floor
            update_economy(user_id, eco)

            win_embed = discord.Embed(title=f"👑 انتصار أسطوري ساحق في الطابق {target_floor}!", description=f"لقد تمكنت من دحر الوحش **{monster_name}** وإخضاع الطابق بالكامل!", color=0x2ECC71)
            win_embed.add_field(name="🪙 العملات المكتسبة", value=f"+{coins_reward:,} عملة", inline=True)
            win_embed.add_field(name="💎 جواهر الظلام", value=f"+{gems_reward} جوهرة", inline=True)
            win_embed.add_field(name="🏆 أعلى طابق", value=f"الطابق {eco['max_floor']}", inline=False)
            await msg.edit(embed=win_embed, view=None)
        else:
            lost_coins = min(eco["coins"], 100 * (target_floor // 10 + 1))
            eco["coins"] = max(0, eco["coins"] - lost_coins)
            update_economy(user_id, eco)

            lose_embed = discord.Embed(title=f"💀 هزيمة قاسية في الطابق {target_floor}!", description=f"تفوق عليك الوحش المرعب **{monster_name}**!", color=0xE74C3C)
            lose_embed.add_field(name="⚠️ الخسائر", value=f"فقدت `{lost_coins:,}` عملة أثناء الهروب!", inline=False)
            await msg.edit(embed=lose_embed, view=None)

class UpgradeGearModal(discord.ui.Modal, title="⚒️ منصة تطوير العتاد (حتى 10000)"):
    levels_input = discord.ui.TextInput(label="عدد المستويات المراد ترقيتها", placeholder="أدخل المستويات (كل مستوى يكلف 50 عملة)...", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            add_levels = int(self.levels_input.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب إدخال رقم صحيح!", ephemeral=True)
            return

        if add_levels <= 0:
            await interaction.response.send_message("❌ يجب أن تكون المستويات أكبر من صفر!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)
        current_gear = eco.get("gear_level", 1)

        if current_gear + add_levels > 10000:
            await interaction.response.send_message(f"❌ عذراً، الحد الأقصى لتطوير العتاد هو **10,000** مستوى! مستواك الحالي: {current_gear}", ephemeral=True)
            return

        cost = add_levels * 50
        if eco["coins"] < cost:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي! تحتاج إلى `{cost:,}` عملة عادية.", ephemeral=True)
            return

        eco["coins"] -= cost
        eco["gear_level"] += add_levels
        update_economy(user_id, eco)

        embed = discord.Embed(title="⚒️ تمت ترقية العتاد بنجاح!", description=f"قمت بتطوير عتادك بمقدار `{add_levels}` مستوى!", color=0xF1C40F)
        embed.add_field(name="⚡ مستوى العتاد الجديد", value=f"**{eco['gear_level']} / 10,000**", inline=True)
        embed.add_field(name="🪙 التكلفة", value=f"`{cost:,}` عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TowerPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="بدء المغامرة وصعود الطوابق", style=discord.ButtonStyle.green, emoji="⚔️")
    async def start_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لتبدأ صعود الطوابق!", ephemeral=True)
            return
        await interaction.response.send_modal(FloorInputModal())

    @discord.ui.button(label="تطوير العتاد (حتى 10000)", style=discord.ButtonStyle.blurple, emoji="⚒️")
    async def upgrade_gear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لتتمكن من تطوير عتادك!", ephemeral=True)
            return
        await interaction.response.send_modal(UpgradeGearModal())

    @discord.ui.button(label="حقيبة العتاد والملخص", style=discord.ButtonStyle.grey, emoji="🎒")
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ لم تقم بالتسجيل بعد!", ephemeral=True)
            return
        eco = get_user_economy(interaction.user.id)
        embed = discord.Embed(title="🏰 لوحة حالة برج المغامرات والعتاد", description=f"ملخص بيانات المغامر:", color=0x3498DB)
        embed.add_field(name="⚡ مستوى العتاد الحالي", value=f"**{eco.get('gear_level', 1)} / 10,000**", inline=True)
        embed.add_field(name="🏆 أعلى طابق", value=f"الطابق **{eco.get('max_floor', 1)}**", inline=True)
        embed.add_field(name="🪙 العملات العادية", value=f"{eco['coins']:,} عملة", inline=True)
        embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
        embed.add_field(name="💳 الديون البنكية", value=f"{eco.get('loan_debt', 0):,} عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="الطابق", description="فتح القائمة الإمبراطورية لصعود الطوابق وتطوير العتاد")
async def tower(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏰 ⟪ بـرْج العـَظـَمـَة والمـُغـَامـَرَات الإمـْبـرَاطـُوريـة ⟫ 🏰",
        description="مرحباً بك في برج التحدي الأسطوري! اختر ما تحتاجه بكل سلاسة من الأزرار أدناه:",
        color=0x8E44AD
    )
    await interaction.response.send_message(embed=embed, view=TowerPanelView(), ephemeral=False)

# ==================== الملف الشخصي ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وبطلك الأسطوري")
async def profile(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_data = get_user_profile(user_id)
    if not user_data:
        await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    
    eco = get_user_economy(user_id)
    hero_name = user_data.get("hero", "غير محدد")
    hero_info = HEROES_DATA.get(hero_name, {"title": "بلا لقب", "story": "لا توجد قصة", "power": "عادي", "skills": "لا توجد", "art": "[ شخصية عادية 🛡️ ]"})
    
    embed = discord.Embed(title=f"👑 الملف الشخصي الأسطوري | {user_data['name']}", description=f"**اللقب الأسطوري:** {hero_info['title']}\n📖 *{hero_info['story']}*", color=0xE67E22)
    embed.add_field(name="⚔️ البطل المختار والشكل المرئي", value=f"**{hero_name}**\n{hero_info['art']}", inline=False)
    embed.add_field(name="⚡ القدرة الخاصة", value=hero_info['power'], inline=True)
    embed.add_field(name="🌀 المهارة الفتاكة", value=hero_info['skills'], inline=True)
    embed.add_field(name="🪙 العملات العادية", value=f"{eco['coins']:,} عملة", inline=True)
    embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
    embed.add_field(name="⚒️ مستوى العتاد", value=f"{eco.get('gear_level', 1)} / 10,000", inline=True)
    embed.add_field(name="💳 الديون المعلقة", value=f"{eco.get('loan_debt', 0):,} عملة", inline=True)
    embed.add_field(name="🏰 أعلى طابق", value=f"الطابق {eco.get('max_floor', 1)}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
