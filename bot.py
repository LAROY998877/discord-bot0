import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# ================== ⚙️ إعدادات الاتصال والبوت ==================
# قراءة رابط قاعدة البيانات و الـ Token من متغيرات البيئة (Railway / Replit / الخ)
MONGO_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
db_client = MongoClient(MONGO_URL)
db = db_client["empire_bot"]
users_col = db["users"]

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

def is_user_registered(user_id):
    """التحقق مما إذا كان المستخدم مسجلاً مسبقاً"""
    return users_col.find_one({"user_id": str(user_id)}) is not None

@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        print(f"✅ تم تسجيل دخول البوت بنجاح باسم: {client.user}")
        print(f"🔗 تم مزامنة {len(synced)} أمر (Slash Commands) بنجاح.")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")


# ================== 🛒 نظام المتجر العادي والمقاييس الملكية ==================

NORMAL_GEAR_CATEGORIES = {
    "خوذة": [
        {"name": "🪖 خوذة الحرس الملكي", "power": 300, "price_gold": 1500, "rank": "عادي"},
        {"name": "🪖 خوذة الفولاذ الصلب", "power": 600, "price_gold": 3200, "rank": "مطور"},
        {"name": "🪖 خوذة الصقر الذهبي", "power": 1200, "price_gold": 7000, "rank": "نادر"}
    ],
    "درع": [
        {"name": "🛡️ درع الفرسان المشاة", "power": 500, "price_gold": 2500, "rank": "عادي"},
        {"name": "🛡️ درع الحديد المصفح", "power": 900, "price_gold": 5000, "rank": "مطور"},
        {"name": "🛡️ درع الفرسان الأحرار", "power": 1500, "price_gold": 9500, "rank": "نادر"}
    ],
    "بنطال": [
        {"name": "👖 بنطال الجلد القماشي", "power": 200, "price_gold": 1000, "rank": "عادي"},
        {"name": "👖 بنطال الحديد الملعون", "power": 450, "price_gold": 2200, "rank": "مطور"},
        {"name": "👖 بنطال الحراس الملكيين", "power": 850, "price_gold": 4500, "rank": "نادر"}
    ],
    "حذاء": [
        {"name": "👢 حذاء السفر الجلدي", "power": 150, "price_gold": 800, "rank": "عادي"},
        {"name": "👢 حذاء الفرسان السريع", "power": 350, "price_gold": 1800, "rank": "مطور"},
        {"name": "👢 حذاء الرياح الخفية", "power": 700, "price_gold": 3800, "rank": "نادر"}
    ],
    "سيف": [
        {"name": "⚔️ سيف الجندي البسيط", "power": 700, "price_gold": 3000, "rank": "عادي"},
        {"name": "⚔️ سيف الفارس القاطع", "power": 1400, "price_gold": 6500, "rank": "مطور"},
        {"name": "⚔️ سيف اللهب الملكي", "power": 2500, "price_gold": 12000, "rank": "نادر"}
    ],
    "مطرقة": [
        {"name": "🔨 مطرقة الحداد الخشنة", "power": 800, "price_gold": 3500, "rank": "عادي"},
        {"name": "🔨 مطرقة الأرض المحطمة", "power": 1600, "price_gold": 7500, "rank": "مطور"},
        {"name": "🔨 مطرقة التيتانيوم الثقيلة", "power": 2800, "price_gold": 13500, "rank": "نادر"}
    ],
    "خنجر": [
        {"name": "🗡️ خنجر الظل الصغير", "power": 400, "price_gold": 2000, "rank": "عادي"},
        {"name": "🗡️ خنجر القاتل الخفي", "power": 900, "price_gold": 4500, "rank": "مطور"},
        {"name": "🗡️ خنجر الأفعى السامة", "power": 1700, "price_gold": 8500, "rank": "نادر"}
    ],
    "عصا سحرية": [
        {"name": "🪄 عصا المبتدئ السحرية", "power": 600, "price_gold": 2800, "rank": "عادي"},
        {"name": "🪄 عصا اللهب الأزرق", "power": 1300, "price_gold": 6000, "rank": "مطور"},
        {"name": "🪄 عصا النجوم المضيئة", "power": 2400, "price_gold": 11000, "rank": "نادر"}
    ]
}

class NormalShopCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="خوذة", description="تصفح خوذ الحماية العادية", emoji="🪖"),
            discord.SelectOption(label="درع", description="تصفح الدروع الحربية", emoji="🛡️"),
            discord.SelectOption(label="بنطال", description="تصفح السراويل الواقية", emoji="👖"),
            discord.SelectOption(label="حذاء", description="تصفح أحذية السرعة", emoji="👢"),
            discord.SelectOption(label="سيف", description="تصفح السيوف الحادة", emoji="⚔️"),
            discord.SelectOption(label="مطرقة", description="تصفح المطارق الثقيلة", emoji="🔨"),
            discord.SelectOption(label="خنجر", description="تصفح الخناجر السريعة", emoji="🗡️"),
            discord.SelectOption(label="عصا سحرية", description="تصفح العصا السحرية", emoji="🪄"),
        ]
        super().__init__(placeholder="🛡️ اختر فئة العتاد في المتجر العادي...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        items = NORMAL_GEAR_CATEGORIES[cat]
        
        view = NormalShopItemView(cat, items)
        embed = discord.Embed(
            title=f"🛡️ متجر الإمبراطورية — قسم [{cat}]",
            description="اختر القطعة التي تريد شراءها بالعملة الذهبية 🪙 لتعزيز قوتك:",
            color=discord.Color.blue()
        )
        for item in items:
            embed.add_field(
                name=item["name"],
                value=f"⚡ القوة: `+{item['power']:,}`\n🪙 السعر: `{item['price_gold']:,}` ذهب\n🎖️ الرتبة: `{item['rank']}`",
                inline=False
            )
        await interaction.response.edit_message(embed=embed, view=view)

class NormalShopItemSelect(discord.ui.Select):
    def __init__(self, category: str, items: list):
        self.category = category
        options = [
            discord.SelectOption(
                label=item["name"],
                value=str(item["power"]) + "|" + str(item["price_gold"]) + "|" + item["name"],
                description=f"القوة: +{item['power']:,} | السعر: {item['price_gold']:,} 🪙"
            ) for item in items
        ]
        super().__init__(placeholder=f"🛒 اختر قطعة من {category} لشرائها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        parts = self.values[0].split("|")
        power, price, name = int(parts[0]), int(parts[1]), parts[2]
        
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        
        if not user_data:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
            
        if user_data.get("balance", 0) < price:
            return await interaction.response.send_message(f"❌ لا تملك ما يكفي من الذهب! تحتاج إلى `{price:,}` 🪙.", ephemeral=True)
            
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"balance": -price, "power": power},
                "$push": {"inventory": name}
            }
        )
        
        embed = discord.Embed(
            title="✨ عملية شراء ناجحة!",
            description=f"لقد قمت بشراء **[{name}]** بنجاح!\n⚡ زادت طاقتك بمقدار `+{power:,}`.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(NormalShopCategorySelect())

class NormalShopItemView(discord.ui.View):
    def __init__(self, category: str, items: list):
        super().__init__()
        self.add_item(NormalShopItemSelect(category, items))
        
        back_btn = discord.ui.Button(label="🔙 عودة للفئات", style=discord.ButtonStyle.secondary)
        async def back_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🏛️ متجر الإمبراطورية العام",
                    description="مرحباً بك أيها المغامر في المتجر الملكي. اختر الفئة المطلوبة من القائمة أدناه لتجهيز نفسك:",
                    color=discord.Color.blue()
                ),
                view=NormalShopView()
            )
        back_btn.callback = back_callback
        self.add_item(back_btn)

@client.tree.command(name="متجر", description="🛒 فتح متجر الإمبراطورية العام لشراء العتاد بالذهب")
async def normal_shop_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
        
    embed = discord.Embed(
        title="🏛️ متجر الإمبراطورية العام",
        description="مرحباً بك أيها المغامر في المتجر الملكي الأساسي.\nاختر فئة العتاد التي ترغب في استعراضها وشراؤها بالعملة الذهبية 🪙:",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)


# ================== 🌑 المتجر المظلم السري والمعدات الأسطورية الخارقة ==================

DARK_GEAR_CATEGORIES = {
    "خوذة": [
        {"name": "🩸 خوذة الجحيم المظلمة", "power": 25000, "price_diamonds": 100, "rank": "الشيطان الأبدي"},
        {"name": "💀 خوذة الأرواح المعذبة", "power": 18000, "price_diamonds": 70, "rank": "الجحيم القاتل"},
        {"name": "🗡️ خوذة الظل الدموي", "power": 12000, "price_diamonds": 45, "rank": "السفاح القرمزي"}
    ],
    "درع": [
        {"name": "🩸 درع التنين الأسود الأبدي", "power": 35000, "price_diamonds": 150, "rank": "الشيطان الأبدي"},
        {"name": "💀 درع الفوضى العارمة", "power": 26000, "price_diamonds": 110, "rank": "الجحيم القاتل"},
        {"name": "🗡️ درع الهلاك القرمزي", "power": 19000, "price_diamonds": 80, "rank": "السفاح القرمزي"}
    ],
    "بنطال": [
        {"name": "🩸 بنطال الهاوية السوداء", "power": 22000, "price_diamonds": 90, "rank": "الشيطان الأبدي"},
        {"name": "💀 بنطال رعب الكهوف", "power": 16000, "price_diamonds": 60, "rank": "الجحيم القاتل"},
        {"name": "🗡️ بنطال القاتل الصامت", "power": 11000, "price_diamonds": 40, "rank": "السفاح القرمزي"}
    ],
    "حذاء": [
        {"name": "🩸 حذاء خطوات الجحيم", "power": 20000, "price_diamonds": 85, "rank": "الشيطان الأبدي"},
        {"name": "💀 حذاء البرق الأسود", "power": 15000, "price_diamonds": 55, "rank": "الجحيم القاتل"},
        {"name": "🗡️ حذاء الانقضاض السريع", "power": 10000, "price_diamonds": 35, "rank": "السفاح القرمزي"}
    ],
    "سيف": [
        {"name": "🩸 سيف عذاب الأرواح الأبدي", "power": 50000, "price_diamonds": 250, "rank": "الشيطان الأبدي"},
        {"name": "💀 سيف الهلاك الشامل", "power": 38000, "price_diamonds": 180, "rank": "الجحيم القاتل"},
        {"name": "🗡️ سيف الدم الشره", "power": 28000, "price_diamonds": 120, "rank": "السفاح القرمزي"}
    ],
    "مطرقة": [
        {"name": "🩸 مطرقة تحطيم العوالم الأبدية", "power": 55000, "price_diamonds": 270, "rank": "الشيطان الأبدي"},
        {"name": "💀 مطرقة زلازل الجحيم", "power": 40000, "price_diamonds": 190, "rank": "الجحيم القاتل"},
        {"name": "🗡️ مطرقة الغضب القرمزي", "power": 30000, "price_diamonds": 130, "rank": "السفاح القرمزي"}
    ],
    "خنجر": [
        {"name": "🩸 خنجر الموت المحتوم", "power": 45000, "price_diamonds": 220, "rank": "الشيطان الأبدي"},
        {"name": "💀 خنجر السموم القاتلة", "power": 33000, "price_diamonds": 150, "rank": "الجحيم القاتل"},
        {"name": "🗡️ خنجر الظل الدموي السريع", "power": 24000, "price_diamonds": 100, "rank": "السفاح القرمزي"}
    ],
    "عصا سحرية": [
        {"name": "🩸 عصا الفراغ والظلام المطلق", "power": 52000, "price_diamonds": 260, "rank": "الشيطان الأبدي"},
        {"name": "💀 عصا اللهب الأسود المحرق", "power": 39000, "price_diamonds": 185, "rank": "الجحيم القاتل"},
        {"name": "🗡️ عصا التعاويذ المحرمة", "power": 29000, "price_diamonds": 125, "rank": "السفاح القرمزي"}
    ]
}

class DarkShopCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="خوذة", description="خوذ مظلمة برتب رعب أبدية", emoji="🩸"),
            discord.SelectOption(label="درع", description="دروع حماية الجحيم الفولاذية", emoji="💀"),
            discord.SelectOption(label="بنطال", description="سراويل الهاوية والظلال", emoji="👖"),
            discord.SelectOption(label="حذاء", description="أحذية السرعة الشيطانية", emoji="👢"),
            discord.SelectOption(label="سيف", description="سيوف الدم والأرواح المدمرة", emoji="⚔️"),
            discord.SelectOption(label="مطرقة", description="مطارق تحطيم الأبعاد", emoji="🔨"),
            discord.SelectOption(label="خنجر", description="خناجر الاغتيال السريعة", emoji="🗡️"),
            discord.SelectOption(label="عصا سحرية", description="عصي الفراغ والسحر الأسود", emoji="🔮"),
        ]
        super().__init__(placeholder="🌑 اختر فئة العتاد في المتجر المظلم السري...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        items = DARK_GEAR_CATEGORIES[cat]
        
        view = DarkShopItemView(cat, items)
        embed = discord.Embed(
            title=f"🌑 المتجر المظلم السري — قسم [{cat}]",
            description="⚠️ **تحذير:** معدات محرمة وقوية للغاية! تُشترى حصرياً بالألماس والعملات النادرة 💎:",
            color=discord.Color.from_rgb(40, 0, 0)
        )
        for item in items:
            embed.add_field(
                name=item["name"],
                value=f"⚡ القوة الخارقة: `+{item['power']:,}`\n💎 السعر: `{item['price_diamonds']:,}` ألماس\n🔥 الرتبة: **{item['rank']}**",
                inline=False
            )
        await interaction.response.edit_message(embed=embed, view=view)

class DarkShopItemSelect(discord.ui.Select):
    def __init__(self, category: str, items: list):
        self.category = category
        options = [
            discord.SelectOption(
                label=item["name"],
                value=str(item["power"]) + "|" + str(item["price_diamonds"]) + "|" + item["name"],
                description=f"القوة: +{item['power']:,} | السعر: {item['price_diamonds']} 💎 | {item['rank']}"
            ) for item in items
        ]
        super().__init__(placeholder=f"🩸 اختر قطعة مظلمة من {category}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        parts = self.values[0].split("|")
        power, price, name = int(parts[0]), int(parts[1]), parts[2]
        
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        
        if not user_data:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
            
        if user_data.get("diamonds", 0) < price:
            return await interaction.response.send_message(f"❌ لا تملك ما يكفي من الألماس والعملات النادرة! تحتاج إلى `{price}` 💎.", ephemeral=True)
            
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"diamonds": -price, "power": power},
                "$push": {"inventory": name}
            }
        )
        
        embed = discord.Embed(
            title="🩸 عقد الظلام الأبدي تم بنجاح!",
            description=f"لقد حصلت على العتاد المحرم **[{name}]**!\n⚡ تضاعفت طاقتك بقوة مظلمة تبلغ `+{power:,}`.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DarkShopCategorySelect())

class DarkShopItemView(discord.ui.View):
    def __init__(self, category: str, items: list):
        super().__init__()
        self.add_item(DarkShopItemSelect(category, items))
        
        back_btn = discord.ui.Button(label="🔙 عودة لفئات المتجر المظلم", style=discord.ButtonStyle.danger)
        async def back_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🌑 المتجر المظلم السري — Dark Sanctuary",
                    description="أهلاً بك في قاع الظلمات حيث تُباع أعتى وأقوى الأسلحة والعتاد في الإمبراطورية.\nاختر فئة العتاد المطلوبة:",
                    color=discord.Color.from_rgb(40, 0, 0)
                ),
                view=DarkShopView()
            )
        back_btn.callback = back_callback
        self.add_item(back_btn)

@client.tree.command(name="المتجر_المظلم", description="🌑 فتح المتجر المظلم السري لشراء العتاد الأسطوري بالألماس")
async def dark_shop_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
        
    embed = discord.Embed(
        title="🌑 المتجر المظلم السري — Dark Sanctuary",
        description="أهلاً بك في قاع الظلمات حيث تُباع أعتى وأقوى الأسلحة والعتاد في الإمبراطورية.\n"
                    "🔥 جميع المعدات هنا تحمل رتب عليا ومخيفة:\n"
                    "• **الشيطان الأبدي**\n• **الجحيم القاتل**\n• **السفاح القرمزي**\n\n"
                    "اختر الفئة التي تريد استعراضها (التداول حصرياً بالألماس والعملات النادرة 💎):",
        color=discord.Color.from_rgb(40, 0, 0)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)


# ================== ⚡ نظام تطوير المعدلات المطلقة (بلا حدود) ==================

STATS_CONFIG = {
    "aim": {"name": "التصويب", "emoji": "🎯", "desc": "دقة إصابة الأهداف البعيدة بدقة متناهية"},
    "dodge": {"name": "المراوغة", "emoji": "💨", "desc": "القدرة الاحترافية على تفادي الضربات القاتلة"},
    "attack": {"name": "الهجوم", "emoji": "⚔️", "desc": "قوة الضربات الجسدية المباشرة والمدمرة"},
    "precision": {"name": "الدقة", "emoji": "🎯", "desc": "إصابة نقاط الضعف الخفية للخصوم"},
    "critical": {"name": "الضربة القاتلة", "emoji": "☠️", "desc": "مضاعفة ضرر الإصابات الحرجة والمهلكة"},
    "magic": {"name": "السحر", "emoji": "🔮", "desc": "السيطرة المطلقة على تدفق الطاقات المحرمة"},
    "intelligence": {"name": "الذكاء", "emoji": "🧠", "desc": "سرعة البديهة واستراتيجيات القتال العميقة"},
    "defense": {"name": "الدفاع", "emoji": "🛡️", "desc": "امتصاص وتخفيف أعتى أضرار الهجمات القادمة"}
}

class StatsUpgradeModal(discord.ui.Modal, title="⚡ هيكلة وتطوير المعدلات المطلقة بلا حدود"):
    points_input = discord.ui.TextInput(
        label="عدد النقاط المراد إضافتها للمعدل",
        placeholder="مثال: 1000 أو 500000000",
        min_length=1,
        required=True
    )

    def __init__(self, stat_key: str):
        super().__init__()
        self.stat_key = stat_key

    async def on_submit(self, interaction: discord.Interaction):
        try:
            points_to_add = int(self.points_input.value.strip().replace(",", ""))
            if points_to_add <= 0:
                return await interaction.response.send_message("❌ يجب أن يكون عدد النقاط أكبر من الصفر!", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال رقم صحيح وصريح!", ephemeral=True)

        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

        cost_per_point = 1000
        total_cost = points_to_add * cost_per_point

        current_gold = user_data.get("balance", 0)
        if current_gold < total_cost:
            return await interaction.response.send_message(
                f"❌ رصيدك من الذهب لا يكفي لتنفيذ هذا التطوير الجبار!\n"
                f"• التكلفة المطلوبة: `{total_cost:,}` 🪙\n"
                f"• رصيدك الحالي: `{current_gold:,}` 🪙",
                ephemeral=True
            )

        stat_info = STATS_CONFIG[self.stat_key]

        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": -total_cost,
                    f"stats.{self.stat_key}": points_to_add,
                    "power": points_to_add
                }
            }
        )

        embed = discord.Embed(
            title="🔥 تم صقل وهندسة المعدلات الإمبراطورية بنجاح!",
            description=f"لقد قمت برفع معدل **{stat_info['emoji']} {stat_info['name']}** إلى مستويات مرعبة!\n\n"
                        f"• **النقاط المضافة:** `+{points_to_add:,}`\n"
                        f"• **التكلفة المستقطعة:** `{total_cost:,}` 🪙 ذهب\n"
                        f"• **الارتقاء بالقوة الكلية:** `+{points_to_add:,}` ⚡",
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["name"],
                value=key,
                description=info["desc"][:50],
                emoji=info["emoji"]
            ) for key, info in STATS_CONFIG.items()
        ]
        super().__init__(placeholder="⚡ اختر المعدل المراد تطويره بلا حدود...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        stat_key = self.values[0]
        await interaction.response.send_modal(StatsUpgradeModal(stat_key))

class StatsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(StatsSelect())

@client.tree.command(name="المعدلات", description="⚡ قاعة صقل وتطوير المعدلات القتالية المطلقة بلا حدود")
async def stats_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    stats = user_data.get("stats", {})
    
    desc_lines = []
    for key, info in STATS_CONFIG.items():
        val = stats.get(key, 0)
        desc_lines.append(f"{info['emoji']} **{info['name']}:** `{val:,}`")

    embed = discord.Embed(
        title="⚡ معبد القدرات المطلقة — Stat Sanctuary",
        description="أهلاً بك في مقدّس الصقل الإمبراطوروي.\n"
                    "هنا تتجاوز حدود البشر، وترفع معدلاتك العسكرية إلى آفاق لا نهائية حتى وإن وصلت لمليارات النقاط!\n"
                    "• **سعر النقطة الواحدة:** `1,000` 🪙 ذهب.\n\n"
                    "📊 **معدلاتك الحالية:**\n" + "\n".join(desc_lines),
        color=discord.Color.from_rgb(15, 25, 45)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="⚡ التطوير مفتوح بلا سقف أو قيود إمبراطورية")
    await interaction.response.send_message(embed=embed, view=StatsView(), ephemeral=True)


# ================== 🚀 تشغيل البوت ==================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ خطأ: يرجى وضع التوكن الخاص بالبوت في متغير البيئة DISCORD_TOKEN.")
