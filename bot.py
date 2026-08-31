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

def is_user_registered(uid) -> bool:
    return users_col.find_one({"user_id": str(uid)}) is not None

def is_dev(uid) -> bool:
    suid = str(uid)
    if suid == MAIN_DEV_ID or devs_col.find_one({"user_id": suid}):
        return True
    u = users_col.find_one({"user_id": suid})
    return bool(u and u.get("is_dev"))

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
    "valerian": {
        "name": "فالريان، سيف الشمس", "gender": "ذكر", "emoji": "⚔️",
        "story": "فارس أسطوري ولد تحت نجم ملتهب، يقود فرسان الإمبراطورية في طليعة المعارك ولا يعرف التراجع.",
        "base_power": 1200,
        "stats": {"leadership": 35, "attack": 30, "defense": 25, "aim": 10, "magic": 5, "intelligence": 15, "deception": 5}
    },
    "ignis": {
        "name": "إغنيس، سيد اللهب الأسود", "gender": "ذكر", "emoji": "🔥",
        "story": "ساحر ظلال قديم تحكم بعناصر النار المظلمة بعد تدمير برجه الأسطوري، يحرق أعداءه بلمشة بصرية.",
        "base_power": 1350,
        "stats": {"magic": 40, "intelligence": 30, "attack": 25, "leadership": 10, "aim": 10, "defense": 10, "deception": 10}
    },
    "zephyr": {
        "name": "زفير، ظل الرماة", "gender": "ذكر", "emoji": "🎯",
        "story": "قناص الغابات المحرمة الذي لا تخطئ سهامه من أي مسافة، يختفي بين الظلال ويصطاد فرائسه بمهارة.",
        "base_power": 1150,
        "stats": {"aim": 40, "deception": 25, "attack": 25, "intelligence": 15, "defense": 10, "magic": 5, "leadership": 10}
    },
    "lucian": {
        "name": "لوكيان، حارس العرش الفولاذي", "gender": "ذكر", "emoji": "🛡️",
        "story": "درع الإمبراطورية الأخير الذي صمد أمام جيوش الشياطين بمفرده، يستمد قوته من الحماية الصلبة.",
        "base_power": 1250,
        "stats": {"defense": 45, "leadership": 25, "intelligence": 20, "attack": 15, "aim": 5, "magic": 5, "deception": 5}
    },
    "malakai": {
        "name": "مالاكاي، حائك الأوهام", "gender": "ذكر", "emoji": "🎭",
        "story": "سيد التجسس والدسائس الذي أطاح بممالك كاملة دون أن يسل سيفاً، يتلاعب بالعقول كحجارة الشطرنج.",
        "base_power": 1100,
        "stats": {"deception": 45, "intelligence": 35, "aim": 15, "magic": 15, "leadership": 10, "attack": 10, "defense": 5}
    },
    "athena": {
        "name": "أثينا، قائدة الفرسان الستة", "gender": "أنثى", "emoji": "👑",
        "story": "إمبراطورة الميدان التي تقود الجيش بذكاء تكتيكي لا مثيل له، تخضع لها أعتى الجيوش باحترام.",
        "base_power": 1300,
        "stats": {"leadership": 40, "defense": 25, "attack": 25, "intelligence": 20, "aim": 10, "magic": 5, "deception": 5}
    },
    "serene": {
        "name": "سيرين، كاهنة القمر والبحار", "gender": "أنثى", "emoji": "🔮",
        "story": "سيدة السحر السماوي التي تستدعي أمواج البحار وأشعة القمر لتطهير الأرض من الجيوش المظلمة.",
        "base_power": 1400,
        "stats": {"magic": 45, "intelligence": 30, "leadership": 20, "defense": 15, "aim": 10, "deception": 5, "attack": 10}
    },
    "lyra": {
        "name": "ليرا، عاصفة السهام", "gender": "أنثى", "emoji": "🏹",
        "story": "صيادة سريعة كالعاصفة، تطلق مئات السهام الضوئية في لحظة واحدة لتمطر الأعداء بالموت المفاجئ.",
        "base_power": 1200,
        "stats": {"aim": 42, "attack": 28, "deception": 20, "intelligence": 15, "leadership": 10, "defense": 5, "magic": 10}
    },
    "morgana": {
        "name": "مورغانا، ملكة الدسائس", "gender": "أنثى", "emoji": "🖤",
        "story": "حاكمة الظلال التي تلاعبت بعقول الملوك وجعلتهم ينقادون لإرادتها بجمالها وسحرها الغامض.",
        "base_power": 1250,
        "stats": {"deception": 42, "magic": 30, "intelligence": 28, "aim": 10, "leadership": 10, "attack": 5, "defense": 5}
    },
    "hilda": {
        "name": "هيلدا، جدار الجليد", "gender": "أنثى", "emoji": "❄️",
        "story": "محاربة الشمال الأسطورية التي تسخر طاقة الجليد لتجميد خُصومها وصد أعتى ضرباتهم بلا اهتزاز.",
        "base_power": 1280,
        "stats": {"defense": 40, "attack": 30, "leadership": 20, "intelligence": 15, "magic": 10, "aim": 10, "deception": 5}
    }
}

HERO_STATS_CFG = {
    "aim": ("التصويب", "🎯"),
    "magic": ("السحر", "🔮"),
    "attack": ("الهجوم", "🗡️"),
    "defense": ("الدفاع", "🛡️"),
    "intelligence": ("الذكاء", "🧠"),
    "deception": ("الخداع", "🎭"),
    "leadership": ("القيادة", "👑")
}

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

STATS_CFG = {
    "aim": ("التصويب", "🎯"), "evasion": ("المراوغة", "💨"), "attack": ("الهجوم", "🗡️"),
    "accuracy": ("الدقة", "👁️"), "critical": ("الضربات القاتلة", "💥"), "magic": ("السحر", "🔮"),
    "intelligence": ("الذكاء", "🧠"), "defense": ("الدفاع", "🛡️")
}

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

def render_hp_bar(cur: int, max_hp: int) -> str:
    pct = max(0.0, min(1.0, cur / max_hp)) if max_hp > 0 else 0
    f = int(pct * 10)
    return f"`[{'█'*f}{'░'*(10-f)}]` {cur:,}/{max_hp:,} HP"

async def process_floor_battle(ctx: discord.Interaction, floor_num: int):
    uid = str(ctx.user.id)
    u = users_col.find_one({"user_id": uid}) or {}
    if floor_num > 500:
        await ctx.response.send_message("🏆 أتممت الـ 500 طابق بالكامل!", ephemeral=True)
        return

    is_b = (floor_num % 10 == 0)
    e_hp = 500 + (floor_num * 350) if is_b else 150 + (floor_num * 100)
    e_atk = 40 + (floor_num * 30) if is_b else 15 + (floor_num * 12)
    e_name = f"👑 BOSS طابق {floor_num}" if is_b else f"🧟 زومبي طابق {floor_num}"

    p_atk = u.get("attack", 10) * 12 + u.get("power", 100) * 1.2
    p_hp = p_max = 300 + u.get("defense", 10) * 25 + u.get("power", 100) * 2

    emb = discord.Embed(title=f"⚔️ معركة الطابق [{floor_num}/500]", color=discord.Color.red())
    emb.add_field(name="👤 اللاعب", value=render_hp_bar(int(p_hp), int(p_max)))
    emb.add_field(name=f"👾 {e_name}", value=render_hp_bar(e_hp, e_hp))

    await ctx.response.send_message(embed=emb)
    msg = await ctx.original_response()

    await asyncio.sleep(1.5)
    gold = floor_num * 300 + random.randint(100, 500)
    users_col.update_one({"user_id": uid}, {"$inc": {"balance": gold, "power": 30}, "$set": {"max_floor": floor_num + 1}})

    win_emb = discord.Embed(title=f"🎉 انتصرت في الطابق [{floor_num}]!", description=f"🎁 المكافأة: `{gold:,}` 🪙 ذهب!", color=discord.Color.gold())
    v = discord.ui.View()
    btn = discord.ui.Button(label=f"➡️ الطابق التالي [{floor_num+1}]", style=discord.ButtonStyle.success)

    async def b_call(b_ctx: discord.Interaction):
        if str(b_ctx.user.id) != uid:
            await b_ctx.response.send_message("❌ المعركة ليست لك!", ephemeral=True)
            return
        await process_floor_battle(b_ctx, floor_num + 1)

    btn.callback = b_call
    v.add_item(btn)
    await msg.edit(embed=win_emb, view=v)

class TowerMainSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="بدء المغامرة", value="start", emoji="⚔️"),
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
            await process_floor_battle(ctx, u.get("max_floor", 1))
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

class DevActionSelectMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="عملات لا نهائية", value="inf", emoji="♾️", description="شحن رصيد عملات لا نهائي لك"),
            discord.SelectOption(label="تفعيل السفاح الخارق", value="assassin", emoji="🩸", description="رفع طاقتك وخصائصك لأقصى حد"),
            discord.SelectOption(label="إهداء عتاد للاعب", value="gift_gear", emoji="🎁", description="إهداء عتاد محدد للاعب بالمنشن"),
            discord.SelectOption(label="تحويل / إهداء عملات", value="transfer", emoji="💸", description="شحن عملات للاعب بالمنشن"),
            discord.SelectOption(label="إضافة مطور", value="add_dev", emoji="👑", description="منح صلاحية مطور للاعب بالمنشن")
        ]
        super().__init__(placeholder="⚙️ اختر إجراء المطور...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        if not is_dev(ctx.user.id):
            await ctx.response.send_message("❌ لست مطوراً!", ephemeral=True)
            return
        uid = str(ctx.user.id)
        v = self.values[0]

        if v == "inf":
            users_col.update_one({"user_id": uid}, {"$set": {"balance": 999999999999, "diamonds": 999999999}})
            await ctx.response.send_message("♾️ تم شحن عملات لا نهائية لحسابك!", ephemeral=True)

        elif v == "assassin":
            st = {"power": 999999999999, "balance": 999999999999, "diamonds": 999999999, "attack": 999999999, "defense": 999999999}
            users_col.update_one({"user_id": uid}, {"$set": st})
            await ctx.response.send_message("🩸 تم تفعيل شخصية السفاح الخارقة!", ephemeral=True)

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

    @discord.ui.button(label="💸 تحويل بالمنشن", style=discord.ButtonStyle.danger, row=1)
    async def transfer_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_message("👤 اختر العضو المراد التحويل له من القائمة:", view=BankTransferSelectView(), ephemeral=True)

    @discord.ui.button(label="📥 إيداع", style=discord.ButtonStyle.secondary, row=1)
    async def deposit_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankDepositModal())

    @discord.ui.button(label="📤 سحب", style=discord.ButtonStyle.secondary, row=1)
    async def withdraw_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.send_modal(BankWithdrawModal())

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
                await ctx.response.send_mes
