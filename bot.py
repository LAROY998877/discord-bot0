import os, random, asyncio, pymongo, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

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

# ================== 🛠️ إعدادات نظام الوظائف ==================
JOBS_CFG = {
    "cook": {"name": "طباخ الإمبراطورية", "emoji": "👨‍🍳", "salary": 2000, "desc": "إعداد الوجبات الفاخرة للجيش والعرش", "req": "لا توجد متطلبات"},
    "miner": {"name": "منجم الأحجار", "emoji": "⛏️", "salary": 2500, "desc": "استخراج الجواهر والمعادن من المناجم", "req": "لا توجد متطلبات"},
    "assassin": {"name": "القاتل المأجور", "emoji": "🗡️", "salary": 4500, "desc": "تنفيذ مهام الاغتيال المظلمة في الخفاء", "req": "لا توجد متطلبات"},
    "singer": {"name": "مغني العرش", "emoji": "🎤", "salary": 2200, "desc": "إمتاع الملوك والأباطرة بالألحان والقصائد", "req": "لا توجد متطلبات"},
    "clown": {"name": "مهرج البلاط", "emoji": "🤡", "salary": 1800, "desc": "إدخال البهجة والضحك في قلوب الحكام", "req": "لا توجد متطلبات"},
    "blacksmith": {"name": "حداد الأسلحة", "emoji": "⚒️", "salary": 3200, "desc": "صناعة وتطوير المعدات والأسلحة للفرسان", "req": "لا توجد متطلبات"},
    "king": {"name": "الملك الأعظم", "emoji": "👑", "salary": 50000, "desc": "حاكم الإمبراطورية والسلطة العليا", "req": "طاقة 50,000+ | طابق 50+ | تبرعات وانجازات عالية"},
    "queen": {"name": "الملكة", "emoji": "👸", "salary": 50000, "desc": "حاكمة العرش وسيدة الإمبراطورية", "req": "جنس أنثى | طاقة 50,000+ | انجازات ومساهمات"},
    "king_hand": {"name": "مساعد الملك", "emoji": "📜", "salary": 25000, "desc": "إدارة شؤون الدولة والقرارات الإستراتيجية", "req": "طاقة 25,000+ | طابق 30+ | مساهمات شرفية"},
    "knight_captain": {"name": "قائد الفرسان", "emoji": "🛡️", "salary": 30000, "desc": "قيادة الجيوش والدفاع عن أراضي العرش", "req": "طاقة 35,000+ | 20 قتلة+ | شعبية وقوة قتالية"}
}

def check_job_req(u, job_key) -> bool:
    pwr = u.get("power", 0)
    flr = u.get("max_floor", 1)
    kls = u.get("kills", 0)
    gnd = u.get("gender", "")
    if job_key == "king": return pwr >= 50000 and flr >= 50
    if job_key == "queen": return gnd == "أنثى" and pwr >= 50000 and flr >= 30
    if job_key == "king_hand": return pwr >= 25000 and flr >= 30
    if job_key == "knight_captain": return pwr >= 35000 and kls >= 20
    return True

class JobSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=v["name"], value=k, emoji=v["emoji"], description=f"راتب: {v['salary']:,} 🪙 | {v['req'][:30]}") for k, v in JOBS_CFG.items()]
        super().__init__(placeholder="💼 اختر الوظيفة للاطلاع عليها...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        jk = self.values[0]
        j = JOBS_CFG[jk]
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        has_req = check_job_req(u, jk)
        st_text = "✅ مؤهل للعمل" if has_req else "❌ لم تحقق الشروط والمساهمات المطلوبة"

        emb = discord.Embed(title=f"{j['emoji']} {j['name']}", color=discord.Color.gold() if has_req else discord.Color.red())
        emb.add_field(name="📜 الوصف", value=j["desc"], inline=False)
        emb.add_field(name="🪙 الراتب اليومي", value=f"`{j['salary']:,}` ذهبة", inline=True)
        emb.add_field(name="📌 متطلبات الوظيفة", value=f"`{j['req']}`", inline=False)
        emb.add_field(name="🔍 حالتك الحالية", value=f"**{st_text}**", inline=False)

        vw = discord.ui.View()
        vw.add_item(JobSelect())

        btn_join = discord.ui.Button(label=f"تعيين في وظيفة {j['name']}", style=discord.ButtonStyle.success if has_req else discord.ButtonStyle.secondary, disabled=not has_req)

        async def join_cb(b_ctx: discord.Interaction):
            users_col.update_one({"user_id": uid}, {"$set": {"job": jk}})
            await b_ctx.response.send_message(f"🎉 تهانينا! تمت ترقيتك وتعيينك رسمياً في وظيفة **{j['emoji']} {j['name']}**!", ephemeral=True)

        btn_join.callback = join_cb
        vw.add_item(btn_join)
        await ctx.response.edit_message(embed=emb, view=vw)

class JobMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(JobSelect())

    @discord.ui.button(label="🪙 استلام الراتب اليومي", style=discord.ButtonStyle.primary, row=1)
    async def claim_salary(self, ctx: discord.Interaction, btn: discord.ui.Button):
        uid = str(ctx.user.id)
        u = users_col.find_one({"user_id": uid}) or {}
        curr_j = u.get("job")

        if not curr_j or curr_j not in JOBS_CFG:
            await ctx.response.send_message("❌ أنت لا تعمل في أي وظيفة حالياً! اختر وظيفة أولاً وتعين بها.", ephemeral=True)
            return

        last_claim = u.get("last_job_claim", 0)
        now_ts = int(datetime.now(timezone.utc).timestamp())

        if now_ts - last_claim < 86400:
            rem = 86400 - (now_ts - last_claim)
            hrs, mins = rem // 3600, (rem % 3600) // 60
            await ctx.response.send_message(f"⏳ لقد استلمت راتبك اليومي! عد مجدداً بعد `{hrs}` ساعة و `{mins}` دقيقة.", ephemeral=True)
            return

        j_data = JOBS_CFG[curr_j]
        sal = j_data["salary"]
        users_col.update_one({"user_id": uid}, {"$inc": {"balance": sal}, "$set": {"last_job_claim": now_ts}})
        await ctx.response.send_message(f"💰 تم صرف راتبك اليومي لوظيفة **{j_data['emoji']} {j_data['name']}**: `+{sal:,}` 🪙 ذهبة!", ephemeral=True)

# ================== 1. نافذة التسجيل ==================
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
            "custom_title": "المبتدئ الأسطوري", "is_dev": (uid == MAIN_DEV_ID), "job": None, "last_job_claim": 0,
            "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10, "critical": 10, "magic": 10, "intelligence": 10, "defense": 10
        })
        emb = discord.Embed(title="👑 تم التسجيل بنجاح!", color=discord.Color.gold())
        emb.add_field(name="🪪 الاسم", value=f"`{self.name_in.value}`", inline=True)
        emb.add_field(name="⏳ العمر", value=f"`{age}`", inline=True)
        emb.add_field(name="🎁 الهدايا", value="5,000 🪙 | 20 💎", inline=False)
        await ctx.response.send_message(embed=emb)

# ================== 🛒 2. المتجر العام والمظلم ==================
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

# ================== ⚡ 3. تطوير المعدلات ==================
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

# ================== 🏰 4. قتال البرج ==================
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
    e_name = f"👑 BOSS طابق {floor_num}" if is_b else f"🧟 زومبي طابق {floor_num}"

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

# ================== 🏆 5. الليدربورد ==================
class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="الأغنى", value="rich", emoji="🪙"),
            discord.SelectOption(label="الأقوى", value="power", emoji="⚡"),
            discord.SelectOption(label="غزو الطوابق", value="floors", emoji="🏰")
        ]
        super().__init__(placeholder="🏆 اختر التصنيف...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        all_u = list(users_col.find())
        if v == "rich":
            all_u.sort(key=lambda x: x.get("balance",0) + x.get("bank",0), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🪙 `{u.get('balance',0):,}`" for i, u in enumerate(all_u[:10])])
            title = "🪙 ترتيب الأغنى"
        elif v == "power":
            all_u.sort(key=lambda x: x.get("power",0), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — ⚡ `{u.get('power',0):,}`" for i, u in enumerate(all_u[:10])])
            title = "⚡ ترتيب الأقوى"
        else:
            all_u.sort(key=lambda x: x.get("max_floor",1), reverse=True)
            txt = "\n".join([f"#{i+1} **{u.get('name','مقاتل')}** — 🏢 الطابق `{u.get('max_floor',1)}`" for i, u in enumerate(all_u[:10])])
            title = "🏰 ترتيب الطوابق"

        emb = discord.Embed(title=title, description=txt or "لا توجد بيانات", color=discord.Color.gold())
        vw = discord.ui.View()
        vw.add_item(LeaderboardSelect())
        await ctx.response.edit_message(embed=emb, view=vw)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())

# ================== 👑 6. لوحة المطور ==================
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

# ================== 🔟 أحداث وأوامر السلاش ==================
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

@bot.tree.command(name="الوظيفة", description="💼 عرض لوحة الوظائف والمهن الملكية")
async def job_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    u = users_col.find_one({"user_id": str(ctx.user.id)}) or {}
    cj = u.get("job")
    j_info = JOBS_CFG.get(cj, {"name": "عاطل عن العمل", "emoji": "👤"})
    emb = discord.Embed(
        title="🏢 ديوان الوظائف والمهن الإمبراطورية",
        description=f"👤 **وظيفتك الحالية:** {j_info['emoji']} **{j_info['name']}**\nاختر وظيفة من القائمة المنسدلة لمعاينة متطلباتها وراتبها اليومي.",
        color=discord.Color.dark_gold()
    )
    await ctx.response.send_message(embed=emb, view=JobMainView())

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

@bot.tree.command(name="الليدربورد", description="👑 عرض الترتيب")
async def leaderboard_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="👑 قاعة العظماء", color=discord.Color.gold()), view=LeaderboardView())

@bot.tree.command(name="لوحة_المطور", description="👑 لوحة التحكم للمطورين")
async def dev_panel_command(ctx: discord.Interaction):
    if not is_dev(ctx.user.id):
        await ctx.response.send_message("❌ هذا الأمر للمطورين فقط!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="👑 لوحة التحكم الإدارية", color=discord.Color.purple()), view=DevPanelView(), ephemeral=True)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
