import os
import json
import random
import asyncio
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
USER_ECONOMY = {}          # {user_id: {"coins": int, "gems": int, "inventory": [], "hero": str, "max_floor": int, "gear_level": int}}
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
        USER_ECONOMY[user_id] = {
            "coins": 1000, 
            "gems": 20, 
            "inventory": ["سيف التدريب الخشبي", "درع الجلد الطبيعي"], 
            "hero": None, 
            "max_floor": 1,
            "gear_level": 1
        }
        save_data()
    if "gear_level" not in USER_ECONOMY[user_id]:
        USER_ECONOMY[user_id]["gear_level"] = 1
    return USER_ECONOMY[user_id]

# تعريف الأبطال (3 ذكور + 6 إناث + بطل السفاح السري)
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


# ==================== 2. لوحة المطور الفخمة جداً ====================
class DevDashboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="فتح بطل السفاح الأسطوري السري", description="امنح نفسك قوة السفاح المطلقة", emoji="💀"),
            discord.SelectOption(label="حقن عملات عادية لا نهائية", description="إضافة 999,999 عملة عادية لرصيدك", emoji="🪙"),
            discord.SelectOption(label="حقن جواهر الظلام النادرة", description="إضافة 9,999 جوهرة نادرة", emoji="💎"),
            discord.SelectOption(label="ترقية العتاد للحد الأقصى (10000)", description="رفع مستوى عتادك إلى القمة الفورية", emoji="⚡"),
            discord.SelectOption(label="إحصائيات النظام السيادية", description="عرض بيانات الخادم واللاعبين والمستخدمين", emoji="👑")
        ]
        super().__init__(placeholder="✦ اختر أمراً سيادياً من قمة لوحة المطور...", options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        eco = get_user_economy(user_id)

        if self.values[0] == "فتح بطل السفاح الأسطوري السري":
            if user_id not in REGISTERED_USERS:
                REGISTERED_USERS[user_id] = {"name": interaction.user.display_name, "age": 25, "gender": "سري", "hero": "السفاح"}
            else:
                REGISTERED_USERS[user_id]["hero"] = "السفاح"
            eco["hero"] = "السفاح"
            save_data()
            await interaction.response.send_message("💀 **[سيادة المطور]**: تم حقن بطل «السفاح» الأسطوري السري في ملفاتك الشخصية بقوة إفناء مطلقة!", ephemeral=True)

        elif self.values[0] == "حقن عملات عادية لا نهائية":
            eco["coins"] += 999999
            save_data()
            await interaction.response.send_message("🪙 **[سيادة المطور]**: تم ضخ 999,999 عملة عادية بنجاح إلى خزنتك السيادية!", ephemeral=True)

        elif self.values[0] == "حقن جواهر الظلام النادرة":
            eco["gems"] += 9999
            save_data()
            await interaction.response.send_message("💎 **[سيادة المطور]**: تم إضافة 9,999 جوهرة ظلام نادرة إلى رصيدك المطلق!", ephemeral=True)

        elif self.values[0] == "ترقية العتاد للحد الأقصى (10000)":
            eco["gear_level"] = 10000
            save_data()
            await interaction.response.send_message("⚡ **[سيادة المطور]**: تم رفع مستوى العتاد فوراً إلى الحد الأقصى الأسطوري **10,000**!", ephemeral=True)

        elif self.values[0] == "إحصائيات النظام السيادية":
            embed_stats = discord.Embed(
                title="👑 النظام السيادي المركزي للإحصائيات",
                description="تقرير أداء الخادم العام:",
                color=0xFFD700
            )
            embed_stats.add_field(name="👥 المغامرون المسجلون", value=f"`{len(REGISTERED_USERS)}` بطل", inline=True)
            embed_stats.add_field(name="🏰 النقابات الإمبراطورية", value=f"`{len(GUILDS_DATA)}` نقابة", inline=True)
            embed_stats.add_field(name="⚙️ الحالة التشغيلية", value="🟢 نشط ومؤمن بالكامل", inline=True)
            await interaction.response.send_message(embed=embed_stats, ephemeral=True)

class DevDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevDashboardSelect())

@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الإمبراطورية الفخمة الخاصة بالمطور الحصري")
async def dev_dashboard(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة بالكامل لمطور النظام والمشرفين السياديين!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⚡ ⟪ المـَنْصـَة السـِّيـادِيـة لـِلـْمـُطـَوِّر ⟫ ⚡",
        description="أنت الآن في قمة السيطرة المطلقة على النظام الإمبراطوري. اختر من القائمة الفخمة أدناه الإجراء الذي ترغب بتنفيذه:",
        color=0x000000
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="نظام الأمان السيادي • مرخص للمطور الحصري فقط")
    await interaction.response.send_message(embed=embed, view=DevDashboardView(), ephemeral=True)


# ==================== 3. نظام الطوابق والمعارك الواقعية والملحمية (لغاية 10000) ====================

class FloorInputModal(discord.ui.Modal, title="⚔️ بوابة صعود الطوابق الإمبراطورية"):
    floor_input = discord.ui.TextInput(
        label="أدخل رقم الطابق المطلوب صعوده", 
        placeholder="اكتب رقماً من 1 إلى 10000...", 
        max_length=5
    )

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

        # تحديد الصعوبة والوحوش
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

        # حساب صحة البطل والوحش (مع الاعتماد على عتاد اللاعب ومستوى التطور لغاية 10000)
        gear_lv = eco.get("gear_level", 1)
        hero_max_hp = 1000 + (gear_lv * 50)
        monster_max_hp = 800 + (target_floor * 35)

        hero_hp = hero_max_hp
        monster_hp = monster_max_hp

        # بدء المعركة الملحمية التفاعلية مع شريط الدم وعدادات الضربات الواقعية
        await interaction.response.send_message(
            f"⚔️ **جارٍ فتح بوابة الطابق `{target_floor}` ({difficulty})...**\n"
            f"الخصم الحالي في ساحة المعركة: **{monster_name}**\n"
            f"استعد لتلاحم السيوف والضربات المباشرة!", 
            ephemeral=False
        )
        msg = await interaction.original_response()

        # حلقات المعركة الواقعية المتدرجة بالدم والضربات
        for round_num in range(1, 5):
            await asyncio.sleep(1.8)
            
            # ضربة البطل
            hero_dmg = random.randint(200, 500) + (gear_lv * 15)
            monster_hp = max(0, monster_hp - hero_dmg)
            
            # ضربة الوحش
            monster_dmg = random.randint(100, 300) + (target_floor * 5)
            hero_hp = max(0, hero_hp - monster_dmg)

            # رسم أشرطة الدم بشكل واقعي وفخم
            hero_bar = "█" * int((hero_hp / hero_max_hp) * 10) + "░" * (10 - int((hero_hp / hero_max_hp) * 10))
            monster_bar = "█" * int((monster_hp / monster_max_hp) * 10) + "░" * (10 - int((monster_hp / monster_max_hp) * 10))

            battle_embed = discord.Embed(
                title=f"🔥 معركة شرسة في الطابق {target_floor} (الجولة {round_num}/4)",
                description=f"الساحة مشتعلة بين البطل والوحش **{monster_name}**!",
                color=0x992D22
            )
            battle_embed.add_field(
                name=f"🛡️ صحة البطل ({interaction.user.display_name})",
                value=f"`{hero_bar}`\n❤️ الدم المتبقي: **{hero_hp:,} / {hero_max_hp:,}**\n💥 أحدث ضربة منك: `-{hero_dmg:,}` للوحش",
                inline=False
            )
            battle_embed.add_field(
                name=f"👹 صحة الوحش ({monster_name})",
                value=f"`{monster_bar}`\n🩸 الدم المتبقي: **{monster_hp:,} / {monster_max_hp:,}**\n⚡ أحدث ضربة منه: `-{monster_dmg:,}` عليك",
                inline=False
            )
            await msg.edit(embed=battle_embed)

            if monster_hp <= 0 or hero_hp <= 0:
                break

        await asyncio.sleep(1.5)

        # النتيجة النهائية
        is_victory = monster_hp <= monster_max_hp * 0.5 or hero_hp > monster_hp or hero_hp > 200

        if is_victory:
            coins_reward = target_floor * 150
            gems_reward = random.randint(1, max(2, target_floor // 200 + 1))
            eco["coins"] += coins_reward
            eco["gems"] += gems_reward
            if target_floor > eco.get("max_floor", 1):
                eco["max_floor"] = target_floor
            save_data()

            win_embed = discord.Embed(
                title=f"👑 انتصار أسطوري ساحق في الطابق {target_floor}!",
                description=f"لقد تمكنت باقتدار من دحر الوحش **{monster_name}** وإخضاع الطابق بالكامل!",
                color=0x2ECC71
            )
            win_embed.add_field(name="🪙 الغنائم المكتسبة من العملات", value=f"+{coins_reward:,} عملة", inline=True)
            win_embed.add_field(name="💎 الغنائم المكتسبة من جواهر الظلام", value=f"+{gems_reward} جوهرة نادرة", inline=True)
            win_embed.add_field(name="🏆 الرقم القياسي الجديد لأعلى طابق", value=f"الطابق {eco['max_floor']}", inline=False)
            await msg.edit(embed=win_embed, view=None)
        else:
            lost_coins = min(eco["coins"], 100 * (target_floor // 10 + 1))
            eco["coins"] = max(0, eco["coins"] - lost_coins)
            save_data()

            lose_embed = discord.Embed(
                title=f"💀 هزيمة قاسية وموجعة في الطابق {target_floor}!",
                description=f"تفوق عليك الوحش المرعب **{monster_name}** وأجبرك على الانسحاب بعد معركة دموية!",
                color=0xE74C3C
            )
            lose_embed.add_field(name="⚠️ الخسائر في المعركة", value=f"فقدت `{lost_coins:,}` عملة أثناء الهروب العاجل!", inline=False)
            lose_embed.add_field(name="💡 نصيحة إمبراطورية", value="قم بتطوير عتادك الإمبراطوري حتى المستوى **10,000** عبر أمر الطابق لتعزيز قوتك المطلقة!", inline=False)
            await msg.edit(embed=lose_embed, view=None)


class UpgradeGearModal(discord.ui.Modal, title="⚒️ منصة تطوير العتاد الأسطوري (حتى 10000)"):
    levels_input = discord.ui.TextInput(
        label="عدد المستويات المراد ترقيتها",
        placeholder="أدخل عدد المستويات (يكلف كل مستوى 50 عملة)...",
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            add_levels = int(self.levels_input.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب إدخال رقم صحيح!", ephemeral=True)
            return

        if add_levels <= 0:
            await interaction.response.send_message("❌ يجب أن تكون المستويات المراد ترقيتها أكبر من صفر!", ephemeral=True)
            return

        user_id = interaction.user.id
        eco = get_user_economy(user_id)
        current_gear = eco.get("gear_level", 1)

        if current_gear + add_levels > 10000:
            await interaction.response.send_message(f"❌ عذراً، الحد الأقصى المطلق لتطوير العتاد هو **10,000** مستوى! مستواك الحالي: {current_gear}", ephemeral=True)
            return

        cost = add_levels * 50
        if eco["coins"] < cost:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي! تحتاج إلى `{cost:,}` عملة عادية لتنفيذ هذه الترقية.", ephemeral=True)
            return

        eco["coins"] -= cost
        eco["gear_level"] += add_levels
        save_data()

        embed = discord.Embed(
            title="⚒️ تمت ترقية العتاد بنجاح باهر!",
            description=f"لقد قمت بتطوير عتادك الإمبراطوري بمقدار `{add_levels}` مستوى!",
            color=0xF1C40F
        )
        embed.add_field(name="⚡ مستوى العتاد الجديد", value=f"**{eco['gear_level']} / 10,000**", inline=True)
        embed.add_field(name="🪙 التكلفة الإجمالية", value=f"`{cost:,}` عملة عادية", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TowerPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="بدء المغامرة وصعود الطوابق", style=discord.ButtonStyle.green, emoji="⚔️")
    async def start_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لتبدأ صعود الطوابق!", ephemeral=True)
            return
        await interaction.response.send_modal(FloorInputModal())

    @discord.ui.button(label="تطوير العتاد (حتى 10000)", style=discord.ButtonStyle.blurple, emoji="⚒️")
    async def upgrade_gear(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً عبر `/تسجيل` لتتمكن من تطوير عتادك!", ephemeral=True)
            return
        await interaction.response.send_modal(UpgradeGearModal())

    @discord.ui.button(label="حقيبة العتاد والملخص", style=discord.ButtonStyle.grey, emoji="🎒")
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in REGISTERED_USERS:
            await interaction.response.send_message("❌ لم تقم بالتسجيل بعد!", ephemeral=True)
            return
        eco = get_user_economy(user_id)
        embed = discord.Embed(
            title="🏰 لوحة حالة برج المغامرات والعتاد",
            description=f"ملخص بيانات المغامر الإمبراطوري:",
            color=0x3498DB
        )
        embed.add_field(name="⚡ مستوى العتاد الحالي", value=f"**{eco.get('gear_level', 1)} / 10,000**", inline=True)
        embed.add_field(name="🏆 أعلى طابق تم بلوغه", value=f"الطابق **{eco.get('max_floor', 1)}**", inline=True)
        embed.add_field(name="🪙 العملات العادية", value=f"{eco['coins']:,} عملة", inline=True)
        embed.add_field(name="💎 جواهر الظلام", value=f"{eco['gems']} جوهرة", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="الطابق", description="فتح القائمة الإمبراطورية المتكاملة لصعود الطوابق، تطوير العتاد والمغامرة")
async def tower(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏰 ⟪ بـرْج العـَظـَمـَة والمـُغـَامـَرَات الإمـْبـرَاطـُوريـة ⟫ 🏰",
        description=(
            "مرحباً بك في برج التحدي الأسطوري!\n"
            "من خلال هذه اللوحة التفاعلية يمكنك اختيار ما تحتاجه بكل سلاسة:\n\n"
            "• **بدء المغامرة**: لا داعي لكتابة أرقام معقدة، اضغط الزر وأدخل رقم الطابق (من 1 إلى 10,000).\n"
            "• **تطوير العتاد**: ارفع قوة عتادك تدريجياً لغاية الحد الأقصى **10,000** لتصمود أمام الوحوش الأسطورية!\n"
            "• **المعارك**: تتميز المعارك الآن بنظام دم وتدمير تفاعلي واقعي يوضح الضربات لحظة بلحظة."
        ),
        color=0x8E44AD
    )
    embed.set_footer(text="اختر أحد الأزرار أدناه للبدء فوراً...")
    await interaction.response.send_message(embed=embed, view=TowerPanelView(), ephemeral=False)


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
    embed.add_field(name="⚒️ مستوى العتاد", value=f"{eco.get('gear_level', 1)} / 10,000", inline=True)
    embed.add_field(name="🏰 أعلى طابق تم بلوغه", value=f"الطابق {eco.get('max_floor', 1)}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

bot.run(os.getenv('TOKEN'))
