import os, random, asyncio, pymongo, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MAIN_DEV_ID = "1103985971638325269"

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col, guilds_col, devs_col = db["users"], db["guilds"], db["devs"]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
AUTO_BATTLES = {}
ACTIVE_GAMES = {}

def is_user_registered(uid) -> bool:
    return users_col.find_one({"user_id": str(uid)}) is not None

def is_dev(uid) -> bool:
    suid = str(uid)
    if suid == MAIN_DEV_ID or devs_col.find_one({"user_id": suid}):
        return True
    u = users_col.find_one({"user_id": suid})
    return bool(u and u.get("is_dev"))

def add_game_win(uid: str, game_key: str, pts: int = 1):
    users_col.update_one(
        {"user_id": str(uid)},
        {
            "$inc": {
                f"game_score.{game_key}": pts,
                "game_score.total": pts,
                "balance": pts * 100
            }
        },
        upsert=True
    )

CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]
DARK_RANKS = ["مشعوذ الظلال", "السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي", "حاكم الظلمات"]
GEN_R = [("مبتدئ","🟢"), ("فولاذي","🪙"), ("ملكي","👑"), ("أسطوري","🌟"), ("إمبراطوري","🐉")]
DRK_R = [("مشعوذ الظلال","🌑"), ("السفاح القرمزي","🩸"), ("الجحيم القاتل","🔥"), ("الشيطان الأبدي","😈"), ("حاكم الظلمات","☠️")]

GEAR_DATA, ALL_GENERAL_ITEMS, ALL_DARK_ITEMS = {}, [], []
for cat in CATEGORIES:
    GEAR_DATA[cat] = []
    for i in range(1, 26):
        rk, em = GEN_R[(i-1)//5]
        g_item = {"id": f"gen_{cat}_{i}", "name": f"{em} {cat} [{rk}] T{i}", "rank": rk, "emoji": em, "power": i*50, "price": i*400, "store": "general"}
        GEAR_DATA[cat].append(g_item)
        ALL_GENERAL_ITEMS.append(g_item)

        drk, dem = DRK_R[(i-1)//5]
        d_item = {"id": f"dark_{cat}_{i}", "name": f"💀 {cat} [{drk}] T{i}", "rank": drk, "emoji": dem, "power": i*250, "price": i*8, "store": "dark"}
        GEAR_DATA[cat].append(d_item)
        ALL_DARK_ITEMS.append(d_item)

GEN_ITEM_POWER_MAP = {it["name"]: it["power"] for it in ALL_GENERAL_ITEMS}
DARK_ITEM_POWER_MAP = {it["name"]: it["power"] for it in ALL_DARK_ITEMS}

HEROES_CFG = {
    "valerian": {"name": "فالريان، سيف الشمس", "gender": "ذكر", "emoji": "⚔️", "story": "فارس أسطوري ولد تحت نجم ملتهب.", "base_power": 1200, "stats": {"leadership": 35, "attack": 30, "defense": 25, "aim": 10, "magic": 5, "intelligence": 15, "deception": 5}},
    "ignis": {"name": "إغنيس، سيد اللهب الأسود", "gender": "ذكر", "emoji": "🔥", "story": "ساحر ظلال قديم تحكم بعناصر النار المظلمة.", "base_power": 1350, "stats": {"magic": 40, "intelligence": 30, "attack": 25, "leadership": 10, "aim": 10, "defense": 10, "deception": 10}},
    "zephyr": {"name": "زفير، ظل الرماة", "gender": "ذكر", "emoji": "🎯", "story": "قناص الغابات المحرمة الذي لا تخطئ سهامه.", "base_power": 1150, "stats": {"aim": 40, "deception": 25, "attack": 25, "intelligence": 15, "defense": 10, "magic": 5, "leadership": 10}},
    "lucian": {"name": "لوكيان، حارس العرش الفولاذي", "gender": "ذكر", "emoji": "🛡️", "story": "درع الإمبراطورية الأخير الذي صمد أمام الجيوش.", "base_power": 1250, "stats": {"defense": 45, "leadership": 25, "intelligence": 20, "attack": 15, "aim": 5, "magic": 5, "deception": 5}},
    "malakai": {"name": "مالاكاي، حائك الأوهام", "gender": "ذكر", "emoji": "🎭", "story": "سيد التجسس والدسائس الذي يتلاعب بالعقول.", "base_power": 1100, "stats": {"deception": 45, "intelligence": 35, "aim": 15, "magic": 15, "leadership": 10, "attack": 10, "defense": 5}},
    "athena": {"name": "أثينا، قائدة الفرسان الستة", "gender": "أنثى", "emoji": "👑", "story": "إمبراطورة الميدان التي تقود الجيش بذكاء.", "base_power": 1300, "stats": {"leadership": 40, "defense": 25, "attack": 25, "intelligence": 20, "aim": 10, "magic": 5, "deception": 5}},
    "serene": {"name": "سيرين، كاهنة القمر والبحار", "gender": "أنثى", "emoji": "🔮", "story": "سيدة السحر السماوي لتطهير الأرض.", "base_power": 1400, "stats": {"magic": 45, "intelligence": 30, "leadership": 20, "defense": 15, "aim": 10, "deception": 5, "attack": 10}},
    "lyra": {"name": "ليرا، عاصفة السهام", "gender": "أنثى", "emoji": "🏹", "story": "صيادة سريعة كالعاصفة بأسلحة ضوئية.", "base_power": 1200, "stats": {"aim": 42, "attack": 28, "deception": 20, "intelligence": 15, "leadership": 10, "defense": 5, "magic": 10}},
    "morgana": {"name": "مورغانا، ملكة الدسائس", "gender": "أنثى", "emoji": "🖤", "story": "حاكمة الظلال التي تلاعبت بعقول الملوك.", "base_power": 1250, "stats": {"deception": 42, "magic": 30, "intelligence": 28, "aim": 10, "leadership": 10, "attack": 5, "defense": 5}},
    "hilda": {"name": "هيلدا، جدار الجليد", "gender": "أنثى", "emoji": "❄️", "story": "محاربة الشمال الأسطورية التي تسخر طاقة الجليد.", "base_power": 1280, "stats": {"defense": 40, "attack": 30, "leadership": 20, "intelligence": 15, "magic": 10, "aim": 10, "deception": 5}}
}

HERO_STATS_CFG = {
    "aim": ("التصويب", "🎯"), "magic": ("السحر", "🔮"), "attack": ("الهجوم", "🗡️"),
    "defense": ("الدفاع", "🛡️"), "intelligence": ("الذكاء", "🧠"), "deception": ("الخداع", "🎭"), "leadership": ("القيادة", "👑")
}

STATS_CFG = {
    "aim": ("التصويب", "🎯"), "evasion": ("المراوغة", "💨"), "attack": ("الهجوم", "🗡️"),
    "accuracy": ("الدقة", "👁️"), "critical": ("الضربات القاتلة", "💥"), "magic": ("السحر", "🔮"),
    "intelligence": ("الذكاء", "🧠"), "defense": ("الدفاع", "🛡️")
}

# ==================== بنك بيانات الألعاب ====================

QUESTIONS_DATA = {
    "normal": [f"ما هي موهبتك السرية رقم {i}؟" for i in range(1, 51)],
    "medium": [f"ما هو أكبر قرار ندمت عليه في حياتك رقم {i}؟" for i in range(1, 51)],
    "bold": [f"سؤال شديد السرية والجريء رقم {i}: هل خنت ثقة صديق من قبل؟" for i in range(1, 51)]
}

PUNISHMENTS_DATA = {
    "normal": [f"قم بغناء مقطع من أغنيتك المفضلة بصوت عالٍ." for _ in range(50)],
    "medium": [f"غير صورتك الشخصية لصورة مضحكة يختارها الروم لمدة 10 دقائق." for _ in range(50)],
    "bold": [f"اعترف بكلمة صريحة لشخص في السيرفر أمام الجميع فوراً." for _ in range(50)]
}

RIDDLES = [
    ("ما هو الشيء الذي كلما أخذت منه كبر؟", "الحفرة"),
    ("ما هو الشيء الذي يمشي بلا أرجل ويدخل الأذنين؟", "الصوت"),
    ("ما هو الشيء الذي ينبض بلا قلب؟", "الساعة"),
    ("ما هو الشيء الذي يحترق لِيُضيء لغيره؟", "الشمعة"),
    ("أخضر في الأرض، وأسود في السوق، وأحمر في البيت؟", "الشاي")
] + [(f"لغز رقم {i}: ما هو الشيء الذي له عين واحدة ولا يرى؟", "الابرة") for i in range(6, 151)]

MATH_EQUATIONS = [
    ("5 + 7 * 2", "19"), ("12 * 12", "144"), ("100 / 4 + 15", "40"),
    ("15 * 3 - 10", "35"), ("81 / 9 + 7", "16")
] + [(f"{i} + {i*2}", str(i + i*2)) for i in range(6, 151)]

ANIME_DATA = [
    ("بطل يستدعي تنين الجنيهات السبعة بالكرات الأسطورية", ["دراغون بول", "درغون بول"]),
    ("نينجا يطمح ليصبح الهوكاجي ويحمل الثعلب ذو التسعة أذيل", ["ناروتو", "ناروتو شيبودن"]),
    ("قرصان قبعة القش يبحث عن الكنز الأسطوري ليكون ملك القراصنة", ["ون بيس", "ونبيس"]),
    ("صياد يبحث عن والده ويخوض امتحان الصيادين مع أصدقائه", ["القناص", "هنتر"]),
    ("عمالقة يهاجمون الأسوار الشامخة والطفل ينتقم لأمه", ["هجوم العمالقة", "هجوم عمالقة"]),
    ("قاتل شياطين يحمل أخته في صندوق خشبي على ظهره", ["قاتل الشياطين", "ديمون سلاير"]),
    ("مستلهم السحر يستدعي كتاب المهارات ذو الخمس أوراق", ["بلاك كلوفر"]),
    ("أنمي عن الشينجامي والمفكرة السحرية التي تقتل من يُكتب اسمه فيها", ["دفتر الموت", "مذكرة الموت", "ديث نوت"]),
    ("طالب يبتلع إصبع ملك اللعنات لينتقل لعالم السحر واللعنات", ["جوجوتسو كايسن", "جوجوتسو"]),
    ("بطل صلب لا يهزم ويقضي على الأعداء بضربة واحدة فقط", ["ون بنش مان", "رجل الضربة الواحدة"]),
    ("طفل متحري يتقلص حجمه بعد تناول عقار سري ويحل القضايا", ["المحقق كونان", "كونان"]),
    ("طبيب نفسي يتعقب قاتلاً متسلسلاً عبقرياً في ألمانيا", ["مونستر", "مانستر"]),
    ("مجموعة من النينجا يرتدون زي الشينجامي ويحملون سيوف الزانباكتو", ["بليتش"]),
    ("محارب يرتدي قناع ليلوش ويقود ثورة ضد إمبراطورية بريطانيا", ["كود غياس", "كود جياس"]),
    ("عالم ألعاب افتراضية حيث الموت في اللعبة يعني الموت في الحقيقة", ["سورد آرت أونلاين", "سورد ارت اونلاين"]),
    ("لاعب شطرنج وسلاح مظلم يتم استدعاؤه في عالم موازٍ ليصبح الحاكم الأكبر", ["سولو ليفلينج", "سولو ليفلينغ"]),
    ("كيميائيان يبحثان عن حجر الفلاسفة لاستعادة أجسادهم المفقودة", ["الكيميائي المعدني", "فل ميتال"]),
    ("فتاة وأخيها يخوضان معركة في عالم الألعاب حيث كل شيء يتقرر باللعب", ["نو جيم نو لايف"]),
    ("مجموعة من العلماء الهواة يكتشفون طريقة لإرسال رسائل عبر الزمن", ["شتاينز جيت", "شتاينز غيت"]),
    ("فتى ينتحر في طوكيو فيتحول إلى نصف غول بعد زرع أعضاء له", ["طوكيو غول", "طوكيو جول"])
]

CUT_TWEETS = [
    "هل الصداقة بين الجنسين ممكنة بدون مشاعر حب مستقبلاً؟",
    "هل الذكاء الاصطناعي يستطيع استبدال الوظائف البشرية بالكامل؟",
    "هل المال يشتري السعادة الحقيقية بنسبة 100%؟",
    "هل خيانة الصديق أشد إيلاماً من خيانة الحبيب؟",
    "هل التغاضي يعتبر ضعف شخصية أم قمة الحكمة؟"
]

DECONSTRUCT_WORDS = [
    ("إمبراطورية", "إ م ب ر ا ط و ر ي ة"),
    ("شيطان", "ش ي ط ا ن"),
    ("مقاتل", "م ق ا ت ل"),
    ("أسطورة", "أ س ط و ر ة"),
    ("فرسان", "ف ر س ا ن")
] + [(f"كلمة{i}", " ".join(list(f"كلمة{i}"))) for i in range(6, 101)]

FASTEST_WORDS = [
    "الإمبراطورية العظمى", "سيد الظلال", "مقاتل الظلال الأسطوري",
    "بوت الديسكورد", "السفاح القرمزي", "الانتصار الملكي", "القتال الملكي",
    "ملك العالم", "سرعة البديهة", "البطل الأسطوري", "العرش الإمبراطوري",
    "البطل الخارق", "حاكم الجحيم", "فرسان الشرف", "درع الفولاذ", "سيف العدالة"
] + [f"كلمة_سريعة_{i}" for i in range(17, 150)]

# ==================== كلاسات التسجيل والمتجر والخصائص ====================

class RegisterModal(discord.ui.Modal, title="📜 استمارة التسجيل في الإمبراطورية"):
    name_in = discord.ui.TextInput(label="الاسم", placeholder="اسم الشخصية...", min_length=2, max_length=30)
    age_in = discord.ui.TextInput(label="العمر", placeholder="مثال: 25", min_length=1, max_length=4)
    gen_in = discord.ui.TextInput(label="الجنس", placeholder="ذكر / أنثى", min_length=3, max_length=4)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            age = int(self.age_in.value.strip())
            if not (1 <= age <= 3000): raise ValueError()
        except:
            await ctx.response.send_message("❌ العمر يجب أن يكون رقماً بين 1 و 3000!", ephemeral=True)
            return

        gender = self.gen_in.value.strip()
        if gender not in ["ذكر", "أنثى"]:
            await ctx.response.send_message("❌ اكتب (ذكر) أو (أنثى) فقط!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        users_col.insert_one({
            "user_id": uid, "name": self.name_in.value.strip(), "age": age, "gender": gender,
            "created_at": datetime.now(timezone.utc), "balance": 5000, "bank": 0, "diamonds": 20,
            "power": 100, "kills": 0, "max_floor": 1, "inventory": [], "titles": ["المبتدئ الأسطوري"],
            "custom_title": "المبتدئ الأسطوري", "is_dev": (uid == MAIN_DEV_ID),
            "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10, "critical": 10, "magic": 10, "intelligence": 10, "defense": 10,
            "last_daily": None, "loan": 0, "chosen_hero": None, "hero_stats": {}, "guild_id": None
        })
        emb = discord.Embed(title="👑 تم التسجيل بنجاح!", color=discord.Color.gold())
        emb.add_field(name="🪪 الاسم", value=f"`{self.name_in.value}`", inline=True)
        emb.add_field(name="⏳ العمر", value=f"`{age}`", inline=True)
        emb.add_field(name="🎁 الهدايا", value="5,000 🪙 | 20 💎", inline=False)
        await ctx.response.send_message(embed=emb)

class GeneralItemSelect(discord.ui.Select):
    def __init__(self, cat: str):
        self.cat = cat
        opts = [discord.SelectOption(label=it["name"], value=it["id"], description=f"⚡+{it['power']:,} | 🪙{it['price']:,}", emoji=it["emoji"]) for it in GEAR_DATA[cat] if it["store"] == "general"]
        super().__init__(placeholder=f"⚔️ عتاد [{cat}]...", options=opts[:25])

    async def callback(self, ctx: discord.Interaction):
        uid = str(ctx.user.id)
        item = next(i for i in GEAR_DATA[self.cat] if i["id"] == self.values[0])
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < item["price"]:
            await ctx.response.send_message("❌ لا تملك ذهباً كافياً!", ephemeral=True)
            return
        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -item["price"], "power": item["power"]}, "$push": {"inventory": item["name"]}})
        await ctx.response.send_message(f"🛍️ تم شراء **{item['name']}** بـ `{item['price']:,}` 🪙!", ephemeral=True)

class GeneralCategorySelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="🏰 اختر قسم العتاد...", options=[discord.SelectOption(label=c, value=c, emoji="🛡️") for c in CATEGORIES])

    async def callback(self, ctx: discord.Interaction):
        v = discord.ui.View()
        v.add_item(GeneralCategorySelect())
        v.add_item(GeneralItemSelect(self.values[0]))
        await ctx.response.edit_message(embed=discord.Embed(title=f"🏛️ قسم [{self.values[0]}]", color=discord.Color.gold()), view=v)

class GeneralStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GeneralCategorySelect())

class DarkItemSelect(discord.ui.Select):
    def __init__(self, cat: str):
        self.cat = cat
        opts = [discord.SelectOption(label=it["name"], value=it["id"], description=f"⚡+{it['power']:,} | 💎{it['price']:,}", emoji=it["emoji"]) for it in GEAR_DATA[cat] if it["store"] == "dark"]
        super().__init__(placeholder=f"🔮 عتاد ظلال [{cat}]...", options=opts[:25])

    async def callback(self, ctx: discord.Interaction):
        uid = str(ctx.user.id)
        item = next(i for i in GEAR_DATA[self.cat] if i["id"] == self.values[0])
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("diamonds", 0) < item["price"]:
            await ctx.response.send_message("❌ لا تملك ألماساً كافياً!", ephemeral=True)
            return
        users_col.update_one({"user_id": uid}, {"$inc": {"diamonds": -item["price"], "power": item["power"]}, "$push": {"inventory": item["name"]}})
        await ctx.response.send_message(f"⚡ تم شراء **{item['name']}** بـ `{item['price']:,}` 💎!", ephemeral=True)

class DarkCategorySelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="👁️ اختر قسم الظلال...", options=[discord.SelectOption(label=c, value=c, emoji="🌑") for c in CATEGORIES])

    async def callback(self, ctx: discord.Interaction):
        v = discord.ui.View()
        v.add_item(DarkCategorySelect())
        v.add_item(DarkItemSelect(self.values[0]))
        await ctx.response.edit_message(embed=discord.Embed(title=f"🖤 خزنة الظلال — [{self.values[0]}]", color=discord.Color.purple()), view=v)

class DarkStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DarkCategorySelect())

class StatUpgradeModal(discord.ui.Modal):
    def __init__(self, key: str):
        self.key = key
        name, _ = STATS_CFG[key]
        super().__init__(title=f"🚀 ترقية: {name}")
        self.pts_in = discord.ui.TextInput(label="عدد النقاط (النقطة = 100 🪙)", placeholder="مثال: 10")
        self.add_item(self.pts_in)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            pts = int(self.pts_in.value.strip())
            if pts <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً أكبـر من 0!", ephemeral=True)
            return

        cost = pts * 100
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < cost:
            await ctx.response.send_message(f"❌ تكلفة الترقية `{cost:,}` 🪙 وغير متوفرة برصيدك!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -cost, self.key: pts, "power": pts * 10}})
        name, emo = STATS_CFG[self.key]
        await ctx.response.send_message(f"🔥 تم زيادة {emo} **{name}** بـ `+{pts:,}` نقطة!")

class StatSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=name, value=k, emoji=emo, description="100 🪙 للنقطة") for k, (name, emo) in STATS_CFG.items()]
        super().__init__(placeholder="🔥 اختر المعدل لتطويره...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.send_modal(StatUpgradeModal(self.values[0]))

class StatsUpgradeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(StatSelect())

# ==================== كلاسات برج الطوابق ====================

def render_hp_bar(cur: int, max_hp: int) -> str:
    pct = max(0.0, min(1.0, cur / max_hp)) if max_hp > 0 else 0
    f = int(pct * 10)
    return f"`[{'█'*f}{'░'*(10-f)}]` {cur:,}/{max_hp:,} HP"

async def process_floor_battle(ctx_or_msg, user_id: str, floor_num: int, is_first: bool = True):
    if floor_num > 500:
        AUTO_BATTLES[user_id] = False
        msg_txt = "🏆 **مبروك! أتممت جميع طوابق البرج الـ 500 بنجاح وصعدت العرش الأسطوري!**"
        if is_first:
            await ctx_or_msg.response.send_message(msg_txt, ephemeral=True)
        else:
            await ctx_or_msg.edit(content=msg_txt, embed=None, view=None)
        return

    AUTO_BATTLES[user_id] = True
    u = users_col.find_one({"user_id": user_id}) or {}

    is_boss = (floor_num % 10 == 0)

    if is_boss:
        e_name = f"👑 زعيم الطابق {floor_num} — [تنين الجحيم المظلم]" if floor_num % 50 == 0 else f"👹 قائد الظلال (BOSS طابق {floor_num})"
        e_hp = 600 + (floor_num * 400)
        e_atk = 50 + (floor_num * 35)
    else:
        e_name = random.choice([
            f"🧟 زومبي الطابق {floor_num}",
            f"🐺 ذئب الظلال طابق {floor_num}",
            f"🗿 الحارس الحجري طابق {floor_num}",
            f"🗡️ مقاتل الموت طابق {floor_num}"
        ])
        e_hp = 180 + (floor_num * 120)
        e_atk = 20 + (floor_num * 15)

    p_atk = int(u.get("attack", 10) * 15 + u.get("power", 100) * 1.5)
    p_max_hp = int(400 + u.get("defense", 10) * 30 + u.get("power", 100) * 2.5)
    p_cur_hp = p_max_hp
    e_cur_hp = e_hp

    p_name = u.get("name", "المقاتل")
    h_id = u.get("chosen_hero")
    hero_info = HEROES_CFG.get(h_id, {}) if h_id else {}
    hero_name = hero_info.get("name", "البطل") if h_id else None

    desc_dialogue = f"⚔️ **بداية المعركة!**\nتقدم **{p_name}** بثقة نحو عرش الطابق `{floor_num}` في مواجهة **{e_name}**!"

    emb = discord.Embed(
        title=f"🏰 │ معركة ملحمية — الطابق [{floor_num} / 500]",
        description=desc_dialogue,
        color=discord.Color.red() if is_boss else discord.Color.dark_orange()
    )
    emb.add_field(name=f"👤 {p_name}", value=render_hp_bar(p_cur_hp, p_max_hp), inline=True)
    emb.add_field(name=f"👾 {e_name}", value=render_hp_bar(e_cur_hp, e_hp), inline=True)
    emb.set_footer(text="⚔️ القتال والتقدم يعملان تلقائياً... اضغط الزر بالأسفل للإيقاف.")

    class StopAutoView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="🛑 إيقاف القتال التلقائي", style=discord.ButtonStyle.danger)
        async def stop_btn(self, btn_ctx: discord.Interaction, button: discord.ui.Button):
            if str(btn_ctx.user.id) != user_id:
                await btn_ctx.response.send_message("❌ هذه المعركة ليست لك!", ephemeral=True)
                return
            AUTO_BATTLES[user_id] = False
            await btn_ctx.response.send_message("🛑 تم إيقاف الغزو التلقائي بعد انتهاء هذه الجولة.", ephemeral=True)

    view = StopAutoView()

    if is_first:
        await ctx_or_msg.response.send_message(embed=emb, view=view)
        msg = await ctx_or_msg.original_response()
    else:
        await ctx_or_msg.edit(embed=emb, view=view)
        msg = ctx_or_msg

    while p_cur_hp > 0 and e_cur_hp > 0 and AUTO_BATTLES.get(user_id, True):
        await asyncio.sleep(1.2)

        damage_dealt = random.randint(int(p_atk * 0.8), int(p_atk * 1.2))
        is_crit = random.random() < 0.2
        if is_crit:
            damage_dealt = int(damage_dealt * 1.7)
            dialogue = f"💥 **ضربة قاضية!** يوجه **{p_name}** سيفه نحو ثغرة **{e_name}** ليسبب `{damage_dealt:,}` ضرر حرج!"
        else:
            dialogue = f"⚔️ **هجوم حاسم!** يستغل **{p_name}** سرعته ويضرب **{e_name}** بضرر قدره `{damage_dealt:,}`!"

        if hero_name and random.random() < 0.3:
            hero_dmg = random.randint(100, 300) + floor_num * 10
            damage_dealt += hero_dmg
            dialogue += f"\n✨ **مساندة أسطورية!** ينقض **{hero_name}** ويزيد الضرر بـ `+{hero_dmg:,}` ضرر سحري!"

        e_cur_hp = max(0, e_cur_hp - damage_dealt)

        if e_cur_hp <= 0:
            dialogue += f"\n💀 **السقوط!** يترنح **{e_name}** ويسقط صريعاً على أرض المعركة!"

        emb.description = dialogue
        emb.set_field_at(0, name=f"👤 {p_name}", value=render_hp_bar(p_cur_hp, p_max_hp), inline=True)
        emb.set_field_at(1, name=f"👾 {e_name}", value=render_hp_bar(e_cur_hp, e_hp), inline=True)
        try:
            await msg.edit(embed=emb)
        except:
            break

        if e_cur_hp <= 0:
            break

        await asyncio.sleep(1.2)
        enemy_dmg = random.randint(int(e_atk * 0.7), int(e_atk * 1.1))
        p_cur_hp = max(0, p_cur_hp - enemy_dmg)

        e_dialogue = f"🔥 **رد الخصم!** يزأر **{e_name}** بقوة وينفذ هجوماً مضاداً يلحق `{enemy_dmg:,}` ضرر بـ **{p_name}**!"
        if p_cur_hp <= 0:
            e_dialogue += f"\n💔 **الهزيمة!** خارت قوى **{p_name}** وتراجع لحماية حياته!"

        emb.description = e_dialogue
        emb.set_field_at(0, name=f"👤 {p_name}", value=render_hp_bar(p_cur_hp, p_max_hp), inline=True)
        emb.set_field_at(1, name=f"👾 {e_name}", value=render_hp_bar(e_cur_hp, e_hp), inline=True)
        try:
            await msg.edit(embed=emb)
        except:
            break

    if p_cur_hp > 0 and e_cur_hp <= 0:
        gold_reward = floor_num * 400 + random.randint(200, 800)
        power_reward = 40 + (50 if is_boss else 0)

        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"balance": gold_reward, "power": power_reward, "kills": 1},
                "$set": {"max_floor": floor_num + 1}
            }
        )

        win_emb = discord.Embed(
            title=f"🎉 │ انتصار ساحق في الطابق [{floor_num}]!",
            description=(
                f"🏆 تم القضاء على **{e_name}** بنجاح بعد معركة طاحنة!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 **المكافأة المالية:** `+{gold_reward:,}` ذهب\n"
                f"⚡ **القوة المكتسبة:** `+{power_reward}` طاقة\n"
                f"🏰 **الطابق التالي:** `[{floor_num + 1} / 500]`"
            ),
            color=discord.Color.gold()
        )

        if AUTO_BATTLES.get(user_id, True):
            win_emb.set_footer(text="🚀 جاري الانتقال تلقائياً إلى الطابق التالي خلال 3 ثوانٍ...")
            try:
                await msg.edit(embed=win_emb, view=view)
            except:
                pass
            await asyncio.sleep(3)

            if AUTO_BATTLES.get(user_id, True):
                await process_floor_battle(msg, user_id, floor_num + 1, is_first=False)
        else:
            win_emb.set_footer(text="🛑 تم إيقاف القتال التلقائي بناءً على طلبك.")
            try:
                await msg.edit(embed=win_emb, view=None)
            except:
                pass
    else:
        AUTO_BATTLES[user_id] = False
        loss_emb = discord.Embed(
            title=f"💔 │ هزيمة في الطابق [{floor_num}]",
            description=f"لم تطعك قوتك على هزم **{e_name}**!\nقم بتطوير معدلاتك وعتادك وبطلك من المتجر ثم حاول مجدداً.",
            color=discord.Color.dark_red()
        )
        try:
            await msg.edit(embed=loss_emb, view=None)
        except:
            pass

class TowerMainSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="بدء المغامرة والتألق", value="start", emoji="⚔️"),
            discord.SelectOption(label="المتجر العادي", value="gen", emoji="🛒"),
            discord.SelectOption(label="المتجر المظلم", value="dark", emoji="🔮"),
            discord.SelectOption(label="تطوير معداتي", value="up", emoji="⚡")
        ]
        super().__init__(placeholder="🏰 اختر الإجراء...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        v = self.values[0]
        if v == "start":
            await process_floor_battle(ctx, str(ctx.user.id), u.get("max_floor", 1), is_first=True)
        elif v == "gen":
            await ctx.response.send_message(embed=discord.Embed(title="🏛️ المتجر العام", color=discord.Color.gold()), view=GeneralStoreView(), ephemeral=True)
        elif v == "dark":
            await ctx.response.send_message(embed=discord.Embed(title="🔮 المتجر المظلم", color=discord.Color.purple()), view=DarkStoreView(), ephemeral=True)
        elif v == "up":
            await ctx.response.send_message(embed=discord.Embed(title="✨ تطوير المعدلات", color=discord.Color.red()), view=StatsUpgradeView(), ephemeral=True)

class TowerMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TowerMainSelect())

# ==================== كلاسات الليدربورد العام والأبطال ====================

class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="ترتيب اقوى اللاعبين", value="top_power", emoji="⚡", description="حسب إجمالي الطاقة والقوة"),
            discord.SelectOption(label="ترتيب اغني اللاعبين", value="top_rich", emoji="🪙", description="حسب إجمالي الذهب بالكاش والبنك"),
            discord.SelectOption(label="ترتيب قاهر اللاعبين", value="top_kills", emoji="🩸", description="حسب عدد القتلات والإطاحات"),
            discord.SelectOption(label="ترتيب المعدات العادية", value="top_gen_gear", emoji="🛡️", description="حسب قوة العتاد العادي الممتلك"),
            discord.SelectOption(label="ترتيب المعدات المحرمة", value="top_dark_gear", emoji="🔮", description="حسب قوة عتاد الظلال المحرم"),
            discord.SelectOption(label="ترتيب غزو الطوابق", value="top_floors", emoji="🏰", description="حسب أعلى طابق تم الوصول إليه"),
            discord.SelectOption(label="ترتيب جامع الالقاب", value="top_titles", emoji="👑", description="حسب عدد الألقاب المكتسبة")
        ]
        super().__init__(placeholder="🏆 اختر تصنيف الليدربورد...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        all_u = list(users_col.find())

        if v == "top_power":
            all_u.sort(key=lambda x: x.get("power", 0), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — ⚡ `{u.get('power',0):,}` طاقة" for i, u in enumerate(all_u[:10])])
            title = "⚡ ترتيب أقوى اللاعبين"

        elif v == "top_rich":
            all_u.sort(key=lambda x: x.get("balance",0) + x.get("bank",0), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🪙 `{u.get('balance',0)+u.get('bank',0):,}` ذهب" for i, u in enumerate(all_u[:10])])
            title = "🪙 ترتيب أغنى اللاعبين"

        elif v == "top_kills":
            all_u.sort(key=lambda x: x.get("kills",0), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🩸 `{u.get('kills',0):,}` قتلة" for i, u in enumerate(all_u[:10])])
            title = "🩸 ترتيب قاهر اللاعبين"

        elif v == "top_gen_gear":
            def get_gen_power(u):
                inv = u.get("inventory", [])
                return sum(GEN_ITEM_POWER_MAP.get(item, 0) for item in inv)

            all_u.sort(key=get_gen_power, reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🛡️ `{get_gen_power(u):,}` قوة عتاد عادي" for i, u in enumerate(all_u[:10])])
            title = "🛡️ ترتيب أقوى اللاعبين (المعدات العادية)"

        elif v == "top_dark_gear":
            def get_dark_power(u):
                inv = u.get("inventory", [])
                return sum(DARK_ITEM_POWER_MAP.get(item, 0) for item in inv)

            all_u.sort(key=get_dark_power, reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🔮 `{get_dark_power(u):,}` قوة عتاد محرم" for i, u in enumerate(all_u[:10])])
            title = "🔮 ترتيب أقوى اللاعبين (المعدات المحرمة)"

        elif v == "top_floors":
            all_u.sort(key=lambda x: x.get("max_floor",1), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🏢 الطابق `{u.get('max_floor',1)}`" for i, u in enumerate(all_u[:10])])
            title = "🏰 ترتيب غزو الطوابق"

        elif v == "top_titles":
            def get_title_count(u):
                t = u.get("titles", [])
                return len(t) if isinstance(t, list) else 0

            all_u.sort(key=get_title_count, reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 👑 `{get_title_count(u):,}` ألقاب" for i, u in enumerate(all_u[:10])])
            title = "👑 ترتيب جامع الألقاب"

        emb = discord.Embed(title=title, description=txt or "لا توجد بيانات مسجلة حالياً", color=discord.Color.gold())
        vw = discord.ui.View()
        vw.add_item(LeaderboardSelect())
        await ctx.response.edit_message(embed=emb, view=vw)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())

class HeroSelect(discord.ui.Select):
    def __init__(self):
        opts = []
        for h_id, h in HEROES_CFG.items():
            opts.append(discord.SelectOption(
                label=h["name"],
                value=h_id,
                emoji=h["emoji"],
                description=f"[{h['gender']}] ⚡ قوة بدائية: {h['base_power']:,}"
            ))
        super().__init__(placeholder="🦸‍♂️ اختر البطل/البطلة للتعرف عليه واختياره...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        h_id = self.values[0]
        h = HEROES_CFG[h_id]
        uid = str(ctx.user.id)

        emb = discord.Embed(
            title=f"{h['emoji']} {h['name']} ({h['gender']})",
            description=f"**📜 القصة الفانتازية:**\n{h['story']}",
            color=discord.Color.gold() if h['gender'] == "ذكر" else discord.Color.purple()
        )
        emb.add_field(name="⚡ القوة البدائية", value=f"`{h['base_power']:,}`", inline=False)

        stats_txt = []
        for s_key, (s_name, s_emo) in HERO_STATS_CFG.items():
            val = h["stats"].get(s_key, 0)
            stats_txt.append(f"{s_emo} {s_name}: `{val}`")
        emb.add_field(name="📊 معدلات البطل الأساسية", value=" | ".join(stats_txt), inline=False)

        v = discord.ui.View()
        v.add_item(HeroSelect())

        btn = discord.ui.Button(label=f"👑 اختيار {h['name']} كبطل رسمي لك", style=discord.ButtonStyle.success)

        async def adopt_hero_callback(b_ctx: discord.Interaction):
            if str(b_ctx.user.id) != uid:
                await b_ctx.response.send_message("❌ هذا العرض ليس لك!", ephemeral=True)
                return

            init_stats = h["stats"].copy()
            users_col.update_one(
                {"user_id": uid},
                {
                    "$set": {"chosen_hero": h_id, "hero_stats": init_stats},
                    "$inc": {"power": h["base_power"]}
                }
            )
            await b_ctx.response.send_message(f"🎉 تهانينا! اخترت **{h['name']}** ليكون بطل إمبراطوريتك الرسمي!\nأضيفت `+{h['base_power']:,}` ⚡ لقوتك الكلية.", ephemeral=True)

        btn.callback = adopt_hero_callback
        v.add_item(btn)

        await ctx.response.edit_message(embed=emb, view=v)

class HeroesView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HeroSelect())

class HeroStatUpgradeModal(discord.ui.Modal):
    def __init__(self, key: str):
        self.key = key
        s_name, _ = HERO_STATS_CFG[key]
        super().__init__(title=f"🚀 تطوير: {s_name} (بدون حد أقصى)")
        self.pts_in = discord.ui.TextInput(label="عدد النقاط المطلوبة (النقطة = 150 🪙)", placeholder="مثال: 50 أو 1000")
        self.add_item(self.pts_in)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            pts = int(self.pts_in.value.strip())
            if pts <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً أكبـر من 0!", ephemeral=True)
            return

        cost = pts * 150
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}

        if u.get("balance", 0) < cost:
            await ctx.response.send_message(f"❌ تكلفة التطوير `{cost:,}` 🪙 وغير متوفرة في كاشك!", ephemeral=True)
            return

        h_id = u.get("chosen_hero")
        if not h_id or h_id not in HEROES_CFG:
            await ctx.response.send_message("❌ لم تقم باختيار بطل بعد! استخدم `/الابطال` أولاً.", ephemeral=True)
            return

        stat_path = f"hero_stats.{self.key}"
        users_col.update_one(
            {"user_id": uid},
            {
                "$inc": {
                    "balance": -cost,
                    stat_path: pts,
                    "power": pts * 15
                }
            }
        )
        s_name, s_emo = HERO_STATS_CFG[self.key]
        await ctx.response.send_message(f"🔥 تم زيادة {s_emo} **{s_name}** لبطلـك بـ `+{pts:,}` نقطة!\n• التكلفة: `{cost:,}` 🪙\n• الزيادة بالقوة الكلية: `+{pts*15:,}` ⚡")

class HeroStatSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=s_name, value=k, emoji=s_emo, description="150 🪙 للنقطة الواحدة (مفتوح)") for k, (s_name, s_emo) in HERO_STATS_CFG.items()]
        super().__init__(placeholder="⚡ اختر المعدل المراد تطويره لبطلك...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.send_modal(HeroStatUpgradeModal(self.values[0]))

class HeroUpgradeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HeroStatSelect())

# ==================== كلاسات لوحة المطورين وعتاد T25 ====================

class DevTitleModal(discord.ui.Modal, title="👑 منح/تحديد لقب خاص"):
    title_in = discord.ui.TextInput(label="اكتب اللقب المطلوب", placeholder="مثال: حاكم العوالم، قاهر الظلال...", min_length=2, max_length=40)

    async def on_submit(self, ctx: discord.Interaction):
        t_name = self.title_in.value.strip()
        uid = str(ctx.user.id)
        users_col.update_one(
            {"user_id": uid},
            {
                "$push": {"titles": t_name},
                "$set": {"custom_title": t_name}
            }
        )
        await ctx.response.send_message(f"👑 تم إضافة اللقب **[{t_name}]** وتعيينه كـ لقبك الرسمي بنجاح!", ephemeral=True)

class DevAddUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="👤 اختر العضو لترقيته إلى مطور...", min_values=1, max_values=1)

    async def callback(self, ctx: discord.Interaction):
        if str(ctx.user.id) != MAIN_DEV_ID:
            await ctx.response.send_message("❌ هذا الإجراء مقتصر على المطور الرئيسي فقط!", ephemeral=True)
            return
        target = self.values[0]
        devs_col.update_one({"user_id": str(target.id)}, {"$set": {"user_id": str(target.id)}}, upsert=True)
        users_col.update_one({"user_id": str(target.id)}, {"$set": {"is_dev": True}})
        await ctx.response.send_message(f"👑 تم منح صلاحيات المطور لـ {target.mention} بنجاح!", ephemeral=True)

class DevAddUserView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevAddUserSelect())

class DevTransferModal(discord.ui.Modal):
    def __init__(self, target_user: discord.User):
        super().__init__(title=f"💸 تحويل إلى {target_user.display_name[:15]}")
        self.target_user = target_user
        self.amount_in = discord.ui.TextInput(label="المبلغ المراد إهداؤه/تحويله", placeholder="مثال: 50000")
        self.curr_in = discord.ui.TextInput(label="نوع العملة (اكتب: ذهب أو ألماس)", placeholder="ذهب / ألماس", default="ذهب")
        self.add_item(self.amount_in)
        self.add_item(self.curr_in)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if amt <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً أكبـر من 0!", ephemeral=True)
            return

        curr = self.curr_in.value.strip()
        field = "diamonds" if ("ألم" in curr or "الم" in curr or "dia" in curr.lower()) else "balance"
        sym = "💎" if field == "diamonds" else "🪙"

        t_id = str(self.target_user.id)
        if not is_user_registered(t_id):
            await ctx.response.send_message("❌ هذا اللاعب غير مسجل باللعبة!", ephemeral=True)
            return

        users_col.update_one({"user_id": t_id}, {"$inc": {field: amt}})
        await ctx.response.send_message(f"🎁 تم شحن/تحويل `{amt:,}` {sym} إلى {self.target_user.mention} بنجاح!", ephemeral=True)

class DevTransferUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="👤 اختر اللاعب المراد تحويل/إهداء العملات له...", min_values=1, max_values=1)

    async def callback(self, ctx: discord.Interaction):
        target = self.values[0]
        await ctx.response.send_modal(DevTransferModal(target))

class DevTransferUserView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevTransferUserSelect())

class DevGearUserSelect(discord.ui.UserSelect):
    def __init__(self, item: dict):
        super().__init__(placeholder="👤 اختر اللاعب بالمنشن لإهدائه العتاد...", min_values=1, max_values=1)
        self.item = item

    async def callback(self, ctx: discord.Interaction):
        target = self.values[0]
        t_id = str(target.id)

        if not is_user_registered(t_id):
            await ctx.response.send_message("❌ هذا اللاعب غير مسجل باللعبة!", ephemeral=True)
            return

        users_col.update_one(
            {"user_id": t_id},
            {
                "$push": {"inventory": self.item["name"]},
                "$inc": {"power": self.item["power"]}
            }
        )

        emb = discord.Embed(
            title="🎁 تم إهداء العتاد بنجاح!",
            description=f"• **المستلم:** {target.mention}\n• **العتاد:** {self.item['name']}\n• **القوة المضافة:** `+{self.item['power']:,}` ⚡",
            color=discord.Color.gold()
        )
        await ctx.response.send_message(embed=emb, ephemeral=True)

class DevGearUserView(discord.ui.View):
    def __init__(self, item: dict):
        super().__init__(timeout=60)
        self.add_item(DevGearUserSelect(item))

class DevGearItemSelect(discord.ui.Select):
    def __init__(self, cat: str, store_type: str):
        self.cat = cat
        self.store_type = store_type
        st_name = "general" if store_type == "gen" else "dark"
        items = [it for it in GEAR_DATA[cat] if it["store"] == st_name]
        opts = [discord.SelectOption(label=it["name"], value=it["id"], description=f"⚡+{it['power']:,}", emoji=it["emoji"]) for it in items]
        super().__init__(placeholder=f"⚔️ اختر القطعة المراد إهداؤها من [{cat}]...", options=opts[:25])

    async def callback(self, ctx: discord.Interaction):
        item_id = self.values[0]
        item = next(i for i in GEAR_DATA[self.cat] if i["id"] == item_id)
        await ctx.response.send_message(f"👤 اختر اللاعب بالمنشن الذي تريد إهداؤه **{item['name']}**:", view=DevGearUserView(item), ephemeral=True)

class DevGearCategorySelect(discord.ui.Select):
    def __init__(self):
        opts = []
        for c in CATEGORIES:
            opts.append(discord.SelectOption(label=f"{c} (عادي)", value=f"gen_{c}", emoji="🛡️"))
            opts.append(discord.SelectOption(label=f"{c} (ظلال محرم)", value=f"dark_{c}", emoji="🔮"))
        super().__init__(placeholder="🎁 اختر قسم ونوع العتاد للإهداء...", options=opts[:25])

    async def callback(self, ctx: discord.Interaction):
        val = self.values[0]
        store_type, cat = val.split("_", 1)
        v = discord.ui.View()
        v.add_item(DevGearItemSelect(cat, store_type))
        await ctx.response.send_message(f"📦 اختر العتاد المحدد من قسم [{cat}] ({'عادي' if store_type == 'gen' else 'ظلال'}):", view=v, ephemeral=True)

class DevGearCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevGearCategorySelect())

class DevGearTakeUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="☠️ اختر اللاعب لسحب العتاد المحرم T25 منه...", min_values=1, max_values=1)

    async def callback(self, ctx: discord.Interaction):
        target = self.values[0]
        t_id = str(target.id)
        if not is_user_registered(t_id):
            await ctx.response.send_message("❌ هذا اللاعب غير مسجل باللعبة!", ephemeral=True)
            return

        u = users_col.find_one({"user_id": t_id}) or {}
        inv = u.get("inventory", [])
        removed_power = 0
        removed_count = 0

        max_dark_items = [it for it in ALL_DARK_ITEMS if it["id"].endswith("_25")]

        for item in max_dark_items:
            while item["name"] in inv:
                inv.remove(item["name"])
                removed_power += item["power"]
                removed_count += 1

        users_col.update_one(
            {"user_id": t_id},
            {
                "$set": {"inventory": inv},
                "$inc": {"power": -removed_power}
            }
        )
        await ctx.response.send_message(
            f"☠️ تم سحب طقم العتاد المحرم (T25) من {target.mention} بنجاح!\n"
            f"• **عدد القطع المسحوبة:** `{removed_count}`\n"
            f"• **القوة المخصومة:** `-{removed_power:,}` ⚡",
            ephemeral=True
        )

class DevGearGiveUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🎁 اختر اللاعب لإهدائه العتاد المحرم الكامل T25...", min_values=1, max_values=1)

    async def callback(self, ctx: discord.Interaction):
        target = self.values[0]
        t_id = str(target.id)
        if not is_user_registered(t_id):
            await ctx.response.send_message("❌ هذا اللاعب غير مسجل باللعبة!", ephemeral=True)
            return

        max_dark_items = [it for it in ALL_DARK_ITEMS if it["id"].endswith("_25")]
        add_names = [it["name"] for it in max_dark_items]
        add_power = sum(it["power"] for it in max_dark_items)

        users_col.update_one(
            {"user_id": t_id},
            {
                "$push": {"inventory": {"$each": add_names}},
                "$inc": {"power": add_power}
            }
        )
        await ctx.response.send_message(
            f"🎁 تم إهداء طقم العتاد المحرم الكامل T25 (8 قطع أسطورية) إلى {target.mention} بنجاح!\n"
            f"• **إجمالي القوة المضافة:** `+{add_power:,}` ⚡",
            ephemeral=True
        )

class DevGearActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="👑 أخذ العتاد لنفسي فوراً", style=discord.ButtonStyle.success, row=0)
    async def self_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        uid = str(ctx.user.id)
        max_dark_items = [it for it in ALL_DARK_ITEMS if it["id"].endswith("_25")]
        add_names = [it["name"] for it in max_dark_items]
        add_power = sum(it["power"] for it in max_dark_items)

        users_col.update_one(
            {"user_id": uid},
            {
                "$push": {"inventory": {"$each": add_names}},
                "$inc": {"power": add_power}
            }
        )
        await ctx.response.send_message(
            f"☠️ **تم تزويدك بطقم العتاد المحرم الكامل (T25) بنجاح!**\n"
            f"• **المعدات المضافة:** (خوذة، درع، بنطال، حذاء، سيف، خنجر، مطرقة، عصا سحرية) T25\n"
            f"• **إجمالي القوة المضافة:** `+{add_power:,}` ⚡",
            ephemeral=True
        )

    @discord.ui.button(label="🎁 إهداء العتاد للاعب", style=discord.ButtonStyle.primary, row=0)
    async def give_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        v = discord.ui.View(timeout=60)
        v.add_item(DevGearGiveUserSelect())
        await ctx.response.send_message("👤 اختر اللاعب المراد إهداؤه الطقم المحرم الكامل (T25):", view=v, ephemeral=True)

    @discord.ui.button(label="☠️ سحب العتاد من لاعب", style=discord.ButtonStyle.danger, row=1)
    async def take_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        v = discord.ui.View(timeout=60)
        v.add_item(DevGearTakeUserSelect())
        await ctx.response.send_message("👤 اختر اللاعب المراد سحب الطقم المحرم T25 منه:", view=v, ephemeral=True)

class DevActionSelectMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="⚡ تطوير بنقرة واحدة (Max All)", value="one_click_max", emoji="🚀", description="رفع جميع المعدلات والخصائص لرقم خيالي أسطوري"),
            discord.SelectOption(label="💀 عتاد المطور المحرم (T25)", value="dev_gear_action", emoji="☠️", description="أخذ/إهداء/سحب طقم العتاد المحرم T25 بالكامل"),
            discord.SelectOption(label="عملات لا نهائية", value="inf", emoji="♾️", description="شحن رصيد عملات لا نهائي لك"),
            discord.SelectOption(label="تفعيل السفاح الخارق", value="assassin", emoji="🩸", description="رفع طاقتك وخصائصك لأقصى حد"),
            discord.SelectOption(label="الحصول على القاب", value="get_title", emoji="👑", description="إضافة وتعيين أي لقب خاص لبروفايلك"),
            discord.SelectOption(label="إهداء عتاد فردي للاعب", value="gift_gear", emoji="🎁", description="إهداء عتاد محدد للاعب بالمنشن"),
            discord.SelectOption(label="تحويل / إهداء عملات", value="transfer", emoji="💸", description="شحن عملات للاعب بالمنشن"),
            discord.SelectOption(label="إضافة مطور", value="add_dev", emoji="🔱", description="منح صلاحية مطور للاعب بالمنشن")
        ]
        super().__init__(placeholder="⚙️ اختر إجراء المطور الخارق...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        if not is_dev(ctx.user.id):
            await ctx.response.send_message("❌ لست مطوراً!", ephemeral=True)
            return
        uid = str(ctx.user.id)
        v = self.values[0]

        if v == "dev_gear_action":
            emb_gear = discord.Embed(
                title="☠️ │ إدارة عتاد المطور المحرم (T25)",
                description=(
                    "يتضمن هذا الطقم العتاد المحرم الأعلى بالمستوى T25 لجميع الأقسام الـ 8:\n"
                    "• ☠️ **خوذة** [حاكم الظلمات] T25\n"
                    "• ☠️ **درع** [حاكم الظلمات] T25\n"
                    "• ☠️ **بنطال** [حاكم الظلمات] T25\n"
                    "• ☠️ **حذاء** [حاكم الظلمات] T25\n"
                    "• ☠️ **سيف** [حاكم الظلمات] T25\n"
                    "• ☠️ **خنجر** [حاكم الظلمات] T25\n"
                    "• ☠️ **مطرقة** [حاكم الظلمات] T25\n"
                    "• ☠️ **عصا سحرية** [حاكم الظلمات] T25\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "اختر الإجراء المطلوب من الأزرار بالأسفل:"
                ),
                color=discord.Color.purple()
            )
            await ctx.response.send_message(embed=emb_gear, view=DevGearActionView(), ephemeral=True)

        elif v == "one_click_max":
            max_val = 999999999999999
            st = {
                "power": max_val, "balance": max_val, "bank": max_val, "diamonds": max_val,
                "attack": max_val, "defense": max_val, "magic": max_val, "aim": max_val,
                "evasion": max_val, "accuracy": max_val, "critical": max_val, "intelligence": max_val,
                "max_floor": 500, "kills": 999999
            }
            u = users_col.find_one({"user_id": uid}) or {}
            if u.get("chosen_hero"):
                for k in HERO_STATS_CFG.keys():
                    st[f"hero_stats.{k}"] = max_val

            users_col.update_one({"user_id": uid}, {"$set": st})

            emb_res = discord.Embed(
                title="🚀 │ تم التطوير الخارق بنقرة واحدة!",
                description=(
                    "💥 **تم رفع جميع المعدلات إلى الحدود الإلهية الخيالية!**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ **القوة والخصائص:** `999,999,999,999,999`\n"
                    f"🪙 **الذهب والكاش:** `999,999,999,999,999`\n"
                    f"💎 **الألماس الملكي:** `999,999,999,999,999`\n"
                    f"🦸‍♂️ **معدلات البطل:** مكسورة لأقصى حد!\n"
                    f"🏰 **برج الطوابق:** تم فتح الطابق `500` بالكامل!"
                ),
                color=discord.Color.gold()
            )
            await ctx.response.send_message(embed=emb_res, ephemeral=True)

        elif v == "inf":
            users_col.update_one({"user_id": uid}, {"$set": {"balance": 999999999999, "diamonds": 999999999}})
            await ctx.response.send_message("♾️ تم شحن عملات لا نهائية لحسابك!", ephemeral=True)

        elif v == "assassin":
            st = {"power": 999999999999, "balance": 999999999999, "diamonds": 999999999, "attack": 999999999, "defense": 999999999}
            users_col.update_one({"user_id": uid}, {"$set": st})
            await ctx.response.send_message("🩸 تم تفعيل شخصية السفاح الخارقة!", ephemeral=True)

        elif v == "get_title":
            await ctx.response.send_modal(DevTitleModal())

        elif v == "gift_gear":
            await ctx.response.send_message("🎁 اختر القسم والنوع للعتاد المراد إهداؤه:", view=DevGearCategoryView(), ephemeral=True)

        elif v == "transfer":
            await ctx.response.send_message("👤 اختر اللاعب الذي تريد شحن/إهداء العملات له:", view=DevTransferUserView(), ephemeral=True)

        elif v == "add_dev":
            if uid != MAIN_DEV_ID:
                await ctx.response.send_message("❌ إضافة المطورين مقتصرة على المطور الرئيسي فقط!", ephemeral=True)
                return
            await ctx.response.send_message("👤 اختر العضو المراد ترقيته إلى مطور:", view=DevAddUserView(), ephemeral=True)

class DevPanelView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DevActionSelectMenu())

# ==================== كلاسات المصرف والنقابات ====================

class BankDepositModal(discord.ui.Modal, title="📥 إيداع في البنك"):
    amount_in = discord.ui.TextInput(label="المبلغ المراد إيداعه", placeholder="مثال: 1000")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if amt <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < amt:
            await ctx.response.send_message("❌ لا تملك هذا المبلغ في كاشك!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -amt, "bank": amt}})
        await ctx.response.send_message(f"🏦 تم إيداع `{amt:,}` 🪙 في بنكك بنجاح!", ephemeral=True)

class BankWithdrawModal(discord.ui.Modal, title="📤 سحب من البنك"):
    amount_in = discord.ui.TextInput(label="المبلغ المراد سحبه", placeholder="مثال: 1000")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if amt <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("bank", 0) < amt:
            await ctx.response.send_message("❌ لا تملك هذا المبلغ في البنك!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"bank": -amt, "balance": amt}})
        await ctx.response.send_message(f"💵 تم سحب `{amt:,}` 🪙 من البنك إلى كاشك بنجاح!", ephemeral=True)

class TakeLoanModal(discord.ui.Modal, title="💳 طلب قرض إمبراطوري"):
    amount_in = discord.ui.TextInput(label="قيمة القرض (الأقصى 50,000 🪙)", placeholder="مثال: 20000")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if not (1 <= amt <= 50000): raise ValueError()
        except:
            await ctx.response.send_message("❌ المبلغ يجب أن يكون رقماً بين 1 و 50,000 🪙!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("loan", 0) > 0:
            await ctx.response.send_message(f"❌ عليك قرض سابق بـ `{u.get('loan'):,}` 🪙، يجب سداده أولاً!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": amt}, "$set": {"loan": amt}})
        await ctx.response.send_message(f"💳 تم منحك القرض بنجاح بمبلغ `{amt:,}` 🪙! أضيفت إلى حسابك.", ephemeral=True)

class TransferAmountModal(discord.ui.Modal):
    def __init__(self, target_user: discord.User):
        super().__init__(title=f"💸 تحويل إلى {target_user.display_name[:15]}")
        self.target_user = target_user
        self.amount_in = discord.ui.TextInput(label="المبلغ المراد تحويله (🪙)", placeholder="مثال: 5000")
        self.add_item(self.amount_in)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if amt <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً أكبـر من 0!", ephemeral=True)
            return

        if self.target_user.id == ctx.user.id:
            await ctx.response.send_message("❌ لا يمكنك التحويل لنفسك!", ephemeral=True)
            return

        if not is_user_registered(self.target_user.id):
            await ctx.response.send_message("❌ هذا العضو غير مسجل باللعبة!", ephemeral=True)
            return

        uid, t_id = str(ctx.user.id), str(self.target_user.id)
        u = users_col.find_one({"user_id": uid}) or {}

        if u.get("balance", 0) < amt:
            await ctx.response.send_message("❌ لا تملك هذا القدر من الذهب في كاشك!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -amt}})
        users_col.update_one({"user_id": t_id}, {"$inc": {"balance": amt}})
        await ctx.response.send_message(f"💸 تم تحويل `{amt:,}` 🪙 بنجاح إلى المقاتل {self.target_user.mention}!")

class BankTransferUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="👤 اختر العضو الذي تريد التحويل له بالمنشن...", min_values=1, max_values=1)

    async def callback(self, ctx: discord.Interaction):
        selected_user = self.values[0]
        await ctx.response.send_modal(TransferAmountModal(selected_user))

class BankTransferSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(BankTransferUserSelect())

class BankExchangeModal(discord.ui.Modal, title="💎 صرافة الألماس الإمبراطورية"):
    gold_in = discord.ui.TextInput(label="كمية الذهب للتحويل إلى ألماس (10,000 🪙 = 1 💎)", placeholder="مثال: 50000")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.gold_in.value.strip())
            if amt < 10000: raise ValueError()
        except:
            await ctx.response.send_message("❌ الحد الأدنى للتحويل هو 10,000 🪙!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < amt:
            await ctx.response.send_message("❌ لا تملك هذا القدر من الذهب في الكاش!", ephemeral=True)
            return

        d_gained = amt // 10000
        used_gold = d_gained * 10000

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -used_gold, "diamonds": d_gained}})
        await ctx.response.send_message(f"💎 تم تحويل `{used_gold:,}` 🪙 إلى `+{d_gained:,}` 💎 ألماس ملكي بنجاح!", ephemeral=True)

class BankInvestModal(discord.ui.Modal, title="📈 الاستثمار الملكي السريع"):
    amount_in = discord.ui.TextInput(label="المبلغ المراد استثماره في الأسهم", placeholder="مثال: 20000")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amount_in.value.strip())
            if amt < 1000: raise ValueError()
        except:
            await ctx.response.send_message("❌ الحد الأدنى للاستثمار هو 1,000 🪙!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < amt:
            await ctx.response.send_message("❌ لا تملك هذا المبلغ بالرصيد المباشر!", ephemeral=True)
            return

        roll = random.random()
        if roll > 0.15:
            profit_pct = random.randint(15, 45)
            gain = int(amt * (profit_pct / 100))
            users_col.update_one({"user_id": uid}, {"$inc": {"balance": gain}})
            await ctx.response.send_message(f"📈 **نجح استثمارك!** ارتفعت أسهم الإمبراطورية بـ `{profit_pct}%`!\n🎉 الأرباح الصافية: `+{gain:,}` 🪙 ذهب!", ephemeral=True)
        else:
            loss_pct = random.randint(5, 12)
            loss = int(amt * (loss_pct / 100))
            users_col.update_one({"user_id": uid}, {"$inc": {"balance": -loss}})
            await ctx.response.send_message(f"📉 **تراجعت السوق!** خسرت `{loss_pct}%` من استثمارك.\n💸 الخسارة: `-{loss:,}` 🪙 ذهب.", ephemeral=True)

class ImperialBankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 الراتب اليومي", style=discord.ButtonStyle.success, row=0)
    async def daily_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        last_d = u.get("last_daily")
        now = datetime.now(timezone.utc)

        if last_d and (now - last_d.replace(tzinfo=timezone.utc if last_d.tzinfo is None else last_d.tzinfo)).total_seconds() < 86400:
            rem_sec = int(86400 - (now - last_d.replace(tzinfo=timezone.utc if last_d.tzinfo is None else last_d.tzinfo)).total_seconds())
            hrs, mins = rem_sec // 3600, (rem_sec % 3600) // 60
            await ctx.response.send_message(f"⏳ أخذت راتبك اليومي! يمكنك الاستلام بعد: `{hrs}` ساعة و `{mins}` دقيقة.", ephemeral=True)
            return

        gold_reward, dia_reward = 3000, 5
        users_col.update_one({"user_id": uid}, {"$inc": {"balance": gold_reward, "diamonds": dia_reward}, "$set": {"last_daily": now}})
        await ctx.response.send_message(f"🎉 تم استلام الراتب اليومي الإمبراطوري!\n🪙 +`{gold_reward:,}` ذهب | 💎 +`{dia_reward}` ألماس", ephemeral=True)

    @discord.ui.button(label="💳 طلب قرض", style=discord.ButtonStyle.primary, row=0)
    async def loan_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(TakeLoanModal())

    @discord.ui.button(label="⚖️ سداد القرض", style=discord.ButtonStyle.secondary, row=0)
    async def repay_loan_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        loan = u.get("loan", 0)

        if loan <= 0:
            await ctx.response.send_message("✨ لا تجب عليك أي ديون أو قروض حالياً!", ephemeral=True)
            return

        if u.get("balance", 0) < loan:
            await ctx.response.send_message(f"❌ تحتاج إلى `{loan:,}` 🪙 في الكاش لسداد القرض!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -loan}, "$set": {"loan": 0}})
        await ctx.response.send_message(f"🎉 تم سداد القرض بالكامل بمبلغ `{loan:,}` 🪙! أصبحت خالي الديون.", ephemeral=True)

    @discord.ui.button(label="📥 إيداع", style=discord.ButtonStyle.secondary, row=1)
    async def deposit_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankDepositModal())

    @discord.ui.button(label="📤 سحب", style=discord.ButtonStyle.secondary, row=1)
    async def withdraw_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankWithdrawModal())

    @discord.ui.button(label="💸 تحويل بالمنشن", style=discord.ButtonStyle.danger, row=1)
    async def transfer_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_message("👤 اختر العضو المراد التحويل له من القائمة:", view=BankTransferSelectView(), ephemeral=True)

    @discord.ui.button(label="💎 صرافة الألماس", style=discord.ButtonStyle.primary, row=2)
    async def exchange_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankExchangeModal())

    @discord.ui.button(label="📈 الاستثمار الملكي", style=discord.ButtonStyle.success, row=2)
    async def invest_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankInvestModal())

class CreateGuildModal(discord.ui.Modal, title="🏰 تأسيس نقابة إمبراطورية جديدة"):
    guild_name_in = discord.ui.TextInput(label="اسم النقابة", placeholder="اكتب اسم النقابة العظيم...", min_length=3, max_length=30)

    async def on_submit(self, ctx: discord.Interaction):
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}

        if u.get("guild_id"):
            await ctx.response.send_message("❌ أنت تنتمي لنقابة بالفعل! يجب عليك مغادرتها أولاً لتأسيس نقابة جديدة.", ephemeral=True)
            return

        if u.get("balance", 0) < 400:
            await ctx.response.send_message("❌ رسوم تأسيس النقابة هي `400` 🪙 عملة عادية وغير متوفرة في كاشك!", ephemeral=True)
            return

        g_name = self.guild_name_in.value.strip()
        if guilds_col.find_one({"name": g_name}):
            await ctx.response.send_message("❌ اسم النقابة هذا مستخدم بالفعل من قبل حلف آخر! اختر اسماً آخر.", ephemeral=True)
            return

        g_doc = {
            "name": g_name,
            "leader_id": uid,
            "members": [uid],
            "balance": 0,
            "diamonds": 0,
            "power": u.get("power", 100),
            "is_open": True,
            "gear_vault": [],
            "created_at": datetime.now(timezone.utc)
        }
        res = guilds_col.insert_one(g_doc)
        g_id = str(res.inserted_id)
        guilds_col.update_one({"_id": res.inserted_id}, {"$set": {"guild_id": g_id}})

        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -400}, "$set": {"guild_id": g_id}})

        emb = discord.Embed(
            title="🏰 تم تأسيس النقابة بنجاح!",
            description=f"🎉 تهانينا للقائد {ctx.user.mention} على رفع راية **[ {g_name} ]** العظيمة!\n• **رسوم التأسيس:** `400` 🪙 ذهب\n• يمكنك الآن إدارة نقابتك، التبرع بها، ودعوة الأعضاء عبر أمر `/نقابتي`.",
            color=discord.Color.gold()
        )
        await ctx.response.send_message(embed=emb)

class GuildJoinSelect(discord.ui.Select):
    def __init__(self, open_guilds: list):
        opts = []
        for g in open_guilds[:25]:
            opts.append(discord.SelectOption(
                label=g["name"],
                value=g["guild_id"],
                description=f"⚡ القوة: {g.get('power',0):,} | 👥 الأعضاء: {len(g.get('members',[]))}",
                emoji="🏰"
            ))
        super().__init__(placeholder="🤝 اختر نقابة مفتوحة للانضمام إليها...", options=opts if opts else [discord.SelectOption(label="لا توجد نقابات مفتوحة حالياً", value="none")])

    async def callback(self, ctx: discord.Interaction):
        if self.values[0] == "none":
            await ctx.response.send_message("❌ لا توجد نقابات متاحة للانضمام حالياً.", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("guild_id"):
            await ctx.response.send_message("❌ أنت تنتمي لنقابة بالفعل!", ephemeral=True)
            return

        g_id = self.values[0]
        g = guilds_col.find_one({"guild_id": g_id})

        if not g or not g.get("is_open", True):
            await ctx.response.send_message("❌ هذه النقابة مغلقة أمام الانضمام حالياً بقرار من القائد!", ephemeral=True)
            return

        guilds_col.update_one(
            {"guild_id": g_id},
            {
                "$push": {"members": uid},
                "$inc": {"power": u.get("power", 100)}
            }
        )
        users_col.update_one({"user_id": uid}, {"$set": {"guild_id": g_id}})

        await ctx.response.send_message(f"🎉 مرحباً بك في الصفوف! تم انضمامك بنجاح إلى نقابة **[ {g['name']} ]**.")

class GuildsListView(discord.ui.View):
    def __init__(self, open_guilds: list):
        super().__init__(timeout=60)
        self.add_item(GuildJoinSelect(open_guilds))

class GuildDonateCurrencyModal(discord.ui.Modal, title="🪙/💎 التبرع بـ العملات للنقابة"):
    amt_in = discord.ui.TextInput(label="المبلغ المراد التبرع به", placeholder="مثال: 5000")
    curr_in = discord.ui.TextInput(label="نوع العملة (اكتب: ذهب أو ألماس)", placeholder="ذهب / ألماس", default="ذهب")

    async def on_submit(self, ctx: discord.Interaction):
        try:
            amt = int(self.amt_in.value.strip())
            if amt <= 0: raise ValueError()
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        g_id = u.get("guild_id")

        if not g_id:
            await ctx.response.send_message("❌ أنت لست عضواً في أي نقابة!", ephemeral=True)
            return

        curr_type = self.curr_in.value.strip()
        is_dia = ("ألم" in curr_type or "الم" in curr_type or "dia" in curr_type.lower())
        field = "diamonds" if is_dia else "balance"
        sym = "💎" if is_dia else "🪙"

        if u.get(field, 0) < amt:
            await ctx.response.send_message(f"❌ لا تملك هذا القدر من الـ {sym} في حسابك الشخصي!", ephemeral=True)
            return

        users_col.update_one({"user_id": uid}, {"$inc": {field: -amt}})
        guilds_col.update_one({"guild_id": g_id}, {"$inc": {field: amt}})

        await ctx.response.send_message(f"🎁 تم التبرع بـ `{amt:,}` {sym} لخزنة النقابة! شكراً لدعمك العظيم لحلفك.", ephemeral=True)

class GuildDonateGearSelect(discord.ui.Select):
    def __init__(self, inv_items: list):
        counts = {}
        for it in inv_items:
            counts[it] = counts.get(it, 0) + 1

        opts = [
            discord.SelectOption(label=f"{item_name} (x{count})", value=item_name, emoji="🛡️")
            for item_name, count in counts.items()
        ][:25]

        super().__init__(placeholder="🎒 اختر قطعة عتاد للتبرع بها للنقابة...", options=opts if opts else [discord.SelectOption(label="حقيبتك فارغة", value="none")])

    async def callback(self, ctx: discord.Interaction):
        if self.values[0] == "none":
            await ctx.response.send_message("❌ لا تملك عتاداً للتبرع به!", ephemeral=True)
            return

        item_name = self.values[0]
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        g_id = u.get("guild_id")

        inv = u.get("inventory", [])
        if item_name not in inv:
            await ctx.response.send_message("❌ القطعة غير متوفرة بحقيبتك!", ephemeral=True)
            return

        item_pow = GEN_ITEM_POWER_MAP.get(item_name, DARK_ITEM_POWER_MAP.get(item_name, 100))

        inv.remove(item_name)
        users_col.update_one({"user_id": uid}, {"$set": {"inventory": inv}})

        guilds_col.update_one(
            {"guild_id": g_id},
            {
                "$push": {"gear_vault": item_name},
                "$inc": {"power": item_pow}
            }
        )

        await ctx.response.send_message(f"⚔️ تم التبرع بـ **{item_name}** لخزنة النقابة!\n• تم إضافة `+{item_pow:,}` ⚡ لقوة النقابة الإجمالية.", ephemeral=True)

class GuildDonateGearView(discord.ui.View):
    def __init__(self, inv_items: list):
        super().__init__(timeout=60)
        self.add_item(GuildDonateGearSelect(inv_items))

class MyGuildView(discord.ui.View):
    def __init__(self, is_open: bool):
        super().__init__(timeout=None)

        toggle_label = "🔒 إغلاق الانضمام" if is_open else "🔓 فتح الانضمام"
        toggle_style = discord.ButtonStyle.danger if is_open else discord.ButtonStyle.success

        self.add_item(discord.ui.Button(label="🎁 التبرع بالعتاد", style=discord.ButtonStyle.success, custom_id="btn_donate_gear", row=0))
        self.add_item(discord.ui.Button(label="🪙/💎 التبرع بالعملات", style=discord.ButtonStyle.primary, custom_id="btn_donate_curr", row=0))
        self.add_item(discord.ui.Button(label=toggle_label, style=toggle_style, custom_id="btn_toggle_join", row=1))

    async def interaction_check(self, ctx: discord.Interaction) -> bool:
        custom_id = ctx.data.get("custom_id")
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        g_id = u.get("guild_id")

        if not g_id:
            await ctx.response.send_message("❌ أنت لست في هذه النقابة!", ephemeral=True)
            return False

        if custom_id == "btn_donate_gear":
            inv = u.get("inventory", [])
            if not inv:
                await ctx.response.send_message("❌ حقيبتك فارغة، لا يوجد عتاد للتبرع به!", ephemeral=True)
                return False
            await ctx.response.send_message("🎒 اختر القطعة المراد التبرع بها للنقابة:", view=GuildDonateGearView(inv), ephemeral=True)

        elif custom_id == "btn_donate_curr":
            await ctx.response.send_modal(GuildDonateCurrencyModal())

        elif custom_id == "btn_toggle_join":
            g = guilds_col.find_one({"guild_id": g_id})
            if not g or str(g.get("leader_id")) != uid:
                await ctx.response.send_message("❌ تغيير حالة الانضمام مقتصر على قائد النقابة فقط!", ephemeral=True)
                return False

            new_state = not g.get("is_open", True)
            guilds_col.update_one({"guild_id": g_id}, {"$set": {"is_open": new_state}})
            state_txt = "🔓 مفتوح للجميع" if new_state else "🔒 مغلق الآن"
            await ctx.response.send_message(f"⚙️ تم تغيير حالة الانضمام للنقابة إلى: **{state_txt}**!", ephemeral=True)

        return True

# ==================== كلاسات أنظمة الألعاب المنسقة ====================

class StopGameView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        ACTIVE_GAMES[self.channel_id] = False
        await ctx.response.send_message("🛑 تم إيقاف اللعبة التلقائية بنجاح!", ephemeral=False)

class GamesLeaderboardSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="أبطال الألعاب الشامل", value="total", emoji="🏆"),
            discord.SelectOption(label="أبطال الألغاز", value="riddles", emoji="🧩"),
            discord.SelectOption(label="أبطال الرياضيات", value="math", emoji="🧮"),
            discord.SelectOption(label="أبطال خمن الأنمي", value="anime", emoji="🎌"),
            discord.SelectOption(label="أبطال أسرع", value="fastest", emoji="⚡"),
            discord.SelectOption(label="أبطال فكك", value="deconstruct", emoji="🔤"),
            discord.SelectOption(label="أبطال إكس أوه", value="xo", emoji="❌")
        ]
        super().__init__(placeholder="🏆 اختر ليدربورد الألعاب...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        all_u = list(users_col.find({"game_score": {"$exists": True}}))

        def get_score(u):
            gs = u.get("game_score", {})
            return gs.get(v, 0) if isinstance(gs, dict) else 0

        all_u.sort(key=get_score, reverse=True)

        txt_lines = []
        for idx, u in enumerate(all_u[:10]):
            score = get_score(u)
            if score > 0:
                txt_lines.append(f"#{idx+1} **{u.get('name','لاعب')}** — `{score:,}` نقطة 🏅")

        txt = "\n".join(txt_lines) if txt_lines else "لا يوجد متصدرين مسجلين في هذا التصنيف بعد!"

        emb = discord.Embed(
            title=f"🏆 │ ليدربورد الألعاب — [{self.values[0].upper()}]",
            description=txt,
            color=discord.Color.gold()
        )
        vw = discord.ui.View()
        vw.add_item(GamesLeaderboardSelect())
        await ctx.response.edit_message(embed=emb, view=vw)

# ==================== كلاسات لعبة إكس أوه (Tic-Tac-Toe) ====================

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, ctx: discord.Interaction):
        view: TicTacToeView = self.view

        if ctx.user.id != view.current_player.id:
            await ctx.response.send_message("❌ ليس دورك الآن في اللعب!", ephemeral=True)
            return

        idx = self.y * 3 + self.x
        if view.board[idx] is not None or view.winner is not None:
            await ctx.response.send_message("❌ المكان اختير بالفعل أو اللعبة انتهت!", ephemeral=True)
            return

        symbol = "❌" if view.current_player == view.p1 else "⭕"
        self.label = symbol
        self.style = discord.ButtonStyle.danger if symbol == "❌" else discord.ButtonStyle.primary
        self.disabled = True
        view.board[idx] = symbol

        winner_symbol = view.check_winner()
        if winner_symbol:
            view.winner = view.current_player
            add_game_win(view.winner.id, "xo")
            view.disable_all_board()
            emb = discord.Embed(
                title="❌⭕ │ لعبة إكس أوه (Tic-Tac-Toe)",
                description=f"🎉 **مبروك الانتصار!**\nفاز المقاتل {view.winner.mention} ({winner_symbol}) بمهارة عالية! 🏆",
                color=discord.Color.gold()
            )
            await ctx.response.edit_message(embed=emb, view=view)
            return

        if None not in view.board:
            view.disable_all_board()
            emb = discord.Embed(
                title="❌⭕ │ لعبة إكس أوه (Tic-Tac-Toe)",
                description="🤝 **تعادل أسطوري!** خاض الطرفان معركة متكافئة وانتهت بدون فائز.",
                color=discord.Color.blue()
            )
            await ctx.response.edit_message(embed=emb, view=view)
            return

        view.current_player = view.p2 if view.current_player == view.p1 else view.p1
        emb = discord.Embed(
            title="❌⭕ │ لعبة إكس أوه (Tic-Tac-Toe)",
            description=f"🎮 **التحدي مستمر!**\n• {view.p1.mention} (❌) **ضد** {view.p2.mention} (⭕)\n• **الدور الآن على:** {view.current_player.mention}",
            color=discord.Color.gold()
        )
        await ctx.response.edit_message(embed=emb, view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, p1: discord.User, p2: discord.User):
        super().__init__(timeout=None)
        self.p1 = p1
        self.p2 = p2
        self.current_player = p1
        self.board = [None] * 9
        self.winner = None

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

        restart_btn = discord.ui.Button(label="🔄 إعادة الجولة", style=discord.ButtonStyle.success, row=3)
        stop_btn = discord.ui.Button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.danger, row=3)

        restart_btn.callback = self.restart_cb
        stop_btn.callback = self.stop_cb

        self.add_item(restart_btn)
        self.add_item(stop_btn)

    def disable_all_board(self):
        for item in self.children:
            if isinstance(item, TicTacToeButton):
                item.disabled = True

    def check_winner(self):
        b = self.board
        wins = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        for x, y, z in wins:
            if b[x] and b[x] == b[y] == b[z]:
                return b[x]
        return None

    async def restart_cb(self, ctx: discord.Interaction):
        if ctx.user.id not in [self.p1.id, self.p2.id]:
            await ctx.response.send_message("❌ إعادة الجولة مقتصرة على اللاعبين المشاركين فقط!", ephemeral=True)
            return

        new_view = TicTacToeView(self.p1, self.p2)
        emb = discord.Embed(
            title="❌⭕ │ جولة جديدة في لعبة إكس أوه!",
            description=f"🎮 **بدأت جولة جديدة!**\n• {self.p1.mention} (❌) **ضد** {self.p2.mention} (⭕)\n• **الدور الأول على:** {self.p1.mention}",
            color=discord.Color.gold()
        )
        await ctx.response.send_message(embed=emb, view=new_view)

    async def stop_cb(self, ctx: discord.Interaction):
        if ctx.user.id not in [self.p1.id, self.p2.id]:
            await ctx.response.send_message("❌ إيقاف اللعبة مقتصر على اللاعبين المشاركين فقط!", ephemeral=True)
            return

        self.disable_all_board()
        emb = discord.Embed(
            title="❌⭕ │ تم إيقاف لعبة إكس أوه",
            description=f"🛑 تم إيقاف اللعبة بطلب من المقاتل {ctx.user.mention}.",
            color=discord.Color.red()
        )
        await ctx.response.edit_message(embed=emb, view=self)

class TicTacToeChallengeView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=60)
        self.host = host

    @discord.ui.button(label="⚔️ قبول التحدي والدخول كمنافس", style=discord.ButtonStyle.success)
    async def join_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        if ctx.user.id == self.host.id:
            await ctx.response.send_message("❌ لا يمكنك الانضمام والتحدي ضد نفسك!", ephemeral=True)
            return

        p1 = self.host
        p2 = ctx.user

        xo_view = TicTacToeView(p1, p2)
        emb = discord.Embed(
            title="❌⭕ │ مواجهة إكس أوه (Tic-Tac-Toe)",
            description=f"⚔️ **بدأت المعركة!**\n• {p1.mention} (❌) **ضد** {p2.mention} (⭕)\n• **الدور الأول على:** {p1.mention}",
            color=discord.Color.gold()
        )
        await ctx.response.edit_message(content=None, embed=emb, view=xo_view)

# ==================== باقي أطقم كلاسات الألعاب ====================

class QuestionsGameView(discord.ui.View):
    def __init__(self, channel_id: int, level: str, players: list):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.level = level
        self.players = players

    @discord.ui.button(label="💥 طلب عقاب", style=discord.ButtonStyle.danger, row=0)
    async def punish_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        p = random.choice(PUNISHMENTS_DATA.get(self.level, PUNISHMENTS_DATA["normal"]))
        await ctx.response.send_message(f"💥 **العقاب المستحق:**\n`{p}`", ephemeral=False)

    @discord.ui.button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.secondary, row=0)
    async def stop_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        ACTIVE_GAMES[self.channel_id] = False
        await ctx.response.send_message("🛑 تم إيقاف جلسة الأسئلة بنجاح.", ephemeral=False)

    async def start_loop(self, initial_msg):
        msg = initial_msg
        while ACTIVE_GAMES.get(self.channel_id, False):
            await asyncio.sleep(15)
            if not ACTIVE_GAMES.get(self.channel_id, False): break

            target_player = random.choice(self.players)
            question = random.choice(QUESTIONS_DATA.get(self.level, QUESTIONS_DATA["normal"]))

            emb = discord.Embed(
                title=f"🎲 │ لعبة الأسئلة والجريئة — [{self.level.upper()}]",
                description=(
                    f"🎲 **جاري تدوير النرد لاختيار الضحية...**\n"
                    f"🎯 **الدور على:** {target_player.mention}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❓ **السؤال:**\n`{question}`\n"
                    f"⏱️ **سيتغير السؤال واللاعب تلقائياً خلال 15 ثانية!**"
                ),
                color=discord.Color.red() if self.level == "bold" else discord.Color.gold()
            )
            try:
                await msg.edit(embed=emb, view=self)
            except:
                break

class QuestionsLevelSelect(discord.ui.Select):
    def __init__(self, players: list):
        self.players = players
        opts = [
            discord.SelectOption(label="المستوى العادي", value="normal", emoji="🟢", description="أسئلة خفيفة وممتعة"),
            discord.SelectOption(label="المستوى المتوسط", value="medium", emoji="🟡", description="أسئلة شخصية وتحديات"),
            discord.SelectOption(label="المستوى الجريء جداً", value="bold", emoji="🔴", description="أسئلة صريحة وقوية")
        ]
        super().__init__(placeholder="🎯 اختر مستوى صراحة الأسئلة...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        level = self.values[0]
        cid = ctx.channel.id
        ACTIVE_GAMES[cid] = True

        target_player = random.choice(self.players)
        question = random.choice(QUESTIONS_DATA[level])

        emb = discord.Embed(
            title=f"🎲 │ بداية لعبة الأسئلة والجريئة — [{level.upper()}]",
            description=(
                f"🎲 **جاري تدوير النرد لاختيار الضحية...**\n"
                f"🎯 **الدور الأول على:** {target_player.mention}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❓ **السؤال:**\n`{question}`\n"
                f"⏱️ **سيتغير السؤال واللاعب تلقائياً خلال 15 ثانية!**"
            ),
            color=discord.Color.gold()
        )

        game_view = QuestionsGameView(cid, level, self.players)
        await ctx.response.send_message(embed=emb, view=game_view)
        msg = await ctx.original_response()
        asyncio.create_task(game_view.start_loop(msg))

class SpyGuessSelect(discord.ui.Select):
    def __init__(self, spy_user: discord.User, correct_word: str, words_options: list):
        self.spy_user = spy_user
        self.correct_word = correct_word
        opts = [discord.SelectOption(label=w, value=w) for w in words_options]
        super().__init__(placeholder="🕵️‍♂️ اختر الكلمة التي تعتقد أنها الكلمة السرية...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id != self.spy_user.id:
            await ctx.response.send_message("❌ هذا الخيار للجاسوس فقط!", ephemeral=True)
            return

        choice = self.values[0]
        if choice == self.correct_word:
            await ctx.response.send_message(f"🎉 **ذكاء أسطوري!** تمكن الجاسوس {self.spy_user.mention} من تخمين الكلمة الصحيحة **[{self.correct_word}]** وفاز باللعبة! 🕵️‍♂️🔥")
        else:
            await ctx.response.send_message(f"💀 **هزيمة الجاسوس!** خمن الجاسوس {self.spy_user.mention} الكلمة الخاطئة `[{choice}]`!\nالكلمة الصحيحة كانت **[{self.correct_word}]**. انتصر المواطنون! 🏰")

class SpyVoteSelect(discord.ui.Select):
    def __init__(self, players: list, spy_user: discord.User, correct_word: str, similar_words: list):
        self.players = players
        self.spy_user = spy_user
        self.correct_word = correct_word
        self.similar_words = similar_words
        self.votes = {}

        opts = [discord.SelectOption(label=p.display_name, value=str(p.id), emoji="👤") for p in players]
        super().__init__(placeholder="🗳️ صوّت للشخص المشتبه به كجاسوس...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        voter_id = str(ctx.user.id)
        target_id = self.values[0]
        self.votes[voter_id] = target_id

        await ctx.response.send_message(f"✅ تم تسجيل تصويتك ضد <@{target_id}>!", ephemeral=True)

        if len(self.votes) >= len(self.players):
            counts = {}
            for t in self.votes.values():
                counts[t] = counts.get(t, 0) + 1
            most_voted_id = max(counts, key=counts.get)

            if most_voted_id == str(self.spy_user.id):
                emb_spy = discord.Embed(
                    title="🕵️‍♂️ │ كشف الجاسوس!",
                    description=(
                        f"🎯 **نجح المواطنون في كشف الجاسوس الحقيقي {self.spy_user.mention}!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"❓ **الفرصة الأخيرة للجاسوس:** اختر الكلمة السرية الصحيحة من المنيو بالأسفل لتنقذ نفسك وتفوز!"
                    ),
                    color=discord.Color.red()
                )
                words_opts = self.similar_words.copy()
                if self.correct_word not in words_opts:
                    words_opts[0] = self.correct_word
                random.shuffle(words_opts)

                vw = discord.ui.View()
                vw.add_item(SpyGuessSelect(self.spy_user, self.correct_word, words_opts))
                await ctx.channel.send(embed=emb_spy, view=vw)
            else:
                await ctx.channel.send(f"💀 **خطأ قاتل!** تم طرد المقاتل البريء <@{most_voted_id}>!\n🎉 **فاز الجاسوس المخادع {self.spy_user.mention} بالمعركة!** الكلمة كانت: `[{self.correct_word}]`")

class CutTweetLoopView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.agree = 0
        self.disagree = 0

    @discord.ui.button(label="👍 مـع", style=discord.ButtonStyle.success, row=0)
    async def agree_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        self.agree += 1
        tot = self.agree + self.disagree
        await ctx.response.send_message(f"✅ تصويتك: **مـع**! (النسبة حالياً: `{int(self.agree/tot*100)}%` مـع | `{int(self.disagree/tot*100)}%` ضـد)", ephemeral=True)

    @discord.ui.button(label="👎 ضـد", style=discord.ButtonStyle.danger, row=0)
    async def disagree_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        self.disagree += 1
        tot = self.agree + self.disagree
        await ctx.response.send_message(f"❌ تصويتك: **ضـد**! (النسبة حالياً: `{int(self.agree/tot*100)}%` مـع | `{int(self.disagree/tot*100)}%` ضـد)", ephemeral=True)

    @discord.ui.button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.secondary, row=1)
    async def stop_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        ACTIVE_GAMES[self.channel_id] = False
        await ctx.response.send_message("🛑 تم إيقاف لعبة كت تويت التلقائية بنجاح!", ephemeral=False)

class MainGamesSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="لعبة الأسئلة والجريئة", value="q_game", emoji="🎲", description="3 مستويات + 50 سؤال وعقاب لكل مستوى"),
            discord.SelectOption(label="لعبة الألغاز", value="riddle_game", emoji="🧩", description="150 لغز متدرج الصعوبة (تلقائي)"),
            discord.SelectOption(label="لعبة الجواسيس (Spyfall)", value="spy_game", emoji="🕵️‍♂️", description="3+ لاعبين + تصويت وتخمين"),
            discord.SelectOption(label="لعبة الرياضيات", value="math_game", emoji="🧮", description="معادلات سريعة ومؤقت 15 ثانية (تلقائي)"),
            discord.SelectOption(label="لعبة خمن الأنمي", value="anime_game", emoji="🎌", description="أنميات متنوعة كلاسيكية وحديثة (تلقائي)"),
            discord.SelectOption(label="لعبة كت تويت", value="cut_tweet", emoji="💬", description="تغريدات ونقاشات مع أم ضد (تلقائي)"),
            discord.SelectOption(label="لعبة فكّك", value="deconstruct", emoji="🔤", description="تفكيك الكلمات بالحروف ومؤقت 15s (تلقائي)"),
            discord.SelectOption(label="لعبة أسرع", value="fastest", emoji="⚡", description="كتابة الكلمات السريعة بالعربية (تلقائي)"),
            discord.SelectOption(label="لعبة إكس أوه (Tic-Tac-Toe)", value="xo_game", emoji="❌", description="تحدي لشخصين في XO مع زر إيقاف وإعادة")
        ]
        super().__init__(placeholder="🎮 اختر اللعبة المطلوبة لبدء المرح...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        cid = ctx.channel.id

        if v == "xo_game":
            emb_invite = discord.Embed(
                title="❌⭕ │ تحدي إكس أوه (Tic-Tac-Toe)",
                description=f"👑 أطلق **{ctx.user.mention}** تحدي إكس أوه جديداً!\nاضغط على الزر بالأسفل للانضمام كمنافس (لاعبين اثنين فقط).",
                color=discord.Color.gold()
            )
            await ctx.response.send_message(embed=emb_invite, view=TicTacToeChallengeView(ctx.user))

        elif v == "q_game":
            players = [m for m in ctx.channel.members if not m.bot]
            if len(players) < 2:
                await ctx.response.send_message("❌ هذه اللعبة تتطلب وجود **لاعبين اثنين (2) على الأقل** في الروم!", ephemeral=True)
                return
            vw = discord.ui.View()
            vw.add_item(QuestionsLevelSelect(players))
            await ctx.response.send_message("🎲 اختر مستوى صراحة الأسئلة للبدء:", view=vw)

        elif v == "riddle_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة الألغاز التلقائية!** ستستمر الأسئلة تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                riddle, ans = random.choice(RIDDLES)
                emb = discord.Embed(
                    title="🧩 │ لعبة الألغاز الإمبراطورية",
                    description=f"❓ **اللغز:**\n`{riddle}`\n\n💡 اكتب الإجابة الصحيحة في الشات فوراً!",
                    color=discord.Color.green()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and ans in m.content.strip()

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=30.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "riddles")
                    await ctx.channel.send(f"🎉 **تهنئة ملكية!** إجابة صحيحة يا بطل {winner_msg.author.mention}! 🏆 الإجابة هي: **[{ans}]**")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** لم يتمكن أحد من حل اللغز. الإجابة الصحيحة كانت: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "spy_game":
            players = [m for m in ctx.channel.members if not m.bot][:6]
            if len(players) < 3:
                await ctx.response.send_message("❌ لعبة الجواسيس تتطلب وجود **3 لاعبين على الأقل** في السيرفر/الروم!", ephemeral=True)
                return

            spy = random.choice(players)
            secret_words = ["مستشفى", "مطار", "مدرسة", "قلعة أسطورية", "سفينة قرصان", "مركز شرطة", "مطعم"]
            correct_word = random.choice(secret_words)

            for p in players:
                if p.id == spy.id:
                    try: await p.send("🕵️‍♂️ **أنت الجاسوس!** حاول التمويه واكتشاف الكلمة السرية من تلميحات المواطنين!")
                    except: pass
                else:
                    try: await p.send(f"🤫 **أنت مواطن صالي!** الكلمة السرية هي: **[{correct_word}]**. أعطِ تلميحات ذكية ولا تكشفها للجاسوس!")
                    except: pass

            emb_spy = discord.Embed(
                title="🕵️‍♂️ │ بدأت لعبة الجواسيس (Spyfall)",
                description=(
                    f"👥 **اللاعبون المشاركون:** {', '.join([p.mention for p in players])}\n"
                    f"🤫 تم إرسال الأدور والكلمة السرية في الخاص!\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 ابدأوا في تقديم التلميحات بالروم وصوتوا ضد الجاسوس عبر القائمة بالأسفل:"
                ),
                color=discord.Color.purple()
            )
            vw = discord.ui.View()
            vw.add_item(SpyVoteSelect(players, spy, correct_word, secret_words))
            await ctx.response.send_message(embed=emb_spy, view=vw)

        elif v == "math_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة الرياضيات التلقائية!** ستستمر المعادلات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                eq, ans = random.choice(MATH_EQUATIONS)
                emb = discord.Embed(
                    title="🧮 │ لعبة الرياضيات والسرعة",
                    description=f"⚡ **احسب الناتج بسرعة خلال 15 ثانية:**\n`{eq} = ؟`",
                    color=discord.Color.blue()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == ans

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "math")
                    await ctx.channel.send(f"🎉 **سرعة أسطورية!** {winner_msg.author.mention} حل المعادلة الصحيحة **[{ans}]** بنجاح! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **خسرتم الوقت!** انتهت الـ 15 ثانية بدون إجابة. الناتج الصحيح كان: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "anime_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة خمن الأنمي التلقائية!** ستستمر الأنميات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                hint, valid_answers = random.choice(ANIME_DATA)
                emb = discord.Embed(
                    title="🎌 │ لعبة خمن الأنمي",
                    description=f"💡 **التلميح:**\n`{hint}`\n\n⏱️ **معكم 25 ثانية فقط لمعرفة اسم الأنمي!**",
                    color=discord.Color.gold()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    if m.channel.id != cid or m.author.bot:
                        return False
                    user_ans = m.content.strip().lower()
                    return any(ans.lower() in user_ans for ans in valid_answers)

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=25.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "anime")
                    await ctx.channel.send(f"🎉 **أوتاكو أسطوري!** {winner_msg.author.mention} عرف الأنمي الصحيح **[{valid_answers[0]}]** بنجاح! 👑")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** اسم الأنمي الصحيح كان: **[{valid_answers[0]}]**")

                await asyncio.sleep(2.5)

        elif v == "cut_tweet":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة كت تويت التلقائية!** تتغير المقولات تلقائياً كل 20 ثانية.")

            while ACTIVE_GAMES.get(cid, False):
                tweet = random.choice(CUT_TWEETS)
                emb = discord.Embed(
                    title="💬 │ كت تويت (Cut Tweet)",
                    description=f"📜 **المقولة/النقاش:**\n`{tweet}`\n━━━━━━━━━━━━━━━━━━━━\nهل أنت **مع أم ضد** القول أعلاه؟\n\n⏱️ **تتغير المقولة تلقائياً خلال 20 ثانية!**",
                    color=discord.Color.teal()
                )
                await ctx.channel.send(embed=emb, view=CutTweetLoopView(cid))

                for _ in range(20):
                    if not ACTIVE_GAMES.get(cid, False):
                        break
                    await asyncio.sleep(1)

        elif v == "deconstruct":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة فكّك الكلمات التلقائية!** ستستمر الكلمات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                word, ans = random.choice(DECONSTRUCT_WORDS)
                emb = discord.Embed(
                    title="🔤 │ لعبة فكّك الكلمات",
                    description=f"🎯 **فكّك الكلمة التالية بحروف بينها مسافات خلال 15 ثانية:**\n`[{word}]`",
                    color=discord.Color.orange()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == ans

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "deconstruct")
                    await ctx.channel.send(f"🎉 **إجابة رائعة!** {winner_msg.author.mention} فكك الكلمة بشكل صحيح **[{ans}]**! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهت الـ 15 ثانية!** التفكيك الصحيح كان: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "fastest":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة أسرع كتابة التلقائية!** ستستمر الكلمات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                word = random.choice(FASTEST_WORDS)
                emb = discord.Embed(
                    title="⚡ │ لعبة أسرع كتابة",
                    description=f"🚀 **اكتب الكلمة التالية بسرعة وطابقها بالضبط خلال 15 ثانية:**\n`{word}`",
                    color=discord.Color.magenta()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == word

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "fastest")
                    await ctx.channel.send(f"⚡ **سرعة خارقة!** {winner_msg.author.mention} كتب الكلمة أولاً خلال الثواني الأسرع! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** لم يكتب أحد الكلمة المطابقة `{word}` في الـ 15 ثانية.")

                await asyncio.sleep(2.5)

class MainGamesView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(MainGamesSelect())

# ==================== أحداث وأوامر البوت كاملة ====================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✨ تم مزامنة البوت بنجاح! يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ المزامنة: {e}")

@bot.tree.command(name="تسجيل", description="📜 تسجيل حساب جديد")
async def register_command(ctx: discord.Interaction):
    if is_user_registered(ctx.user.id):
        await ctx.response.send_message("⚠️ أنت مسجل بالفعل!", ephemeral=True)
        return
    await ctx.response.send_modal(RegisterModal())

@bot.tree.command(name="المتجر_العام", description="🏛️ فتح المتجر العام")
async def general_store(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="🏛️ المتجر العام", color=discord.Color.gold()), view=GeneralStoreView())

@bot.tree.command(name="المتجر_المظلم", description="👁️ فتح المتجر المظلم")
async def dark_store(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="🔮 المتجر المظلم", color=discord.Color.purple()), view=DarkStoreView())

@bot.tree.command(name="تطوير_المعدلات", description="⚡ تطوير المعدلات والخصائص")
async def upgrade_stats_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="✨ تطوير المعدلات", color=discord.Color.red()), view=StatsUpgradeView())

@bot.tree.command(name="الطوابق", description="🏰 دخول برج الطوابق بالقتال والتقدم التلقائي")
async def tower_floors_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}
    emb = discord.Embed(title="🏰 برج الطوابق الـ 500", description=f"• الطابق الحالي: `[{u.get('max_floor', 1)}/500]`\n• الطاقة القتالية: `{u.get('power', 0):,}` ⚡", color=discord.Color.green())
    await ctx.response.send_message(embed=emb, view=TowerMainView())

@bot.tree.command(name="الليدربورد", description="👑 عرض قاعة العظماء والتصنيفات")
async def leaderboard_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="👑 قاعة العظماء — اختر التصنيف من القائمة بالأسفل", color=discord.Color.gold()), view=LeaderboardView())

@bot.tree.command(name="لوحة_المطور", description="👑 غرفة التحكم الإلهية والقدرات المطلقة للمطورين")
async def dev_panel_command(ctx: discord.Interaction):
    if not is_dev(ctx.user.id):
        await ctx.response.send_message("❌ هذا الأمر للمطورين فقط!", ephemeral=True)
        return

    emb = discord.Embed(
        title="⚡ │ غرفة التحكم الإلهية والقدرات المطلقة — DEV CONTROL ROOM",
        description=(
            "أهلاً بك يا سيّد المطورين في القاعة الإدارية العليا للإمبراطورية.\n"
            "من هنا تملك السلطة الكاملة للتلاعب بالخصائص، شحن الثروات، إهداء العتاد المحرم T25، والتطوير الأسطوري الفوري!\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.from_rgb(255, 215, 0)
    )
    emb.set_thumbnail(url=ctx.user.display_avatar.url)
    emb.add_field(
        name="👑 **حالة المطور**",
        value=f"• **المطور:** {ctx.user.mention}\n• **الصلاحية:** `ADMIN / DEV GOD`\n• **النظام:** `Active & Operational` 🟢",
        inline=True
    )
    emb.add_field(
        name="🔥 **أبرز الأوامر المطلقة**",
        value="• 🚀 **تطوير بنقرة واحدة** (Max All)\n• ☠️ **عتاد المطور المحرم T25** (8 قطع)\n• ♾️ **ثروات وعملات لا نهائية**\n• 👑 **توليد الألقاب الخاصة**",
        inline=True
    )
    emb.set_footer(text="⚠️ الأوامر المنفذة هنا فورية وتنعكس مباشرة على الداتابيز")

    await ctx.response.send_message(embed=emb, view=DevPanelView(), ephemeral=True)

@bot.tree.command(name="الابطال", description="🦸‍♂️ عرض الأبطال الـ 10 واختيار بطل الخاص بك")
async def heroes_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="🦸‍♂️ قاعة الأبطال الفانتازية (5 ذكور | 5 إناث)", description="اختر بطلاً من القائمة بالأسفل للتعرف على قصته ومعدلاته واختياره!", color=discord.Color.gold()), view=HeroesView())

@bot.tree.command(name="تطوير_البطل", description="🚀 تطوير معدلات بطلتك/بطلك بدون حد أقصى")
async def upgrade_hero_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    uid = str(ctx.user.id)
    u = users_col.find_one({"user_id": uid}) or {}
    h_id = u.get("chosen_hero")

    if not h_id or h_id not in HEROES_CFG:
        await ctx.response.send_message("❌ لم تقم باختيار بطل بعد! استخدم أمر `/الابطال` أولاً واختر بطل إمبراطوريتك.", ephemeral=True)
        return

    h = HEROES_CFG[h_id]
    user_h_stats = u.get("hero_stats", {})

    emb = discord.Embed(
        title=f"🚀 تطوير البطل: {h['emoji']} {h['name']}",
        description="اختر المعدل القتالي الذي تريد ترقيته من القائمة بالأسفل. **(التطوير مفتوح بلا حد أقصى!)**",
        color=discord.Color.blue()
    )

    stats_list = []
    for s_k, (s_n, s_e) in HERO_STATS_CFG.items():
        val = user_h_stats.get(s_k, h["stats"].get(s_k, 0))
        stats_list.append(f"{s_e} {s_n}: `{val:,}`")

    emb.add_field(name="📊 معدلات البطل الحالية", value="\n".join(stats_list), inline=False)
    emb.add_field(name="🪙 رصيدك الحالي", value=f"`{u.get('balance', 0):,}` ذهب", inline=True)

    await ctx.response.send_message(embed=emb, view=HeroUpgradeView(), ephemeral=True)

@bot.tree.command(name="بروفايل", description="🪪 عرض بطاقة المقاتل الفخمة")
async def profile_command(ctx: discord.Interaction, target: discord.User = None):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    target_user = target or ctx.user
    u = users_col.find_one({"user_id": str(target_user.id)})

    if not u:
        await ctx.response.send_message("❌ هذا المستخدم غير مسجل بعد!", ephemeral=True)
        return

    h_id = u.get("chosen_hero")
    h_info = HEROES_CFG.get(h_id, {}) if h_id else {}
    h_name = f"{h_info.get('emoji','🦸')} {h_info.get('name','غير محدد')}" if h_id else "لم يحدد بعد"

    tot_power = u.get('power', 0)
    if tot_power >= 1_000_000: tier = "🔥 حاكم أسطوري"
    elif tot_power >= 100_000: tier = "🌟 إمبراطور الحرب"
    elif tot_power >= 10_000: tier = "⚔️ قائد أسطوري"
    else: tier = "🟢 مقاتل واعد"

    emb = discord.Embed(
        title=f"👑 │ بطاقة المقاتل الإمبراطورية — {u.get('name', 'غير معروف')}",
        description=f"✨ **اللقب الحالي:** `[ {u.get('custom_title', 'المبتدئ الأسطوري')} ]`\n🔰 **الرتبة:** `{tier}`\n━━━━━━━━━━━━━━━━━━━━",
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=target_user.display_avatar.url)

    emb.add_field(
        name="👤 **البيانات الشخصية**",
        value=f"• **العمر:** `{u.get('age', '-')}` عاماً\n• **الجنس:** `{u.get('gender', '-')}`\n• **البطل المعتمد:** {h_name}\n• **الألقاب المكتسبة:** `{len(u.get('titles', [])):,}`",
        inline=True
    )

    total_wealth = u.get('balance', 0) + u.get('bank', 0)
    emb.add_field(
        name="💰 **الثروة والخزينة**",
        value=f"• **الكاش:** `{u.get('balance', 0):,}` 🪙\n• **البنك:** `{u.get('bank', 0):,}` 🪙\n• **الألماس:** `{u.get('diamonds', 0):,}` 💎\n• **إجمالي الثروة:** `{total_wealth:,}` 🪙",
        inline=True
    )

    emb.add_field(
        name="📊 **إحصائيات الإمبراطورية**",
        value=f"• **القوة الكلية:** `{tot_power:,}` ⚡\n• **أعلى طابق:** `[ {u.get('max_floor', 1)} / 500 ]` 🏰\n• **عدد القتلات:** `{u.get('kills', 0):,}` 🩸",
        inline=False
    )

    stats_text = (
        f"🗡️ **هجوم:** `{u.get('attack', 10):,}` │ 🛡️ **دفاع:** `{u.get('defense', 10):,}` │ 🔮 **سحر:** `{u.get('magic', 10):,}`\n"
        f"🎯 **تصويب:** `{u.get('aim', 10):,}` │ 💨 **مراوغة:** `{u.get('evasion', 10):,}` │ 👁️ **دقة:** `{u.get('accuracy', 10):,}`\n"
        f"🧠 **ذكاء:** `{u.get('intelligence', 10):,}` │ 💥 **ضربات قاتلة:** `{u.get('critical', 10):,}`"
    )
    emb.add_field(name="⚔️ **الخصائص القتالية التفصيلية**", value=stats_text, inline=False)
    emb.set_footer(text="👑 الإمبراطورية العظمى • نظام القتال والعرش")

    await ctx.response.send_message(embed=emb)

@bot.tree.command(name="الحقيبة", description="🎒 عرض المعدات والعتاد الممتلك")
async def inventory_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}
    inv = u.get("inventory", [])

    if not inv:
        desc_txt = "لا تملك أي عتاد حالياً. يمكنك الشراء من المتجر!"
    else:
        counts = {}
        for item in inv:
            counts[item] = counts.get(item, 0) + 1
        desc_txt = "\n".join([f"• **{k}** (x{v})" for k, v in counts.items()])

    emb = discord.Embed(title="🎒 حقائبك ومعداتك", description=desc_txt, color=discord.Color.dark_green())
    await ctx.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="البنك_الإمبراطوري", description="🏛️ الخزنة الملكية، إدارة الثروات والاستثمارات")
async def imperial_bank_cmd(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}

    emb = discord.Embed(
        title="🏛️ │ المصرف الملكي والإمبراطوري العظيم",
        description=(
            f"مرحباً بك يا صاحب السعادة المقاتل **{u.get('name', ctx.user.display_name)}** في أكبر مركز مالي في الإمبراطورية.\n"
            f"من هنا يمكنك إدارة ثرواتك، استلام الرواتب الملكية، تحويل الأموال، والاستثمار!\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=ctx.user.display_avatar.url)

    emb.add_field(name="🪙 **الكاش المتاح**", value=f"`{u.get('balance', 0):,}` ذهبة", inline=True)
    emb.add_field(name="🏦 **الرصيد بالبنك**", value=f"`{u.get('bank', 0):,}` ذهبة", inline=True)
    emb.add_field(name="💎 **الألماس الإمبراطوري**", value=f"`{u.get('diamonds', 0):,}` ألماس", inline=True)

    loan = u.get("loan", 0)
    loan_status = f"⚠️ `{loan:,}` 🪙 (يتوجب السداد)" if loan > 0 else "✅ خالي من القروض والديون"
    emb.add_field(name="💳 **وضع القروض والائتمان**", value=loan_status, inline=False)
    emb.set_footer(text="استخدم الأزرار بالأسفل لتنفيذ كافة العمليات المصرفية")

    await ctx.response.send_message(embed=emb, view=ImperialBankView())

@bot.tree.command(name="انشاء_نقابتي", description="🏰 تأسيس نقابة إمبراطورية جديدة (الكلفة: 400 🪙)")
async def create_guild_cmd(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_modal(CreateGuildModal())

@bot.tree.command(name="النقابات", description="🏰 عرض النقابات العظمى وترتيبهم وقوتهم ومكان الانضمام")
async def list_guilds_cmd(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    all_guilds = list(guilds_col.find())
    all_guilds.sort(key=lambda x: x.get("power", 0), reverse=True)

    if not all_guilds:
        desc_txt = "لا توجد نقابات مسجلة حتى الآن! كن أول من يؤسس حلفاً عبر `/انشاء_نقابتي`."
    else:
        lines = []
        for idx, g in enumerate(all_guilds[:10]):
            leader_u = users_col.find_one({"user_id": g.get("leader_id")})
            leader_name = leader_u.get("name", "غير معروف") if leader_u else "غير معروف"
            status = "🔓 مفتوحة" if g.get("is_open", True) else "🔒 مغلقة"
            lines.append(f"#{idx+1} **[ {g.get('name')} ]** — ⚡ `{g.get('power',0):,}` | 👥 `{len(g.get('members',[]))}` عضواً | 👑 القائد: `{leader_name}` ({status})")
        desc_txt = "\n".join(lines)

    emb = discord.Embed(
        title="🏰 قاعة النقابات العظمى بالإمبراطورية",
        description=desc_txt,
        color=discord.Color.gold()
    )

    open_guilds = [g for g in all_guilds if g.get("is_open", True)]
    await ctx.response.send_message(embed=emb, view=GuildsListView(open_guilds))

@bot.tree.command(name="نقابتي", description="🛡️ لوحة معلومات وإدارة نقابتك والتبرع لها")
async def my_guild_cmd(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    uid = str(ctx.user.id)
    u = users_col.find_one({"user_id": uid}) or {}
    g_id = u.get("guild_id")

    if not g_id:
        await ctx.response.send_message("❌ أنت لست تنتمي لأي نقابة حالياً! استعرض النقابات عبر `/النقابات` أو أسس نقابتك عبر `/انشاء_نقابتي`.", ephemeral=True)
        return

    g = guilds_col.find_one({"guild_id": g_id})
    if not g:
        await ctx.response.send_message("❌ حدث خطأ، لم يتم العثور على بيانات النقابة!", ephemeral=True)
        return

    leader_u = users_col.find_one({"user_id": g.get("leader_id")})
    leader_name = leader_u.get("name", "غير معروف") if leader_u else "غير معروف"
    is_open = g.get("is_open", True)

    emb = discord.Embed(
        title=f"🏰 قلعة حلف: [ {g.get('name')} ]",
        description=f"مرحباً بك يا المقاتل في معقل نقابتك العظيمة.\nاستخدم الأزرار بالأسفل للتبرع بالعتاد أو الثروات وتعزيز قوة حلفكم!",
        color=discord.Color.dark_gold()
    )

    emb.add_field(name="👑 قائد النقابة", value=f"`{leader_name}`", inline=True)
    emb.add_field(name="👥 عدد الأعضاء", value=f"`{len(g.get('members', []))}` محارب", inline=True)
    emb.add_field(name="⚡ القوة القتالية", value=f"`{g.get('power', 0):,}` ⚡", inline=True)

    emb.add_field(name="🪙 خزنة الذهب", value=f"`{g.get('balance', 0):,}` ذهبة", inline=True)
    emb.add_field(name="💎 خزنة الألماس", value=f"`{g.get('diamonds', 0):,}` ألماس", inline=True)
    emb.add_field(name="🎒 قطع العتاد المخزنة", value=f"`{len(g.get('gear_vault', []))}` قطعة", inline=True)

    emb.add_field(name="🔓 حالة الانضمام", value="`مفتوح للجميع`" if is_open else "`مغلق بقرار القائد`", inline=False)

    await ctx.response.send_message(embed=emb, view=MyGuildView(is_open))

@bot.tree.command(name="الالعاب", description="🎮 مركز وقاعة الألعاب الإمبراطورية الملكية الـ 9")
async def games_hub_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    emb = discord.Embed(
        title="🎮 │ صالة الألعاب الإمبراطورية العظمى — IMPERIAL GAMES",
        description=(
            "مرحباً بك يا صاحب السعادة في مجمع الترفيه والتحديات الممتعة!\n"
            "اختر اللعبة المناسبة لك ولأصدقائك من القائمة بالأسفل وباشر بالقتال والتحدي:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎲 **الأسئلة والجريئة** │ 🧩 **الألغاز** │ 🕵️‍♂️ **الجواسيس**\n"
            "🧮 **الرياضيات** │ 🎌 **خمن الأنمي** │ 💬 **كت تويت**\n"
            "🔤 **فكّك** │ ⚡ **أسرع** │ ❌ **إكس أوه (XO)**"
        ),
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=ctx.user.display_avatar.url)
    emb.set_footer(text="👑 استمتع بالتحديات المباشرة واكسب نقاط الليدربورد!")
    await ctx.response.send_message(embed=emb, view=MainGamesView())

@bot.tree.command(name="ليدربورد_الالعاب", description="🏆 عرض أبطال ومتصدري الألعاب في السيرفر")
async def games_leaderboard_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    emb = discord.Embed(title="🏆 قاعة العظماء للألعاب — اختر تصنيف اللعبة من القائمة بالأسفل", color=discord.Color.gold())
    vw = discord.ui.View()
    vw.add_item(GamesLeaderboardSelect())
    await ctx.response.send_message(embed=emb, view=vw)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
