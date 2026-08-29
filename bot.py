import os
import json
import random
import asyncio
import sqlite3
import datetime
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== إعداد قاعدة بيانات SQLite الدائمة ====================
DB_FILE = "/data/database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

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
        loan_debt INTEGER DEFAULT 0,
        savings INTEGER DEFAULT 0,
        last_daily TEXT DEFAULT ''
    )
''')
conn.commit()

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
    cursor.execute("SELECT coins, gems, inventory, gear_level, max_floor, loan_debt, savings, last_daily FROM economy WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if not row:
        default_inv = json.dumps(["سيف التدريب الخشبي", "درع الجلد الطبيعي"])
        cursor.execute("INSERT OR REPLACE INTO economy (user_id, coins, gems, inventory, gear_level, max_floor, loan_debt, savings, last_daily) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (str(user_id), 1000, 20, default_inv, 1, 1, 0, 0, ""))
        conn.commit()
        return {"coins": 1000, "gems": 20, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], "gear_level": 1, "max_floor": 1, "loan_debt": 0, "savings": 0, "last_daily": ""}
    return {
        "coins": row[0],
        "gems": row[1],
        "inventory": json.loads(row[2]),
        "gear_level": row[3],
        "max_floor": row[4],
        "loan_debt": row[5] if row[5] is not None else 0,
        "savings": row[6] if row[6] is not None else 0,
        "last_daily": row[7] if row[7] is not None else ""
    }

def update_economy(user_id, eco):
    cursor.execute("UPDATE economy SET coins = ?, gems = ?, inventory = ?, gear_level = ?, max_floor = ?, loan_debt = ?, savings = ?, last_daily = ? WHERE user_id = ?",
                   (eco["coins"], eco["gems"], json.dumps(eco["inventory"]), eco["gear_level"], eco["max_floor"], eco.get("loan_debt", 0), eco.get("savings", 0), eco.get("last_daily", ""), str(user_id)))
    conn.commit()

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
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

class HeroDropdown(discord.ui.Select):
    def __init__(self, options, name_val, age_val, gender):
        super().__init__(placeholder="اختر بطلك الأسطوري المفضّل...", options=options)
        self.name_val = name_val
        self.age_val = age_val
        self.gender = gender

    async def callback(self, interaction: discord.Interaction):
        chosen_hero = self.values[0]
        save_user_profile(interaction.user.id, self.name_val, self.age_val, self.gender, chosen_hero)
        get_user_economy(interaction.user.id)
        
        h_info = HEROES_DATA[chosen_hero]
        embed = discord.Embed(title="🎉 تم التسجيل واختيار البطل بنجاح!", description=f"أهلاً بك في عالم المغامرة يا **{self.name_val}**!", color=0x9B59B6)
        embed.add_field(name="🛡️ البطل المختار", value=f"**{chosen_hero}** ({h_info['title']})\n{h_info['art']}", inline=False)
        embed.add_field(name="⚡ القدرة", value=h_info['power'], inline=True)
        embed.add_field(name="🌀 المهارة", value=h_info['skills'], inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroSelectView(discord.ui.View):
    def __init__(self, gender: str, name_val: str, age_val: int):
        super().__init__(timeout=60)
        options = [discord.SelectOption(label=h_name, description=h_data["title"], emoji="⚔️") for h_name, h_data in HEROES_DATA.items() if h_data["gender"] == gender]
        self.add_item(HeroDropdown(options, name_val, age_val, gender))

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

# ==================== نظام البنك الفاخر ====================
class LoanModal(discord.ui.Modal, title="🏛️ خزنة القروض الإمبراطورية الفاخرة"):
    loan_amount_input = discord.ui.TextInput(label="مبلغ القرض المطلوب", placeholder="أدخل المبلغ (الحد الأقصى 50,000 عملة)...", max_length=6)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.loan_amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب إدخال رقم صحيح!", ephemeral=True)
            return

        if not (100 <= amount <= 50000):
            await interaction.response.send_message("❌ مبلغ القرض يجب أن يكون بين **100 و 50,000** عملة!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if eco.get("loan_debt", 0) > 0:
            await interaction.response.send_message(f"❌ لديك قرض ملكي سابق لم تقم بسداده بقيمة `{eco['loan_debt']:,}` عملة! يجب تسويته أولاً.", ephemeral=True)
            return

        eco["loan_debt"] = amount
        eco["coins"] += amount
        update_economy(user_id, eco)

        embed = discord.Embed(
            title="✨ تم اعتماد القرض الإمبراطوري الملكي بنجاح",
            description=f"لقد تم ضخ مبلغ **{amount:,} عملة** مباشرة إلى خزانتك الشخصية.\n\n"
                        f"⚠️ **تنبيه مصرفي فاخر:** في حال خوضك للمعارارك وصعود الطوابق وعليك دين معلق، سيقوم البنك الإمبراطوري بمصادرة وبيع عتادك لتسوية الدين بالكامل!",
            color=0xD4AF37
        )
        embed.add_field(name="🪙 الرصيد المضاف", value=f"+{amount:,} عملة", inline=True)
        embed.add_field(name="📜 الدين الملكي المترتب", value=f"{amount:,} عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DepositModal(discord.ui.Modal, title="💎 خزانة التوفير والاستثمار الحصري"):
    deposit_input = discord.ui.TextInput(label="المبلغ المراد إيداعه وتوفيره", placeholder="أدخل المبلغ المراد إيداعه...", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.deposit_input.value)
        except ValueError:
            await interaction.response.send_message("❌ الرجاء إدخال رقم صحيح!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ لا يمكنك إيداع قيمة سالبة أو صفرية!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if eco["coins"] < amount:
            await interaction.response.send_message(f"❌ رصيدك الحر لا يكفي! رصيدك الحالي: `{eco['coins']:,}` عملة.", ephemeral=True)
            return

        eco["coins"] -= amount
        eco["savings"] += amount
        update_economy(user_id, eco)

        embed = discord.Embed(
            title="🌟 عملية إيداع ناجحة في الخزنة الملكية",
            description=f"تم نقل مبلغ `{amount:,} عملة` بأمان تام إلى حساب التوفير الخاص بك مع عوائد استثمارية مضمونة.",
            color=0x2ECC71
        )
        embed.add_field(name="💰 رصيد التوفير الحالي", value=f"`{eco['savings']:,}` عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class WithdrawModal(discord.ui.Modal, title="🏧 سحب الأموال من الخزنة الخاصة"):
    withdraw_input = discord.ui.TextInput(label="المبلغ المراد سحبه", placeholder="أدخل المبلغ المراد سحبه...", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.withdraw_input.value)
        except ValueError:
            await interaction.response.send_message("❌ الرجاء إدخال رقم صحيح!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ لا يمكنك سحب قيمة سالبة أو صفرية!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if eco["savings"] < amount:
            echo_savings = eco["savings"]
            await interaction.response.send_message(f"❌ رصيد التوفير لديك لا يكفي! رصيد الخزنة الحالي: `{echo_savings:,}` عملة.", ephemeral=True)
            return

        eco["savings"] -= amount
        eco["coins"] += amount
        update_economy(user_id, eco)

        embed = discord.Embed(
            title="🏧 عملية سحب ناجحة",
            description=f"تم استرداد مبلغ `{amount:,} عملة` من الخزنة الخاصة وإضافتها لمحفظتك الحرة.",
            color=0x3498DB
        )
        embed.add_field(name="🪙 رصيدك الحر الجديد", value=f"`{eco['coins']:,}` عملة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LuxuryBankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="إيداع بالتوفير", style=discord.ButtonStyle.success, emoji="📥")
    async def deposit_savings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لاستخدام خدمات البنك الفاخرة!", ephemeral=True)
            return
        await interaction.response.send_modal(DepositModal())

    @discord.ui.button(label="سحب من التوفير", style=discord.ButtonStyle.secondary, emoji="📤")
    async def withdraw_savings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
            return
        await interaction.response.send_modal(WithdrawModal())

    @discord.ui.button(label="طلب قرض ملكي", style=discord.ButtonStyle.danger, emoji="🏛️")
    async def request_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get_user_profile(interaction.user.id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
            return
        await interaction.response.send_modal(LoanModal())

    @discord.ui.button(label="سداد الدين الكامل", style=discord.ButtonStyle.primary, emoji="💎")
    async def repay_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not get_user_profile(user_id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
            return

        eco = get_user_economy(user_id)
        debt = eco.get("loan_debt", 0)

        if debt <= 0:
            await interaction.response.send_message("✨ سجلك المالي نقي تماماً! ليس لديك أي ديون معلقة في البنك.", ephemeral=True)
            return

        if eco["coins"] < debt:
            await interaction.response.send_message(f"❌ رصيدك الحر لا يكفي لسداد القرض الملكي! الدين المطلوب: `{debt:,}` عملة | رصيدك الحر: `{eco['coins']:,}` عملة.", ephemeral=True)
            return

        eco["coins"] -= debt
        eco["loan_debt"] = 0
        update_economy(user_id, eco)

        embed = discord.Embed(
            title="👑 تمت تسوية وسداد الدين بنجاح تام",
            description=f"لقد قمت بسداد كامل القرض الملكي بقيمة `{debt:,} عملة`. تم رفع الحراسة عن عتادك وأصبحت من كبار الشخصيات الموثوقة!",
            color=0xD4AF37
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="المنحة الملكية اليومية", style=discord.ButtonStyle.success, emoji="🎁")
    async def daily_stipend(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if not get_user_profile(user_id):
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً للحصول على المنحة الملكية!", ephemeral=True)
            return

        eco = get_user_economy(user_id)
        today_str = datetime.date.today().isoformat()

        if eco.get("last_daily") == today_str:
            await interaction.response.send_message("⏳ لقد استلمت منحتك الملكية اليومية بالفعل! عُد غداً في منتصف الليل لتلقي المزيد من العطايا.", ephemeral=True)
            return

        bonus_coins = 2500
        bonus_gems = 10
        eco["coins"] += bonus_coins
        eco["gems"] += bonus_gems
        eco["last_daily"] = today_str
        update_economy(user_id, eco)

        embed = discord.Embed(
            title="🎁 صُرفت المنحة الإمبراطورية اليومية بنجاح",
            description="بصفتك مواطناً من طبقة النبلاء، تفضل البنك المركزي بمنحك هديتك الملكية اليومية!",
            color=0xF1C40F
        )
        embed.add_field(name="🪙 عملات مضافة", value=f"+{bonus_coins:,} عملة", inline=True)
        embed.add_field(name="💎 جواهر الظلام", value=f"+{bonus_gems} جوهرة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="البنك", description="فتح واجهة المصرف الإمبراطوري الفاخر (توفير، قروض، منحة يومية واستثمار)")
async def bank(interaction: discord.Interaction):
    user_id = interaction.user.id
    eco = get_user_economy(user_id)
    
    embed = discord.Embed(
        title="🌟 ⟪ المـَصـْرِف الإمـْبـرَاطـُوري الـْمـَلَكـِي الـْفـَاخـِر ⟫ 🌟",
        description="مرحباً بك في أحدث وأفخم مؤسسة مالية في عوالم المغامرة. استمتع بخدمات التوفير الاستثمارية، خزائن القروض الملكية، والعطايا اليومية الحصرية.",
        color=0xD4AF37
    )
    embed.add_field(name="🪙 الرصيد الحر في المحفظة", value=f"`{eco['coins']:,}` عملة", inline=True)
    embed.add_field(name="💰 خزنة التوفير والاستثمار", value=f"`{eco.get('savings', 0):,}` عملة", inline=True)
    embed.add_field(name="🏛️ القروض والدين المعلق", value=f"`{eco.get('loan_debt', 0):,}` عملة", inline=True)
    embed.add_field(name="💎 رصيد الجواهر الخاصة", value=f"`{eco['gems']}` جوهرة", inline=True)
    embed.set_footer(text="✨ المصرف الإمبراطوري — الأمان المطلق والرفاهية الماليّة لجميع المغامرس.")
    
    await interaction.response.send_message(embed=embed, view=LuxuryBankView(), ephemeral=False)

# ==================== نظام التحويل ====================
@bot.tree.command(name="تحويل", description="تحويل عملات مباشرة لمستخدم آخر عبر المنشن أو اختيار العضو بكل سلاسة")
@app_commands.describe(member="الشخص المراد التحويل إليه (منشن)", amount="المبلغ المراد تحويله")
async def transfer_slash(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = interaction.user.id
    target_id = member.id

    if not get_user_profile(sender_id):
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لتتمكن من إجراء التحويلات!", ephemeral=True)
        return

    if not get_user_profile(target_id):
        await interaction.response.send_message(f"❌ المستخدم {member.mention} غير مسجل في السجلات الإمبراطورية بعد!", ephemeral=True)
        return

    if sender_id == target_id:
        await interaction.response.send_message("❌ لا يمكنك تحويل العملات إلى نفس الشخصية الخاصة بك!", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ يجب أن يكون المبلغ المراد تحويله أكبر من صفر!", ephemeral=True)
        return

    sender_eco = get_user_economy(sender_id)
    if sender_eco["coins"] < amount:
        await interaction.response.send_message(f"❌ رصيدك الحر الحالي لا يكفي! لديك `{sender_eco['coins']:,}` عملة فقط في المحفظة.", ephemeral=True)
        return

    target_eco = get_user_economy(target_id)

    sender_eco["coins"] -= amount
    target_eco["coins"] += amount

    update_economy(sender_id, sender_eco)
    update_economy(target_id, target_eco)

    embed = discord.Embed(
        title="💸 تمت عملية التحويل المالي الملكي بنجاح",
        description=f"قمت بتحويل مبلغ وقدره `{amount:,} عملة` بكل أمان وفخامة إلى {member.mention}!",
        color=0xD4AF37
    )
    embed.add_field(name="👤 المستلم", value=member.mention, inline=True)
    embed.add_field(name="🪙 المبلغ المرسل", value=f"`{amount:,}` عملة", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=False)

# ==================== نظام الطوابق والمعارك ====================
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

        if eco.get("loan_debt", 0) > 0:
            debt = eco["loan_debt"]
            eco["gear_level"] = 1
            eco["inventory"] = ["سيف التدريب الخشبي (تم بيعه لتسوية الدين الملكي)", "درع الجلد الطبيعي"]
            eco["loan_debt"] = 0
            update_economy(user_id, eco)

            punish_embed = discord.Embed(
                title="🚨 تنبيه مصرفي إمبراطوري صارم: مصادرة وبيع العتاد!",
                description=f"لقد حاولت خوض المعركة وعليك قرض ملكي متأخر بقيمة `{debt:,}` عملة ولم تقم بسداده في الموعد!\n\n"
                            f"⚖️ **العقوبة المنفذة:** تدخلت هيئة الرقابة المالية للبنك وقامت بمصادرة وبيع عتادك بالكامل لتسوية الدين. تم إعادة عتادك للمستوى الأساسي `1`.",
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
            f"⚔️ **جارٍ فتح بوابة الطابق الصعب `{target_floor}` ({difficulty})...**\n"
            f"الخصم الواقف في الميدان: **{monster_name}**\n"
            f"استعد لتلاحم الضربات الحماسية!", 
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

            battle_embed = discord.Embed(title=f"🔥 معركة شرسة في الطابق {target_floor} (الجولة {round_num}/4)", description=f"المواجهة مشتعلة بين البطل والوحش **{monster_name}**!", color=0x992D22)
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

            win_embed = discord.Embed(title=f"👑 انتصار أسطوري ساحق في الطابق {target_floor}!", description=f"لقد تمكنت من سحق الوحش **{monster_name}** وإخضاع الطابق بجدارة!", color=0x2ECC71)
            win_embed.add_field(name="🪙 العملات المكتسبة", value=f"+{coins_reward:,} عملة", inline=True)
            win_embed.add_field(name="💎 جواهر الظلام", value=f"+{gems_reward} جوهرة", inline=True)
            win_embed.add_field(name="🏆 أعلى طابق", value=f"الطابق {eco['max_floor']}", inline=False)
            await msg.edit(embed=win_embed, view=None)
        else:
            lost_coins = min(eco["coins"], 100 * (target_floor // 10 + 1))
            eco["coins"] = max(0, eco["coins"] - lost_coins)
            update_economy(user_id, eco)

            lose_embed = discord.Embed(title=f"💀 هزيمة قاسية في الطابق {target_floor}!", description=f"تفوق عليك الوحش المرعب **{monster_name}**!", color=0xE74C3C)
            lose_embed.add_field(name="⚠️ الخسائر", value=f"فقدت `{lost_coins:,}` عملة أثناء الانسحاب!", inline=False)
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
            await interaction.response.send_message(f"❌ رصيدك الحر لا يكفي! تحتاج إلى `{cost:,}` عملة عادية.", ephemeral=True)
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
        embed = discord.Embed(title="🏰 لوحة حالة برج المغامرات والعتاد", description="ملخص بيانات المغامر:", color=0x3498DB)
        embed.add_field(name="⚡ مستوى العتاد الحالي", value=f"**{eco.get('gear_level', 1)} / 10,000**", inline=True)
        embed.add_field(name="🏆 أعلى طابق", value=f"الطابق **{eco.get('max_floor', 1)}**", inline=True)
        embed.add_field(name="🪙 الرصيد الحر", value=f"{eco['coins']:,} عملة", inline=True)
        embed.add_field(name="💰 خزنة التوفير", value=f"{eco.get('savings', 0):,} عملة", inline=True)
        embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
        embed.add_field(name="🏛️ الدين المعلق", value=f"{eco.get('loan_debt', 0):,} عملة", inline=True)
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
        await interaction.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    
    eco = get_user_economy(user_id)
    hero_name = user_data.get("hero", "غير محدد")
    hero_info = HEROES_DATA.get(hero_name, {"title": "بلا لقب", "story": "لا توجد قصة", "power": "عادي", "skills": "لا توجد", "art": "[ شخصية عادية 🛡️ ]"})
    
    embed = discord.Embed(title=f"👑 الملف الشخصي الأسطوري | {user_data['name']}", description=f"**اللقب الأسطوري:** {hero_info['title']}\n📖 *{hero_info['story']}*", color=0xE67E22)
    embed.add_field(name="⚔️ البطل المختار والشكل المرئي", value=f"**{hero_name}**\n{hero_info['art']}", inline=False)
    embed.add_field(name="⚡ القدرة الخاصة", value=hero_info['power'], inline=True)
    embed.add_field(name="🌀 المهارة الفتاكة", value=hero_info['skills'], inline=True)
    embed.add_field(name="🪙 الرصيد الحر", value=f"{eco['coins']:,} عملة", inline=True)
    embed.add_field(name="💰 خزنة التوفير", value=f"{eco.get('savings', 0):,} عملة", inline=True)
    embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
    embed.add_field(name="⚒️ مستوى العتاد", value=f"{eco.get('gear_level', 1)} / 10,000", inline=True)
    embed.add_field(name="🏛️ القروض المعلقة", value=f"{eco.get('loan_debt', 0):,} عملة", inline=True)
    embed.add_field(name="🏰 أعلى طابق", value=f"الطابق {eco.get('max_floor', 1)}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
