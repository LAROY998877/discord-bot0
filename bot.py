import os
import json
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ملف حفظ البيانات محلياً
DB_FILE = "database.json"

# قواعد البيانات
REGISTERED_USERS = {}
USER_ECONOMY = {}          # {user_id: {"coins": int, "gems": int, "inventory": [], "hero": str, "max_floor": int}}
GUILDS_DATA = {}           # {guild_name: {"owner": id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [id]}}

def load_data():
    global REGISTERED_USERS, USER_ECONOMY, GUILDS_DATA
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                REGISTERED_USERS = {int(k): v for k, v in data.get("REGISTERED_USERS", {}).items()}
                USER_ECONOMY = {int(k): v for k, v in data.get("USER_ECONOMY", {}).items()}
                GUILDS_DATA = data.get("GUILDS_DATA", {})
            print("💾 تم تحميل البيانات بنجاح من قاعدة البيانات!")
        except Exception as e:
            print(f"❌ خطأ أثناء تحميل البيانات: {e}")

def save_data():
    data = {
        "REGISTERED_USERS": {str(k): v for k, v in REGISTERED_USERS.items()},
        "USER_ECONOMY": {str(k): v for k, v in USER_ECONOMY.items()},
        "GUILDS_DATA": GUILDS_DATA
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ البيانات: {e}")

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 1000, "gems": 20, "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], "hero": None, "max_floor": 1}
        save_data()
    return USER_ECONOMY[user_id]

# تعريف الأبطال (3 ذكور + 6 إناث + بطل السفاح السري)
HEROES_DATA = {
    # الأبطال الذكور (3)
    "ثورن": {"gender": "ذكر", "title": "عملاق الجبال", "story": "محارب شجاع درعه مصنوع من حجر النيزك.", "power": "صلابة حديدية", "skills": "ضربة الأرض", "art": "[ ثورن 🏔️ ]"},
    "كايدن": {"gender": "ذكر", "title": "سياف اللهيب", "story": "أقسم على الانتقام بسيفه المشتعل بنيران التنين.", "power": "إشعال النيران", "skills": "سيف اللهيب", "art": "[ كايدن 🔥 ]"},
    "زيك": {"gender": "ذكر", "title": "مهندس الموت", "story": "استخدم التكنولوجيا المحرمة لدمج التروس بجسده.", "power": "التحكم التقني", "skills": "مدفع البلازما", "art": "[ زيك ⚙️ ]"},
    
    # الأبطال الإناث (6)
    "لونا": {"gender": "أنثى", "title": "حارسة النجوم", "story": "وُدت تحت ضوء نيزك أزرق نادر لإنقاذ عالمها.", "power": "الضوء القمري", "skills": "انفجار نيزكي", "art": "[ لونا 🌙 ]"},
    "فيكتوريا": {"gender": "أنثى", "title": "فارس العاصفة", "story": "امتزجت روحها بالبرق لتصبح عاصفة بشرية.", "power": "الكهرباء والسرعة", "skills": "صاعقة البرق", "art": "[ فيكتوريا ⚡ ]"},
    "سراب": {"gender": "أنثى", "title": "سيدة الظلال", "story": "تعلقت بفنون التخفي حتى أصبحت شبحاً لا يرى.", "power": "الانتقال الآني", "skills": "طعنة الظل", "art": "[ سراب 👥 ]"},
    "أوريرا": {"gender": "أنثى", "title": "أميرة الفجر", "story": "ابنة الشمس الأولى التي تستمد قوتها من خيوط الفجر الأولى.", "power": "شعاع الشمس الأبدي", "skills": "تطهير النور المقدس", "art": "[ أوريرا ☀️ ]"},
    "ساكورا": {"gender": "أنثى", "title": "زهرة الساموراي", "story": "مقاتلة شرسة تدمج رقة بتلات الكرز بحد السيف القاتل.", "power": "رياح البتلات القاتلة", "skills": "رقصة الكرز القاتلة", "art": "[ ساكورا 🌸 ]"},
    "ميرال": {"gender": "أنثى", "title": "ساحرة الزمن", "story": "تتحكم في نسيج الزمن لتلعب بأعصاب أعدائها في المعارك.", "power": "إبطاء وتجميد الزمن", "skills": "شق الأبعاد والزمن", "art": "[ ميرال ⏳ ]"},
    
    # بطل المطور السري
    "السفاح": {"gender": "سري", "title": "حاصد الأرواح السري", "story": "كائن أسطوري مرعب مخصص للمطور حصرياً بقوة مطلقة.", "power": "إفناء الوجود المطلق", "skills": "لمسة الموت والدمار", "art": "[ 💀 السفاح المرعب 💀 ]"}
}

# معدات متجر الظلام (تُشترى بجواهر الظلام 💎)
DARK_SHOP_ITEMS = {
    "خنجر الشيطان الأبدي": {"price_gems": 10, "rank": "🔴 الشيطان", "power": "قوة تدميرية +999"},
    "سيف الموت الشيطاني": {"price_gems": 18, "rank": "🔴 الشيطان", "power": "قوة تدميرية +1300"},
    "خوذة خطايا الشيطان": {"price_gems": 12, "rank": "🔴 الشيطان", "power": "دفاع شيطاني +1100"},
    "جناح الشيطان المظلم": {"price_gems": 25, "rank": "🔴 الشيطان", "power": "طيران وسرعة +1600"},
    "درع لهيب الجحيم": {"price_gems": 30, "rank": "🔥 الجحيم", "power": "دفاع مطلق +1800"},
    "فأس الحمم البركانية": {"price_gems": 35, "rank": "🔥 الجحيم", "power": "قوة نارية +2100"},
    "حذاء السير في الحمم": {"price_gems": 22, "rank": "🔥 الجحيم", "power": "سرعة فائقة +1500"},
    "خاتم جمر الجحيم": {"price_gems": 28, "rank": "🔥 الجحيم", "power": "حرق الخصوم +1900"},
    "عباءة السفاح الدموية": {"price_gems": 50, "rank": "⚔️ السفاح", "power": "سرعة وتخفي خارق +3000"},
    "منجل حاصد الأرواح": {"price_gems": 75, "rank": "⚔️ السفاح", "power": "قتل فوري وإبادة +5000"},
    "قناع الظل الأعمى": {"price_gems": 45, "rank": "⚔️ السفاح", "power": "تفادي مطلق +3500"},
    "قفازات الإبادة الشاملة": {"price_gems": 60, "rank": "⚔️ السفاح", "power": "تحطيم الدروع +4200"},
    "شفرات الموت المطلق": {"price_gems": 90, "rank": "⚔️ السفاح", "power": "دمار شامل +6000"}
}

# معدات المتجر العادي (تُشترى بالعملات العادية 🪙)
NORMAL_SHOP_ITEMS = {
    "سيف حديدي حاد": {"price": 200, "power": "هجوم +150"},
    "درع الفولاذ المقاوم": {"price": 350, "power": "دفاع +200"},
    "قوس الصيد السريع": {"price": 300, "power": "هجوم عن بعد +180"},
    "جرعة شفاء كبرى": {"price": 100, "power": "استعادة صحة كاملة"},
    "رمح الحراس الملكي": {"price": 450, "power": "هجوم +250"},
    "خوذة الفارس الحديدية": {"price": 250, "power": "دفاع +180"},
    "حذاء السرعة الخفيف": {"price": 150, "power": "سرعة +100"},
    "عصا السحر المبتدئ": {"price": 400, "power": "سحر +220"},
    "درع التاريس الخشبي": {"price": 120, "power": "دفاع +90"},
    "سيف النسر الذهبي": {"price": 800, "power": "هجوم +500"},
    "درع التنين العتيق": {"price": 950, "power": "دفاع +600"},
    "خنجر اللصوص السريع": {"price": 280, "power": "هجوم مباغت +190"}
}

@bot.event
async def on_ready():
    load_data()
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
        super().__init__(placeholder="اختر بطلك الأسطوري المفضّل...", options=options)
        self.name_val, self.age_val, self.gender = name_val, age_val, gender

    async def callback(self, interaction: discord.Interaction):
        chosen_hero = self.values[0]
        REGISTERED_USERS[interaction.user.id] = {"name": self.name_val, "age": self.age_val, "gender": self.gender, "hero": chosen_hero}
        get_user_economy(interaction.user.id)["hero"] = chosen_hero
        save_data()
        
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
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل مسبقاً بالفعل!", ephemeral=True)
        return
    await interaction.response.send_message("🎮 مرحباً بك! يرجى اختيار جنس الشخصية للبدء:", view=GenderSelectView(), ephemeral=True)


# ==================== 2. لوحة المطور (مع بطل السفاح السري) ====================
class DevDashboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الحصول على بطل السفاح الأسطوري السري", description="فتح واستخدام بطل 'السفاح' الخارق للمطور", emoji="💀"),
            discord.SelectOption(label="الحصول على عملات عادية لا نهائية", description="إضافة 999,999 عملة عادية", emoji="🪙"),
            discord.SelectOption(label="الحصول على جواهر ظلام لا نهائية", description="إضافة 9,999 جوهرة نادرة", emoji="💎"),
            discord.SelectOption(label="الحصول على عتاد سري", description="إضافة معدات نادرة لحقيبتك", emoji="⚔️"),
            discord.SelectOption(label="عرض إحصائيات النظام", description="معرفة عدد اللاعبين والنقابات", emoji="📊")
        ]
        super().__init__(placeholder="اختر أمراً من لوحة تحكم المطور...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if self.values[0] == "الحصول على بطل السفاح الأسطوري السري":
            if user_id not in REGISTERED_USERS:
                REGISTERED_USERS[user_id] = {"name": interaction.user.display_name, "age": 25, "gender": "سري", "hero": "السفاح"}
            else:
                REGISTERED_USERS[user_id]["hero"] = "السفاح"
            eco["hero"] = "السفاح"
            save_data()
            await interaction.response.send_message("💀 تم تفعيل بطل «السفاح» الأسطوري السري لحسابك بنجاح بقوة مطلقة!", ephemeral=True)

        elif self.values[0] == "الحصول على عملات عادية لا نهائية":
            eco["coins"] += 999999
            save_data()
            await interaction.response.send_message("🪙 تم إضافة 999,999 عملة عادية بنجاح إلى رصيدك!", ephemeral=True)

        elif self.values[0] == "الحصول على جواهر ظلام لا نهائية":
            eco["gems"] += 9999
            save_data()
            await interaction.response.send_message("💎 تم إضافة 9,999 جوهرة ظلام نادرة بنجاح إلى رصيدك!", ephemeral=True)

        elif self.values[0] == "الحصول على عتاد سري":
            eco["inventory"].extend(["سيف المطور الأسطوري", "درع الإله المطلق"])
            save_data()
            await interaction.response.send_message("⚔️ تم إضافة عتاد سري وخارق إلى حقيبتك!", ephemeral=True)

        elif self.values[0] == "عرض إحصائيات النظام":
            await interaction.response.send_message(f"📊 اللاعبين المسجلين: {len(REGISTERED_USERS)} | النقابات المسجلة: {len(GUILDS_DATA)}", ephemeral=True)

class DevDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevDashboardSelect())

@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الخاصة بالمطور بنظام المنيو")
async def dev_dashboard(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر خاص بالمطور فقط!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🛠️ لوحة تحكم المطور المركزية", description="اختر من القائمة أدناه ما تحتاجه لتطوير اللعبة وإدارتها:", color=0xE74C3C)
    await interaction.response.send_message(embed=embed, view=DevDashboardView(), ephemeral=True)


# ==================== 3. نظام الطوابق والمعارك (الجديد) ====================
@bot.tree.command(name="الطابق", description="خوض معركة في الطوابق لقتال الوحوش وجمع العملات والجواهر النادرة")
@app_commands.describe(رقم_الطابق="رقم الطابق الذي ترغب في دخوله (من 1 إلى 1000)")
async def tower_floor(interaction: discord.Interaction, رقم_الطابق: int):
    user_id = interaction.user.id
    if user_id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لكي تتمكن من صعود الطوابق!", ephemeral=True)
        return
    
    if not (1 <= رقم_الطابق <= 1000):
        await interaction.response.send_message("❌ رقم الطابق يجب أن يكون بين **1 و 1000** حصرياً!", ephemeral=True)
        return

    eco = get_user_economy(user_id)
    
    # تحديد الصعوبة ونوع الوحوش والجوائز حسب الطابق
    if 1 <= رقم_الطابق <= 15:
        difficulty = "🟢 سهل"
        monsters = ["زومبي مبتدئ", "هيكل عظمي تايه", "عنكبوت الكهف الصغير"]
        coins_reward = رقم_الطابق * 60
        gems_reward = random.choice([0, 1])
        win_chance = 0.90  # نسبة الفوز عالية جداً للطوابق السهلة
    elif 16 <= رقم_الطابق <= 30:
        difficulty = "🟡 متوسط"
        monsters = ["محارب منبوذ", "وحش المستنقع السام", "ذئب الظلام الشرس"]
        coins_reward = رقم_الطابق * 180
        gems_reward = random.choice([1, 2, 3])
        win_chance = 0.75
    elif 31 <= رقم_الطابق <= 70:
        difficulty = "🟠 صعب"
        monsters = ["شيطان الحمم البركانية", "عملاق الحجارة الضخم", "فارس الظلام المرعب"]
        coins_reward = رقم_الطابق * 450
        gems_reward = random.randint(3, 8)
        win_chance = 0.55
    else:  # 70 إلى 1000
        difficulty = "🔴 مستحيل / أسطوري"
        monsters = ["تنين الأبعاد الأبدي", "حاصد الأرواح الملكي", "ملك الشياطين المطلق"]
        coins_reward = رقم_الطابق * 1200
        gems_reward = random.randint(10, 30)
        win_chance = 0.30  # صعب جداً ويحتاج عتاد قوي أو بطل السفاح

    monster_name = random.choice(monsters)
    
    # تعديل نسبة الفوز بناءً على امتلاك معدات قوية أو بطل السفاح
    if eco["hero"] == "السفاح" or any("السفاح" in item or "المطور" in item or "الشيطان" in item for item in eco["inventory"]):
        win_chance = min(1.0, win_chance + 0.35)  # تعزيز كبير لمن يمتلك عتاداً قوياً أو البطل السري

    # محاكاة نتيجة المعركة
    is_victory = random.random() < win_chance

    if is_victory:
        eco["coins"] += coins_reward
        eco["gems"] += gems_reward
        if رقم_الطابق > eco.get("max_floor", 1):
            eco["max_floor"] = رقم_الطابق
        save_data()

        embed = discord.Embed(
            title=f"⚔️ انتصار ساحق في الطابق {رقم_الطابق}!",
            description=f"لقد واجهت الوحش **{monster_name}** في قسم المستوى ({difficulty}) وتمكنت من سحقه بنجاح!",
            color=0x2ECC71
        )
        embed.add_field(name="🪙 الغنائم من العملات العادية", value=f"+{coins_reward:,} عملة", inline=True)
        embed.add_field(name="💎 الغنائم من جواهر الظلام", value=f"+{gems_reward} جوهرة نادرة", inline=True)
        embed.add_field(name="🏆 أعلى طابق تم بلوغه", value=f"الطابق {eco['max_floor']}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        # عقوبة خفيفة عند الخسارة
        lost_coins = min(eco["coins"], 50 * (رقم_الطابق // 10 + 1))
        eco["coins"] = max(0, eco["coins"] - lost_coins)
        save_data()

        embed = discord.Embed(
            title=f"💀 هزيمة قاسية في الطابق {رقم_الطابق}!",
            description=f"كان الوحش **{monster_name}** ({difficulty}) أقوى من متوقعك وهزمك في المعركة!",
            color=0xE74C3C
        )
        embed.add_field(name="⚠️ الخسارة", value=f"فقدت `{lost_coins}` عملة عادية أثناء الهروب لإنقاذ حياتك!", inline=False)
        embed.add_field(name="💡 نصيحة", value="طور عتادك من المتجر أو اشترِ معدات متجر الظلام لزيادة فرص فوزك في الطوابق العليا!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)


# ==================== 4. نظام الحقيبة التفاعلي (منيو الحقيبة) ====================
class InventorySelect(discord.ui.Select):
    def __init__(self, inventory):
        if not inventory:
            options = [discord.SelectOption(label="الحقيبة فارغة", description="لا تملك أي عناصر حالياً")]
        else:
            options = [discord.SelectOption(label=item, description="قطعة حربية أو أداة في حقيبتك", emoji="🎒") for item in inventory[:25]]
        super().__init__(placeholder="اختر قطعة من حقيبتك لعرض تفاصيلها...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "الحقيبة فارغة":
            await interaction.response.send_message("❌ حقيبتك فارغة تماماً!", ephemeral=True)
            return
        item_name = self.values[0]
        await interaction.response.send_message(f"🎒 معلومات القطعة **{item_name}**: هذه قطعة أسطورية فريدة تزيد من قدرات بطلك وتمنحك أفضلية خارقة في قتال الطوابق والوحوش!", ephemeral=True)

class InventoryView(discord.ui.View):
    def __init__(self, inventory):
        super().__init__(timeout=60)
        self.add_item(InventorySelect(inventory))

@bot.tree.command(name="الحقيبة", description="فتح قائمة الحقيبة التفاعلية (المنيو)")
async def inventory_menu(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    eco = get_user_economy(user_id)
    embed = discord.Embed(title=f"🎒 حقيبة المغامر | {interaction.user.display_name}", description="اختر من القائمة أدناه لعرض تفاصيل أي قطعة تمتلكها:", color=0x3498DB)
    embed.add_field(name="📋 محتويات الحقيبة", value=", ".join(eco["inventory"]) if eco["inventory"] else "فارغة تماماً", inline=False)
    await interaction.response.send_message(embed=embed, view=InventoryView(eco["inventory"]), ephemeral=True)


# ==================== 5. المتجر العادي ومتجر الظلام ====================
class NormalShopSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, description=f"السعر: {data['price']} عملة | {data['power']}", emoji="🛒") for name, data in NORMAL_SHOP_ITEMS.items()]
        super().__init__(placeholder="اختر غرضاً لشرائه من المتجر العادي...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
            return

        item_name = self.values[0]
        item_data = NORMAL_SHOP_ITEMS[item_name]
        eco = get_user_economy(user_id)

        if eco["coins"] < item_data["price"]:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي! تحتاج إلى {item_data['price']} عملة عادية.", ephemeral=True)
            return

        eco["coins"] -= item_data["price"]
        eco["inventory"].append(item_name)
        save_data()
        await interaction.response.send_message(f"🛍️ تم شراء `{item_name}` بنجاح وإضافته إلى حقيبتك وحفظه!", ephemeral=True)

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(NormalShopSelect())

@bot.tree.command(name="المتجر", description="فتح المتجر العادي لشراء الأسلحة والدروع بالعملات العادية")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمغامرين", description="معدات وأسلحة متنوعة (تُشترى بالعملات العادية 🪙):", color=0xF1C40F)
    for name, data in NORMAL_SHOP_ITEMS.items():
        embed.add_field(name=name, value=f"السعر: {data['price']} عملة\n{data['power']}", inline=True)
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

class DarkShopSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=item_name, description=f"السعر: {data['price_gems']} جوهرة 💎 | {data['rank']}", emoji="🔥") for item_name, data in DARK_SHOP_ITEMS.items()]
        super().__init__(placeholder="اختر قطعة مظلمة أسطورية لشرائها...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
            return

        item_name = self.values[0]
        item_data = DARK_SHOP_ITEMS[item_name]
        eco = get_user_economy(user_id)

        if eco["gems"] < item_data["price_gems"]:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي من جواهر الظلام! تحتاج إلى {item_data['price_gems']} جوهرة 💎.", ephemeral=True)
            return

        eco["gems"] -= item_data["price_gems"]
        eco["inventory"].append(item_name)
        save_data()
        await interaction.response.send_message(f"🌑 تم شراء `{item_name}` برتبة **{item_data['rank']}** وحفظه في حقيبتك بنجاح!", ephemeral=True)

class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DarkShopSelect())

@bot.tree.command(name="متجر_الظلام", description="فتح متجر الظلام للمعدات الشيطانية والأسطورية بالعملة النادرة")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🌑 متجر الظلام الأسطوري", description="معدات الرتب العليـا (الشيطان - الجحيم - السفاح) تُشترى بجواهر الظلام النادرة 💎:", color=0x111111)
    for name, data in DARK_SHOP_ITEMS.items():
        embed.add_field(name=f"{data['rank']} | {name}", value=f"السعر: {data['price_gems']} جوهرة 💎\nقوة: {data['power']}", inline=False)
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)


# ==================== 6. تغيير البطل، النقابات، والملف الشخصي ====================
class ChangeHeroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        options = [discord.SelectOption(label=h_name, description=h_data["title"]) for h_name, h_data in HEROES_DATA.items() if h_name != "السفاح"]
        self.add_item(ChangeHeroDropdown(options))

class ChangeHeroDropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="اختر بطلك الجديد...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        eco = get_user_economy(user_id)
        if eco["coins"] < 200:
            await interaction.response.send_message(f"❌ تحتاج 200 عملة عادية لتغيير البطل! رصيدك: {eco['coins']}", ephemeral=True)
            return
        new_hero = self.values[0]
        eco["coins"] -= 200
        REGISTERED_USERS[user_id]["hero"] = new_hero
        eco["hero"] = new_hero
        save_data()
        await interaction.response.send_message(f"🔄 تم تغيير البطل إلى **{new_hero}** بنجاح وحفظه!", ephemeral=True)

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
        await interaction.response.send_message("❌ رصيدك لا يكفي (تحتاج 299 عملة عادية)!", ephemeral=True)
        return
    eco["coins"] -= 299
    GUILDS_DATA[اسم_النقابة] = {"owner": interaction.user.id, "level": 1, "exp": 0, "bank_coins": 0, "bank_items": [], "members": [interaction.user.id]}
    save_data()
    await interaction.response.send_message(f"🏰 تم تأسيس نقابة **{اسم_النقابة}** وحفظها بنجاح!", ephemeral=False)

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
            await interaction.response.send_message("❌ رصيدك لا يكفي من العملات العادية!", ephemeral=True)
            return
        eco["coins"] -= amount
        guild_info["bank_coins"] += amount
        guild_info["level"] = min(500, guild_info["level"] + (amount // 1000))
        save_data()
        await interaction.response.send_message(f"✅ تم تبرع {amount} عملة للنقابة وحفظ التغييرات بنجاح!", ephemeral=False)
    elif نوع_التبرع.value == "item":
        if القيمة_أو_الاسم not in eco["inventory"]:
            await interaction.response.send_message("❌ العنصر غير موجود بحقيبتك!", ephemeral=True)
            return
        eco["inventory"].remove(القيمة_أو_الاسم)
        guild_info["bank_items"].append(القيمة_أو_الاسم)
        save_data()
        await interaction.response.send_message(f"✅ تم تبرع القطعة للنقابة وحفظها بنجاح!", ephemeral=False)

@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وبطلك الأسطوري مع الشكل والتفاصيل المرئية")
async def profile(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ تسجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    
    user_data = REGISTERED_USERS[user_id]
    eco = get_user_economy(user_id)
    hero_name = user_data.get("hero", "غير محدد")
    hero_info = HEROES_DATA.get(hero_name, {"title": "بلا لقب", "story": "لا توجد قصة", "power": "عادي", "skills": "لا توجد", "art": "[ شخصية عادية 🛡️ ]"})
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي الأسطوري | {user_data['name']}",
        description=f"**اللقب الأسطوري:** {hero_info['title']}\n📖 *{hero_info['story']}*",
        color=0xE67E22
    )
    embed.add_field(name="⚔️ البطل المختار والشكل المرئي", value=f"**{hero_name}**\n{hero_info['art']}", inline=False)
    embed.add_field(name="⚡ القدرة الخاصة", value=hero_info['power'], inline=True)
    embed.add_field(name="🌀 المهارة الفتاكة", value=hero_info['skills'], inline=True)
    embed.add_field(name="🪙 العملات العادية", value=f"{eco['coins']} عملة", inline=True)
    embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
    embed.add_field(name="🏰 أعلى طابق تم بلوغه", value=f"الطابق {eco.get('max_floor', 1)}", inline=True)
    embed.add_field(name="🎒 عناصر الحقيبة", value=f"{len(eco['inventory'])} عناصر", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
