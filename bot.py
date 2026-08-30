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

# ================== قاعدة بيانات الأبطال والعتاد الضخم ==================
HEROES_DATA = {
    "assassin_dev": {"name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)", "emoji": "🩸", "power_boost": 999999},
    "arthur": {
        "name": "آرثر (الذكر الأول)",
        "gender": "ذكر",
        "story": "فارس من عوالم ضائعة وُلد وسط عواصف النيازك، يحمل سيفاً يستمد طاقته من نوى النجوم الميتة.",
        "power": "شفرة النجوم الفضائية",
        "stats": {"hp": 1400, "attack": 180, "defense": 120}
    },
    "zeal": {
        "name": "زيل (الذكر الثاني)",
        "gender": "ذكر",
        "story": "ساحر ظلامي تمرد على معابد الأبعاد السبعة، يسيطر على شظايا الزمان والمكان ليعطل حركة خصومه.",
        "power": "التلاعب بالزمن المظلم",
        "stats": {"hp": 1000, "attack": 240, "defense": 70}
    },
    "thorin": {
        "name": "ثورين (الذكر الثالث)",
        "gender": "ذكر",
        "story": "عملاق صخور البراكين القديمة، وُلد من حمم العصور الغابرة ليحمي البوابات السرية من الانهيار.",
        "power": "درع الصهارة الأبدي",
        "stats": {"hp": 1800, "attack": 130, "defense": 220}
    },
    "lyra": {
        "name": "ليرا (الأنثى الأولى)",
        "gender": "أنثى",
        "story": "أميرة الرياح العاتية في الغابات البلورية، تتحرك بخفة البرق وتطلق أسهماً مكللة بالجليد الأزرق.",
        "power": "عاصفة السهم الجليدي",
        "stats": {"hp": 1100, "attack": 210, "defense": 80}
    },
    "morgana": {
        "name": "مورغانا (الأنثى الثانية)",
        "gender": "أنثى",
        "story": "كاهنة الأرواح المحرمة القادمة من مستنقعات الأوهام، تستدعي طاقات النجوم المظلمة لامتصاص طاقة الأعداء.",
        "power": "امتصاص الأرواح الضائعة",
        "stats": {"hp": 1250, "attack": 190, "defense": 100}
    },
    "valkyrie": {
        "name": "فالكيري (الأنثى الثالثة)",
        "gender": "أنثى",
        "story": "مقاتلة السواتر السماوية، ترتدي دروعاً مهندسة من سبائك النجوم ولديها قدرة مطلقة على اختراق الحصون.",
        "power": "صاعقة التميز السماوي",
        "stats": {"hp": 1350, "attack": 200, "defense": 110}
    }
}

# توليد 25 قطعة لكل فئة في المتجر العادي والمظلم برمجيًا
CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]

def generate_normal_shop_items():
    items = {}
    for cat in CATEGORIES:
        cat_items = []
        for i in range(1, 26):
            cat_items.append({
                "name": f"{cat} إمبراطوري #{i}",
                "price": i * 1500,
                "power": i * 100,
                "category": cat
            })
        items[cat] = cat_items
    return items

def generate_dark_shop_items():
    items = {}
    dark_ranks = ["السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي"]
    
    for cat in CATEGORIES:
        cat_items = []
        for i in range(1, 26):
            if i >= 23:
                rank_title = dark_ranks[i - 23]
                cat_items.append({
                    "name": f"{cat} {rank_title} الخارق",
                    "price": i * 5000,
                    "power": i * 2500,
                    "rank": rank_title,
                    "category": cat
                })
            else:
                cat_items.append({
                    "name": f"{cat} ظلال العذاب #{i}",
                    "price": i * 800,
                    "power": i * 350,
                    "rank": "مظلم محرم",
                    "category": cat
                })
        items[cat] = cat_items
    return items

NORMAL_SHOP = generate_normal_shop_items()
DARK_SHOP = generate_dark_shop_items()

# ================== موديلات الإدخال ولوحات التحكم ==================

class DevGiftModal(discord.ui.Modal, title="إهداء عتاد لعضو"):
    gear_name = discord.ui.TextInput(label="اسم قطعة العتاد أو السلاح", placeholder="مثال: سيف التنين الاسطوري", required=True)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = str(self.target_member.id)
            users_col.update_one({"user_id": target_id}, {"$push": {"inventory": self.gear_name.value}}, upsert=True)
            await interaction.followup.send(f"🎁 **تم إرسال العتاد بنجاح!** حصل المستخدم {self.target_member.mention} على القطعة: `{self.gear_name.value}` ⚔️", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء إرسال العتاد.", ephemeral=True)

class DevAddBalanceModal(discord.ui.Modal, title="إضافة رصيد لعضو"):
    amount = discord.ui.TextInput(label="المبلغ المراد إضافته", placeholder="مثال: 500000", required=True)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = str(self.target_member.id)
            val = int(self.amount.value)
            users_col.update_one({"user_id": target_id}, {"$inc": {"balance": val}}, upsert=True)
            await interaction.followup.send(f"✅ تم إضافة `{val:,}` 🪙 إلى محفظة المستخدم {self.target_member.mention} بنجاح!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ!", ephemeral=True)

# ================== واجهات المتاجر (Views) ==================

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="استعراض المتجر الإمبراطوري", style=discord.ButtonStyle.success, emoji="🏛️", row=0)
    async def normal_catalog(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ كتالوج متجر الإمبراطورية المركزي",
            description="مرحباً بك في السوق الآمن. يتوفر هنا 200 قطعة عتاد رسمية موزعة على 8 فئات أساسية.",
            color=discord.Color.gold()
        )
        embed.add_field(name="🛡️ الفئات المتاحة", value="خوذة | درع | بنطال | حذاء | سيف | مطرقة | خنجر | عصا سحرية", inline=False)
        embed.set_footer(text="العملة المستخدمة: العملات الذهبية 🪙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="الدخول للسوق المظلم 🕳️", style=discord.ButtonStyle.danger, emoji="🩸", row=0)
    async def enter_dark_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🩸 تحذير: أنت على وشك دخول سوق الظلال الملعون!",
            description="هنا حيث تسود الشياطين وتُباع أسلحة الرتب الثلاث المرعبة.",
            color=discord.Color.dark_embed()
        )
        await interaction.response.edit_message(embed=embed, view=DarkShopView())

class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="عروض رتب الشياطين الحصرية", style=discord.ButtonStyle.danger, emoji="👑", row=0)
    async def dark_catalog(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔥 عرش الأسلحة المحرمة والرتب المطلقة",
            description="أنت تستعرض الآن أقوى العتاد في اللعبة بأسرها.",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="العملة المستخدمة: الألماس الأسود النادر 💎")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="العودة للمنطقة الآمنة 🏛️", style=discord.ButtonStyle.secondary, emoji="🔙", row=0)
    async def return_normal_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ متجر الإمبراطورية المركزي (المنطقة الآمنة)",
            description="أهلاً بك مجدداً في النور.",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=NormalShopView())

# ================== أوامر المتاجر الرئيسية ==================

@bot.tree.command(name="المتجر", description="فتح بوابة المتاجر (العادي والمظلم)")
async def shop_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏛️ متجر الإمبراطورية المركزي",
        description="أهلاً بك أيها المقاتل. الإمبراطورية ترحب بك في السوق الرئيسي الآمن.",
        color=discord.Color.gold()
    )
    embed.add_field(name="⚔️ الأقسام المتوفرة", value="• خوذة | درع | بنطال | حذاء\n• سيف | مطرقة | خنجر | عصا سحرية", inline=False)
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

# ================== نظام استعراض الأبطال (/الابطال) ==================

class HeroesSelect(discord.ui.Select):
    def __init__(self):
        heroes_list = {k: v for k, v in HEROES_DATA.items() if k != "assassin_dev"}
        options = [
            discord.SelectOption(
                label=data["name"],
                value=hero_key,
                description=f"النوع: {data['gender']} | القوة: {data['power']}"
            )
            for hero_key, data in heroes_list.items()
        ]
        super().__init__(placeholder="اختر بطلاً لاستعراض قصته وقواته...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        hero = HEROES_DATA[chosen]
        
        embed = discord.Embed(
            title=f"🛡️ تفاصيل البطل: {hero['name']}",
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="📜 القصة الفانتازية", value=hero["story"], inline=False)
        embed.add_field(name="⚡ القدرة الخارقة", value=hero["power"], inline=True)
        embed.add_field(name="🧬 الجنس", value=hero["gender"], inline=True)
        embed.add_field(
            name="📊 المعدلات الخاصة",
            value=f"❤️ الصحة (HP): `{hero['stats']['hp']}`\n⚔️ الهجوم: `{hero['stats']['attack']}`\n🛡️ الدفاع: `{hero['stats']['defense']}`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HeroesSelect())

@bot.tree.command(name="الابطال", description="استعراض قائمة الأبطال الفانتازيا وقصصهم ومعدلاتهم الخاصة")
async def command_heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ سجل الأبطال الأسطوريين",
        description="اختر أحد الأبطال من القائمة أدناه للاطلاع على قصته وقوته ومعدلاته القتالية:",
        color=discord.Color.gold()
    )
    view = HeroesView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ================== أمر البنك (الإيداع والسحب) ==================
@bot.tree.command(name="البنك", description="إدارة أموالك في البنك الإمبراطوري (إيداع / سحب)")
@app_commands.describe(operation="اختر العملية (إيداع أو سحب)", amount="المبلغ المراد تحويله أو كتابة 'الكل'")
@app_commands.choices(operation=[
    app_commands.Choice(name="إيداع", value="deposit"),
    app_commands.Choice(name="سحب", value="withdraw")
])
async def bank_command(interaction: discord.Interaction, operation: str, amount: str):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    
    if operation == "deposit":
        if amount.lower() in ["الكل", "all"]:
            val = balance
        else:
            try:
                val = int(amount)
            except ValueError:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ أو كتابة 'الكل'.", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك إيداع مبلغ صفري أو سالب!", ephemeral=True)
        if balance < val:
            return await interaction.followup.send(f"❌ رصيدك الحالي (`{balance:,}`) لا يكفي لإيداع هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -val, "bank": val}})
        await interaction.followup.send(f"✅ تم إيداع `{val:,}` 🪙 بنجاح في البنك الإمبراطوري!", ephemeral=True)
        
    elif operation == "withdraw":
        if amount.lower() in ["الكل", "all"]:
            val = bank
        else:
            try:
                val = int(amount)
            except ValueError:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ أو كتابة 'الكل'.", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك سحب مبلغ صفري أو سالب!", ephemeral=True)
        if bank < val:
            return await interaction.followup.send(f"❌ رصيدك البنكي الحالي (`{bank:,}`) لا يكفي لسحب هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": val, "bank": -val}})
        await interaction.followup.send(f"✅ تم سحب `{val:,}` 🪙 بنجاح من البنك إلى محفظتك!", ephemeral=True)

# ================== أمر صعود الطوابق / المغامرة ==================
@bot.tree.command(name="المغامرة", description="صعود طوابق البرج القتالي وقتال الوحوش لزيادة الطابق والجوائز")
async def adventure_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    current_max_floor = user_data.get("max_floor", 0)
    power = user_data.get("power", 100)
    
    # محاكاة نتيجة المعركة بالاعتماد على الطاقة وقليل من الحظ
    target_floor = current_max_floor + 1
    required_power = target_floor * 50
    
    # فرصة نجاح تعتمد على القوة
    success_chance = min(90, max(30, int((power / (required_power + 1)) * 50)))
    roll = random.randint(1, 100)
    
    if roll <= success_chance or power >= required_power:
        reward_gold = target_floor * 300
        reward_kills = 1
        users_col.update_one(
            {"user_id": user_id},
            {
                "$max": {"max_floor": target_floor},
                "$inc": {"kills": reward_kills, "balance": reward_gold}
            }
        )
        embed = discord.Embed(
            title=f"🎉 انتصار مظفر في الطابق #{target_floor}!",
            description=f"لقد قاتلت ضواري البرج بشراسة وتمكنت من اجتياز الطابق بنجاح!",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 الغنائم المكتسبة", value=f"`+{reward_gold:,}` 🪙 عملة ذهبية", inline=True)
        embed.add_field(name="🏢 الطابق الجديد", value=str(target_floor), inline=True)
    else:
        embed = discord.Embed(
            title=f"💀 هزيمة قاسية في الطابق #{target_floor}!",
            description=f"كان الخصوم أقوياء جداً هذه المرة، قُم بترقية عتادك وزيادة قوتك قبل المحاولة مجدداً.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚡ طاقتك الحالية", value=f"{power:,}", inline=True)
        embed.add_field(name="🎯 الطاقة المطلوبة تقريباً", value=f"{required_power:,}", inline=True)

    await interaction.followup.send(embed=embed, ephemeral=False)

# ================== قوائم اختيار الأعضاء للمطورين ==================

class DevAddUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🛠️ اختر العضو لترقيته لمطور بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chosen_member = self.values[0]
        target_id = str(chosen_member.id)
        devs_col.update_one({"user_id": target_id}, {"$set": {"user_id": target_id}}, upsert=True)
        await interaction.followup.send(f"🛠️ **تمت الترقية بنجاح!** أصبح العضو {chosen_member.mention} مطوراً معتمداً.", ephemeral=True)

class DevAddUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevAddUserSelect())

class DevGiftUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🎁 اختر العضو لإهداء العتاد له بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        chosen_member = self.values[0]
        await interaction.response.send_modal(DevGiftModal(target_member=chosen_member))

class DevGiftUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevGiftUserSelect())

class DevBalanceUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🪙 اختر العضو لإضافة الرصيد له بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        chosen_member = self.values[0]
        await interaction.response.send_modal(DevAddBalanceModal(target_member=chosen_member))

class DevBalanceUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevBalanceUserSelect())

# ================== لوحة أزرار المطور الرئيسية ==================
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

    @discord.ui.button(label="ثروات لانهائية", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def wealth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": 999999999, "diamonds": 999999999}},
            upsert=True
        )
        await interaction.followup.send("💎 **تم ضخ الثروات اللانهائية!**", ephemeral=True)

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
        await interaction.response.send_message("🎁 اختر العضو الذي تريد إهداء العتاد له بالمنشن من القائمة أدناه:", view=DevGiftUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة رصيد", style=discord.ButtonStyle.secondary, emoji="🪙", row=1)
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🪙 اختر العضو الذي تريد إضافة الرصيد له بالمنشن من القائمة أدناه:", view=DevBalanceUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة مطور", style=discord.ButtonStyle.secondary, emoji="🛠️", row=1)
    async def add_dev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ اختر العضو الذي تريد ترقيته لمطور بالمنشن من القائمة أدناه:", view=DevAddUserSelectView(), ephemeral=True)

@bot.tree.command(name="المطور", description="لوحة السيطرة والتحكم العليا للمطورين")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة السيطرة والتحكم العليا للمطورين",
        description="أهلاً بك أيها الحاكم المطلق. استخدم الأزرار أدناه لتنفيذ الأوامر الخارقة:",
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
    embed.add_field(name="💎 الألماس الأسود والنقاد", value=f"{diamonds:,} 💎", inline=True)

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
