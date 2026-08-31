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
            "last_daily": None, "loan": 0
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

class DevActionSelectMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="عملات لا نهائية", value="inf", emoji="♾️"),
            discord.SelectOption(label="تفعيل السفاح الخارق", value="assassin", emoji="🩸")
        ]
        super().__init__(placeholder="⚙️ إجراءات المطور...", options=opts)

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

class DevPanelView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DevActionSelectMenu())

# ==================== نظام البنك والتحويل بالمنشن ====================

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

# نافذة تحديد المبلغ عند التحويل بالمنشن
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

# قائمة اختيار الشخص بالمنشن للتحويل
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

# ==================== أحداث البوت والأوامر ====================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✨ تم المزامنة بنجاح! البوت يعمل باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ بالمزامنة: {e}")

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

@bot.tree.command(name="الطوابق", description="🏰 دخول برج الطوابق")
async def tower_floors_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}
    emb = discord.Embed(title="🏰 برج الطوابق الـ 500", description=f"• الطابق الحالي: `[{u.get('max_floor', 1)}/500]`\n• الطاقة: `{u.get('power', 0):,}` ⚡", color=discord.Color.green())
    await ctx.response.send_message(embed=emb, view=TowerMainView())

@bot.tree.command(name="الليدربورد", description="👑 عرض قاعة العظماء والتصنيفات")
async def leaderboard_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="👑 قاعة العظماء — اختر التصنيف من القائمة بالأسفل", color=discord.Color.gold()), view=LeaderboardView())

@bot.tree.command(name="لوحة_المطور", description="👑 لوحة التحكم للمطورين")
async def dev_panel_command(ctx: discord.Interaction):
    if not is_dev(ctx.user.id):
        await ctx.response.send_message("❌ هذا الأمر للمطورين فقط!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="👑 لوحة التحكم الإدارية", color=discord.Color.purple()), view=DevPanelView(), ephemeral=True)

@bot.tree.command(name="بروفايل", description="🪪 عرض معلوماتك أو معلومات مقاتل آخر")
async def profile_command(ctx: discord.Interaction, target: discord.User = None):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    target_user = target or ctx.user
    u = users_col.find_one({"user_id": str(target_user.id)})

    if not u:
        await ctx.response.send_message("❌ هذا المستخدم غير مسجل بعد!", ephemeral=True)
        return

    emb = discord.Embed(title=f"🪪 ملف المقاتل — {u.get('name', 'غير معروف')}", color=discord.Color.blue())
    emb.set_thumbnail(url=target_user.display_avatar.url)
    emb.add_field(name="👑 اللقب", value=f"`{u.get('custom_title', 'المبتدئ')}`", inline=True)
    emb.add_field(name="⌛ العمر", value=f"`{u.get('age', '-')}` سنة", inline=True)
    emb.add_field(name="🚻 الجنس", value=f"`{u.get('gender', '-')}`", inline=True)
    emb.add_field(name="⚡ القوة الإجمالية", value=f"`{u.get('power', 0):,}`", inline=False)
    emb.add_field(name="🪙 الكاش", value=f"`{u.get('balance', 0):,}`", inline=True)
    emb.add_field(name="🏦 البنك", value=f"`{u.get('bank', 0):,}`", inline=True)
    emb.add_field(name="💎 الألماس", value=f"`{u.get('diamonds', 0):,}`", inline=True)
    emb.add_field(name="🏰 أعلى طابق", value=f"`{u.get('max_floor', 1)}`", inline=True)

    stats_str = f"🗡️ هجوم: `{u.get('attack', 10)}` | 🛡️ دفاع: `{u.get('defense', 10)}` | 🔮 سحر: `{u.get('magic', 10)}`\n🎯 تصويب: `{u.get('aim', 10)}` | 💨 مراوغة: `{u.get('evasion', 10)}` | 👁️ دقة: `{u.get('accuracy', 10)}`"
    emb.add_field(name="📊 الخصائص القتالية", value=stats_str, inline=False)

    await ctx.response.send_message(embed=emb)

@bot.tree.command(name="الحقيبة", description="🎒 عرض المعدات والعتاد الممتلك")
async def inventory_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}
    inv = u.get("inventory", [])

    emb = discord.Embed(title="🎒 حقائبك ومعداتك", color=discord.Color.dark_green())
    if not inv:
        emb.description = "لا تملك أي عتاد حالياً. يمكنك الشراء من المتجر!"
    else:
        counts = {}
        for item in inv:
            counts[item] = counts.get(item, 0) + 1
        items_txt = "\n".join([f"• **{k}** (x{v})" for k, v in counts.items()])
        emb.description = items_txt

    await ctx.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="يومي", description="🎁 استلام المكافأة اليومية")
async def daily_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    uid = str(ctx.user.id)
    u = users_col.find_one({"user_id": uid}) or {}
    last_d = u.get("last_daily")
    now = datetime.now(timezone.utc)

    if last_d and (now - last_d.replace(tzinfo=timezone.utc if last_d.tzinfo is None else last_d.tzinfo)).total_seconds() < 86400:
        rem_sec = int(86400 - (now - last_d.replace(tzinfo=timezone.utc if last_d.tzinfo is None else last_d.tzinfo)).total_seconds())
        hrs, mins = rem_sec // 3600, (rem_sec % 3600) // 60
        await ctx.response.send_message(f"⏳ يمكنك استلام المكافأة بعد: `{hrs}` ساعة و `{mins}` دقيقة!", ephemeral=True)
        return

    gold_reward = 3000
    dia_reward = 5
    users_col.update_one({"user_id": uid}, {"$inc": {"balance": gold_reward, "diamonds": dia_reward}, "$set": {"last_daily": now}})
    await ctx.response.send_message(f"🎉 تم استلام راتبك اليومي بنجاح!\n🪙 +`{gold_reward:,}` ذهب\n💎 +`{dia_reward}` ألماس")

@bot.tree.command(name="البنك_الإمبراطوري", description="🏛️ الخزنة الملكية، إدارة الثروات، القروض والتحويلات")
async def imperial_bank_cmd(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}

    emb = discord.Embed(
        title="🏛️ البنك الإمبراطوري الملكي",
        description=f"أهلاً بك يا المقاتل **{u.get('name', ctx.user.display_name)}** في النظام المالي للإمبراطورية.\nيمكنك من هنا استلام رواتبك، طلب القروض، أو تحويل الثروات مع بقية المحاربين.",
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=ctx.user.display_avatar.url)

    emb.add_field(name="🪙 الكاش المباشر", value=f"`{u.get('balance', 0):,}` ذهبة", inline=True)
    emb.add_field(name="🏦 الخزنة بالبنك", value=f"`{u.get('bank', 0):,}` ذهبة", inline=True)
    emb.add_field(name="💎 الألماس الملكي", value=f"`{u.get('diamonds', 0):,}` ألماس", inline=True)

    loan = u.get("loan", 0)
    loan_status = f"`{loan:,}` 🪙 (مستحق)" if loan > 0 else "لا توجد ديون ✅"
    emb.add_field(name="💳 حالة القروض", value=loan_status, inline=False)
    emb.set_footer(text="استخدم الأزرار بالأسفل للتفاعل السريع مع البنك")

    await ctx.response.send_message(embed=emb, view=ImperialBankView())

@bot.tree.command(name="تحويل", description="💸 تحويل عملات مباشرة إلى مقاتل بالمنشن")
@app_commands.describe(target="المقاتل المستلم", amount="المبلغ المراد تحويله", currency="نوع العملة")
@app_commands.choices(currency=[
    app_commands.Choice(name="🪙 ذهب", value="gold"),
    app_commands.Choice(name="💎 ألماس", value="diamonds")
])
async def transfer_command(ctx: discord.Interaction, target: discord.User, amount: int, currency: str):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    if target.id == ctx.user.id:
        await ctx.response.send_message("❌ لا يمكنك التحويل لنفسك!", ephemeral=True)
        return

    if not is_user_registered(target.id):
        await ctx.response.send_message("❌ المستلم غير مسجل في البوت!", ephemeral=True)
        return

    if amount <= 0:
        await ctx.response.send_message("❌ اكتب مبلغاً أكبر من 0!", ephemeral=True)
        return

    sender_id, target_id = str(ctx.user.id), str(target.id)
    s_user = users_col.find_one({"user_id": sender_id}) or {}

    field = "balance" if currency == "gold" else "diamonds"
    sym = "🪙" if currency == "gold" else "💎"

    if s_user.get(field, 0) < amount:
        await ctx.response.send_message(f"❌ لا تملك هذا القدر من الـ {sym}!", ephemeral=True)
        return

    users_col.update_one({"user_id": sender_id}, {"$inc": {field: -amount}})
    users_col.update_one({"user_id": target_id}, {"$inc": {field: amount}})

    await ctx.response.send_message(f"💸 تم تحويل `{amount:,}` {sym} إلى {target.mention} بنجاح!")

@bot.tree.command(name="إضافة_مطور", description="👑 إضافة مطور جديد للبوت (للمطور الرئيسي فقط)")
async def add_dev_command(ctx: discord.Interaction, target: discord.User):
    if str(ctx.user.id) != MAIN_DEV_ID:
        await ctx.response.send_message("❌ هذا الأمر خاص بالمطور الرئيسي فقط!", ephemeral=True)
        return

    devs_col.update_one({"user_id": str(target.id)}, {"$set": {"user_id": str(target.id)}}, upsert=True)
    users_col.update_one({"user_id": str(target.id)}, {"$set": {"is_dev": True}})
    await ctx.response.send_message(f"👑 تم إعطاء صلاحيات المطور لـ {target.mention} بنجاح!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
