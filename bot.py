import os, random, asyncio, pymongo, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta

# ==================== إعدادات القاعدة والبوت ====================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MAIN_DEV_ID = "1103985971638325269"

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col, guilds_col, devs_col = db["users"], db["guilds"], db["devs"]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
AUTO_BATTLES = {}
ACTIVE_GAMES = {}

# ==================== الدوابع المساعدة واختصار الأرقام ====================

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

def get_item_category(item_name: str) -> str:
    for cat in CATEGORIES:
        if cat in item_name:
            return cat
    return "سيف"

def format_num(n: int) -> str:
    """اختصار الأرقام الضخمة لتفادي خربشة لوحة الديسكورد"""
    if n >= 1_000_000_000_000:
        return f"{n/1_000_000_000_000:.2f}T"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def render_hp_bar(cur: int, max_hp: int) -> str:
    pct = max(0.0, min(1.0, cur / max_hp)) if max_hp > 0 else 0
    f = int(pct * 10)
    return f"`[{'█'*f}{'░'*(10-f)}]` `{format_num(cur)}/{format_num(max_hp)}`"

# ==================== إعدادات العتاد والمتاجر ====================

CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]
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

# ==================== إعدادات الأبطال الفانتازية ====================

HEROES_CFG = {
    "valerian": {"name": "فالريان، سيف الشمس", "gender": "ذكر", "emoji": "⚔️", "story": "فارس أسطوري ولد تحت نجم ملتهب ليدمر أعداء المملكة.", "base_power": 1200, "stats": {"leadership": 35, "attack": 30, "defense": 25, "aim": 10, "magic": 5, "intelligence": 15, "deception": 5}},
    "ignis": {"name": "إغنيس، سيد اللهب الأسود", "gender": "ذكر", "emoji": "🔥", "story": "ساحر ظلال قديم تحكم بعناصر النار المظلمة ليركع خصومه.", "base_power": 1350, "stats": {"magic": 40, "intelligence": 30, "attack": 25, "leadership": 10, "aim": 10, "defense": 10, "deception": 10}},
    "zephyr": {"name": "زفير، ظل الرماة", "gender": "ذكر", "emoji": "🎯", "story": "قناص الغابات المحرمة الذي لا تخطئ سهامه القاتلة.", "base_power": 1150, "stats": {"aim": 40, "deception": 25, "attack": 25, "intelligence": 15, "defense": 10, "magic": 5, "leadership": 10}},
    "lucian": {"name": "لوكيان، حارس العرش الفولاذي", "gender": "ذكر", "emoji": "🛡️", "story": "درع الإمبراطورية الأخير الذي صمد أمام أعظم الجيوش.", "base_power": 1250, "stats": {"defense": 45, "leadership": 25, "intelligence": 20, "attack": 15, "aim": 5, "magic": 5, "deception": 5}},
    "malakai": {"name": "مالاكاي، حائك الأوهام", "gender": "ذكر", "emoji": "🎭", "story": "سيد التجسس والدسائس الذي يتلاعب بالعقول والخداع.", "base_power": 1100, "stats": {"deception": 45, "intelligence": 35, "aim": 15, "magic": 15, "leadership": 10, "attack": 10, "defense": 5}},
    "athena": {"name": "أثينا، قائدة الفرسان الستة", "gender": "أنثى", "emoji": "👑", "story": "إمبراطورة الميدان التي تقود الفرسان بنصر محتوم.", "base_power": 1300, "stats": {"leadership": 40, "defense": 25, "attack": 25, "intelligence": 20, "aim": 10, "magic": 5, "deception": 5}},
    "serene": {"name": "سيرين، كاهنة القمر والبحار", "gender": "أنثى", "emoji": "🔮", "story": "سيدة السحر السماوي لنشر النور وتطهير الأرض.", "base_power": 1400, "stats": {"magic": 45, "intelligence": 30, "leadership": 20, "defense": 15, "aim": 10, "deception": 5, "attack": 10}},
    "lyra": {"name": "ليرا، عاصفة السهام", "gender": "أنثى", "emoji": "🏹", "story": "صيادة سريعة كالعاصفة تصيب أهدافها بدقة أسطورية.", "base_power": 1200, "stats": {"aim": 42, "attack": 28, "deception": 20, "intelligence": 15, "leadership": 10, "defense": 5, "magic": 10}},
    "morgana": {"name": "مورغانا، ملكة الدسائس", "gender": "أنثى", "emoji": "🖤", "story": "حاكمة الظلال التي تلاعبت بعقول الملوك والحكام.", "base_power": 1250, "stats": {"deception": 42, "magic": 30, "intelligence": 28, "aim": 10, "leadership": 10, "attack": 5, "defense": 5}},
    "hilda": {"name": "هيلدا، جدار الجليد", "gender": "أنثى", "emoji": "❄️", "story": "محاربة الشمال الأسطورية التي تسخر طاقة الجليد القاسية.", "base_power": 1280, "stats": {"defense": 40, "attack": 30, "leadership": 20, "intelligence": 15, "magic": 10, "aim": 10, "deception": 5}}
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

# ==================== بيانات الوظائف والألعاب ====================

JOBS_CFG = {
    "king": {"name": "الملك الإمبراطوري", "emoji": "👑", "salary": "50,000 - 100,000 🪙 + 25 💎", "desc": "حاكم العرش الأعلى للإمبراطورية العظمى.", "req": "👑 مساهمات عالية.", "perk": "🌟 أعلى راتب.", "min_gold": 50000, "max_gold": 100000, "diamonds": 25},
    "knight_commander": {"name": "قائد الفرسان", "emoji": "⚔️", "salary": "20,000 - 45,000 🪙 + 10 💎", "desc": "قيادة الجيوش والفرسان في الحروب.", "req": "🛡️ قوة عتادية عالية.", "perk": "🔥 زيادة الطاقة.", "min_gold": 20000, "max_gold": 45000, "diamonds": 10},
    "merchant": {"name": "التاجر الملكي", "emoji": "⚖️", "salary": "10,000 - 30,000 🪙 + 8 💎", "desc": "إدارة الأسواق والمتاجر.", "req": "🪙 سيولة مالية.", "perk": "📈 أرباح تجارية.", "min_gold": 10000, "max_gold": 30000, "diamonds": 8}
}

QUESTIONS_DATA = {"normal": [f"سؤال رقم {i}" for i in range(1, 10)]}
PUNISHMENTS_DATA = {"normal": ["نفّذ تحدي مضحك!"]}
RIDDLES = [("ما هو الشيء الذي كلما أخذت منه كبر؟", "الحفرة")]
MATH_EQUATIONS = [("5 + 7 * 2", "19")]
ANIME_DATA = [("نينجا يطمح ليصبح الهوكاجي", ["ناروتو"])]
CUT_TWEETS = ["هل المال يشتري السعادة؟"]
DECONSTRUCT_WORDS = [("إمبراطورية", "إ م ب ر ا ط و ر ي ة")]
FASTEST_WORDS = ["الإمبراطورية العظمى"]

# ==================== التسجيل والمتجر ====================

class RegisterModal(discord.ui.Modal, title="📜 استمارة التسجيل الإمبراطورية الملكية"):
    name_in = discord.ui.TextInput(label="الاسم الأسطوري", placeholder="اكتب اسم شخصيتك...", min_length=2, max_length=30)
    age_in = discord.ui.TextInput(label="العمر", placeholder="مثال: 25", min_length=1, max_length=4)
    gen_in = discord.ui.TextInput(label="الجنس", placeholder="ذكر / أنثى", min_length=3, max_length=4)

    async def on_submit(self, ctx: discord.Interaction):
        try:
            age = int(self.age_in.value.strip())
        except:
            await ctx.response.send_message("❌ أدخل رقماً صحيحاً للعمر!", ephemeral=True)
            return

        uid = str(ctx.user.id)
        users_col.insert_one({
            "user_id": uid, "name": self.name_in.value.strip(), "age": age, "gender": self.gen_in.value.strip(),
            "created_at": datetime.now(timezone.utc), "balance": 5000, "bank": 0, "diamonds": 20,
            "power": 100, "kills": 0, "max_floor": 1, "inventory": [], "equipped_gear": {}, "titles": ["المبتدئ الأسطوري"],
            "custom_title": "المبتدئ الأسطوري", "is_dev": (uid == MAIN_DEV_ID),
            "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10, "critical": 10, "magic": 10, "intelligence": 10, "defense": 10,
            "last_daily": None, "loan": 0, "chosen_hero": None, "hero_stats": {}, "guild_id": None, "job": None, "last_work": None
        })
        await ctx.response.send_message("✨ **تم تسجيلك بنجاح في الإمبراطورية!** استخدم /بروفايل للبدء.", ephemeral=True)

class GeneralItemSelect(discord.ui.Select):
    def __init__(self, cat: str):
        self.cat = cat
        opts = [discord.SelectOption(label=it["name"], value=it["id"], description=f"⚡+{it['power']:,} طاقة | 🪙{it['price']:,} ذهب", emoji=it["emoji"]) for it in GEAR_DATA[cat] if it["store"] == "general"]
        super().__init__(placeholder=f"⚔️ اختر العتاد من قسم [{cat}]...", options=opts[:25])

    async def callback(self, ctx: discord.Interaction):
        uid = str(ctx.user.id)
        item = next(i for i in GEAR_DATA[self.cat] if i["id"] == self.values[0])
        u = users_col.find_one({"user_id": uid}) or {}
        if u.get("balance", 0) < item["price"]:
            await ctx.response.send_message("❌ ذهبك لا يكفي للشراء!", ephemeral=True)
            return
        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -item["price"], "power": item["power"]}, "$push": {"inventory": item["name"]}})
        await ctx.response.send_message(f"🛍️ تم شراء **{item['name']}** بنجاح!", ephemeral=True)

class GeneralCategorySelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="🏰 اختر قسم العتاد الملكي...", options=[discord.SelectOption(label=c, value=c, emoji="🛡️") for c in CATEGORIES])

    async def callback(self, ctx: discord.Interaction):
        v = discord.ui.View()
        v.add_item(GeneralCategorySelect())
        v.add_item(GeneralItemSelect(self.values[0]))
        await ctx.response.edit_message(embed=discord.Embed(title=f"🏛️ السوق العام — [{self.values[0]}]", color=discord.Color.gold()), view=v)

class GeneralStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GeneralCategorySelect())

# ==================== كلاسات الحقيبة وارتداء العتاد ====================

class EquipGearSelect(discord.ui.Select):
    def __init__(self, inv_items: list):
        counts = {}
        for it in inv_items: counts[it] = counts.get(it, 0) + 1
        opts = [discord.SelectOption(label=f"{item_name} (x{count})", value=item_name, emoji="🗡️", description=f"تجهيز في [{get_item_category(item_name)}]") for item_name, count in counts.items()][:25]
        super().__init__(placeholder="🛡️ اختر عتاداً لارتدائه وتجهيزه...", options=opts if opts else [discord.SelectOption(label="الحقيبة فارغة", value="none")])

    async def callback(self, ctx: discord.Interaction):
        if self.values[0] == "none": return
        item_name = self.values[0]
        uid = str(ctx.user.id)
        cat = get_item_category(item_name)
        users_col.update_one({"user_id": uid}, {"$set": {f"equipped_gear.{cat}": item_name}})
        await ctx.response.send_message(f"⚔️ **ارتديت الآن:** `{item_name}` في خانة **[{cat}]**!", ephemeral=True)

class UnequipGearSelect(discord.ui.Select):
    def __init__(self, equipped_dict: dict):
        opts = [discord.SelectOption(label=f"خلع {cat}: {item_name}", value=cat, emoji="❌") for cat, item_name in equipped_dict.items() if item_name]
        super().__init__(placeholder="❌ اختر قطعة لخلعها من جسمك...", options=opts if opts else [discord.SelectOption(label="لا يوجد عتاد مرتدى", value="none")])

    async def callback(self, ctx: discord.Interaction):
        if self.values[0] == "none": return
        cat = self.values[0]
        uid = str(ctx.user.id)
        users_col.update_one({"user_id": uid}, {"$unset": {f"equipped_gear.{cat}": ""}})
        await ctx.response.send_message(f"🎒 تم خلع العتاد من خانة **[{cat}]**!", ephemeral=True)

class InventoryMainView(discord.ui.View):
    def __init__(self, inv_items: list, equipped_dict: dict):
        super().__init__(timeout=None)
        if inv_items: self.add_item(EquipGearSelect(inv_items))
        if equipped_dict: self.add_item(UnequipGearSelect(equipped_dict))

# ==================== ساحة المعارك المحدثة الواقعية (PVP ENGINE) ====================

def build_player_pvp_profile(uid, user_obj):
    u = users_col.find_one({"user_id": str(uid)}) or {}
    h_id = u.get("chosen_hero")
    h_info = HEROES_CFG.get(h_id, {}) if h_id else {}
    hero_stats = u.get("hero_stats", {})

    power = u.get("power", 100)
    atk = u.get("attack", 10) * 20 + power * 2 + hero_stats.get("attack", 0) * 15
    def_stat = u.get("defense", 10) * 15 + hero_stats.get("defense", 0) * 10
    max_hp = 1000 + def_stat * 5 + power * 5
    crit_chance = min(0.5, (u.get("critical", 10) + hero_stats.get("aim", 0)) / 100)
    evasion_chance = min(0.4, (u.get("evasion", 10) + hero_stats.get("deception", 0)) / 100)

    # تجريف العتاد المجهز للعرض المباشر
    equipped = u.get("equipped_gear", {})
    gear_items_formatted = []
    for cat in CATEGORIES:
        item = equipped.get(cat)
        if item:
            gear_items_formatted.append(f"`{cat}`: {item}")

    gear_display = " • ".join(gear_items_formatted) if gear_items_formatted else "`[بدون عتاد مجهز]`"
    
    # اختيار السلاح المجهز الرئيسي لسيناريو الضربات
    weapon = equipped.get("سيف") or equipped.get("خنجر") or equipped.get("مطرقة") or equipped.get("عصا سحرية") or "السلاح العادي"

    return {
        "user": user_obj,
        "name": u.get("name", user_obj.display_name),
        "max_hp": int(max_hp),
        "hp": int(max_hp),
        "atk": int(atk),
        "def": int(def_stat),
        "crit": crit_chance,
        "evasion": evasion_chance,
        "hero_name": h_info.get("name"),
        "hero_emoji": h_info.get("emoji", "🦸"),
        "is_alive": True,
        "gear_display": gear_display,
        "weapon": weapon
    }

def format_team_embed_field(team_name: str, team_profiles: list) -> str:
    lines = []
    for p in team_profiles:
        status_icon = "☠️ [صريع]" if not p["is_alive"] else "⚔️ [صامد]"
        hp_bar = render_hp_bar(p["hp"], p["max_hp"])
        
        lines.append(
            f"{p['hero_emoji']} **{p['name']}** {status_icon}\n"
            f"❤️ **الصحة:** {hp_bar}\n"
            f"💥 **الهجوم:** `{format_num(p['atk'])}` │ 🛡️ **الدفاع:** `{format_num(p['def'])}`\n"
            f"🎒 **العتاد المجهز:**\n{p['gear_display']}\n"
        )
    return "\n".join(lines)

async def start_pvp_battle(ctx, team1_users, team2_users, mode):
    t1_profiles = [build_player_pvp_profile(p.id, p) for p in team1_users]
    t2_profiles = [build_player_pvp_profile(p.id, p) for p in team2_users]

    channel = ctx.channel

    battle_emb = discord.Embed(
        title=f"⚔️ │ بدء الملحمة الدموية — طور [{mode}]",
        description="🩸 **الفرسان يتقدمون نحو الساحة! صليل السيوف يملأ المكان والعتاد يتوهج!**",
        color=discord.Color.dark_red()
    )

    battle_emb.add_field(name="🔴 الفريق الأول (A)", value=format_team_embed_field("A", t1_profiles), inline=False)
    battle_emb.add_field(name="🔵 الفريق الثاني (B)", value=format_team_embed_field("B", t2_profiles), inline=False)
    battle_emb.set_footer(text="⚡ القتال المباشر مستمر حتى سقوط الفريق المنافس...")

    battle_msg = await channel.send(embed=battle_emb)

    turn_counter = 0
    while any(p["is_alive"] for p in t1_profiles) and any(p["is_alive"] for p in t2_profiles):
        await asyncio.sleep(2.5)
        turn_counter += 1

        if turn_counter % 2 != 0:
            attacker_team = [p for p in t1_profiles if p["is_alive"]]
            defender_team = [p for p in t2_profiles if p["is_alive"]]
            atk_team_tag, def_team_tag = "🔴 (A)", "🔵 (B)"
        else:
            attacker_team = [p for p in t2_profiles if p["is_alive"]]
            defender_team = [p for p in t1_profiles if p["is_alive"]]
            atk_team_tag, def_team_tag = "🔵 (B)", "🔴 (A)"

        if not attacker_team or not defender_team: break

        attacker = random.choice(attacker_team)
        defender = random.choice(defender_team)

        if random.random() < defender["evasion"]:
            dialogue = f"💨 **مراوغة أسطورية!** حاول **{attacker['name']}** ضرب **{defender['name']}** بـ `{attacker['weapon']}`، لكن الأخير تفاداها بسرعة خاطفة!"
        else:
            is_crit = random.random() < attacker["crit"]
            raw_dmg = random.randint(int(attacker["atk"] * 0.8), int(attacker["atk"] * 1.2))
            dmg = max(50, raw_dmg - int(defender["def"] * 0.3))

            if is_crit:
                dmg = int(dmg * 1.8)
                dialogue = f"💥🩸 **ضربة قاضية وحارقة!** اندفع **{attacker['name']}** بـ `{attacker['weapon']}` وشق درع **{defender['name']}** بضرر قدره `{format_num(dmg)}` HP!"
            else:
                dialogue = f"🗡️ **هجوم مباشر!** سدد **{attacker['name']}** طعنة بـ `{attacker['weapon']}` نحو **{defender['name']}** أحدثت `{format_num(dmg)}` ضرر!"

            if attacker["hero_name"] and random.random() < 0.35:
                hero_dmg = random.randint(300, 800) + int(attacker["atk"] * 0.1)
                dmg += hero_dmg
                dialogue += f"\n{attacker['hero_emoji']} **تدخل البطل!** اندفع **{attacker['hero_name']}** وزاد الضرر السحري بـ `+{format_num(hero_dmg)}`!"

            defender["hp"] = max(0, defender["hp"] - dmg)

            if defender["hp"] <= 0:
                defender["is_alive"] = False
                dialogue += f"\n☠️ **سقوط المقاتل!** انكسر عتاد **{defender['name']}** وسقط صريعاً على أرض الساحة!"

        emb_update = discord.Embed(
            title=f"⚔️ │ المعركة الدموية الواقعية — الجولة [{turn_counter}]",
            description=f"📜 **مجريات القتال ({atk_team_tag} ➔ {def_team_tag}):**\n{dialogue}\n━━━━━━━━━━━━━━━━━━━━",
            color=discord.Color.red()
        )
        emb_update.add_field(name="🔴 الفريق الأول (A)", value=format_team_embed_field("A", t1_profiles), inline=False)
        emb_update.add_field(name="🔵 الفريق الثاني (B)", value=format_team_embed_field("B", t2_profiles), inline=False)
        emb_update.set_footer(text="🩸 جاري تنفيذ الجولة التالية...")

        try: await battle_msg.edit(embed=emb_update)
        except: break

    t1_won = any(p["is_alive"] for p in t1_profiles)
    winning_team = t1_profiles if t1_won else t2_profiles
    winning_name = "🔴 الفريق الأول (A)" if t1_won else "🔵 الفريق الثاني (B)"

    gold_reward = 15000 if mode == "1v1" else (25000 if mode == "2v2" else 40000)
    dia_reward = 5 if mode == "1v1" else (10 if mode == "2v2" else 15)

    winners_mentions = []
    for p in winning_team:
        winners_mentions.append(p["user"].mention)
        users_col.update_one(
            {"user_id": str(p["user"].id)},
            {"$inc": {"balance": gold_reward, "diamonds": dia_reward, "power": 100, "kills": 1}}
        )

    win_emb = discord.Embed(
        title="🏆 │ انتصار أسطوري في ساحة الملحمة!",
        description=(
            f"🎉 **فاز {winning_name} بعد معركة طاحنة وملحمية!**\n"
            f"👑 **الفائزون:** {', '.join(winners_mentions)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 **المكافأة:** `+{gold_reward:,}` ذهب │ `+{dia_reward}` 💎 ألماسة\n"
            f"⚡ **القوة والقتلات:** `+100` طاقة │ `+1` قتلة مسجلة"
        ),
        color=discord.Color.gold()
    )
    try: await battle_msg.edit(embed=win_emb)
    except: pass

class PvPBattleLobbyView(discord.ui.View):
    def __init__(self, host: discord.User, mode: str):
        super().__init__(timeout=120)
        self.host = host
        self.mode = mode
        self.required_per_team = 1 if mode == "1v1" else (2 if mode == "2v2" else 3)
        self.team1 = [host]
        self.team2 = []

    @discord.ui.button(label="⚔️ الانضمام للفريق الأول (A)", style=discord.ButtonStyle.primary, row=0)
    async def join_t1(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not is_user_registered(ctx.user.id):
            await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
            return
        if ctx.user in self.team1 or ctx.user in self.team2:
            await ctx.response.send_message("❌ أنت منضم بالفعل!", ephemeral=True)
            return
        if len(self.team1) >= self.required_per_team:
            await ctx.response.send_message("❌ الفريق مكتمل!", ephemeral=True)
            return
        self.team1.append(ctx.user)
        await self.update_lobby(ctx)

    @discord.ui.button(label="⚔️ الانضمام للفريق الثاني (B)", style=discord.ButtonStyle.danger, row=0)
    async def join_t2(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not is_user_registered(ctx.user.id):
            await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
            return
        if ctx.user in self.team1 or ctx.user in self.team2:
            await ctx.response.send_message("❌ أنت منضم بالفعل!", ephemeral=True)
            return
        if len(self.team2) >= self.required_per_team:
            await ctx.response.send_message("❌ الفريق مكتمل!", ephemeral=True)
            return
        self.team2.append(ctx.user)
        await self.update_lobby(ctx)

    @discord.ui.button(label="🚀 بدء المعركة فوراً", style=discord.ButtonStyle.success, row=1)
    async def start_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        if ctx.user.id != self.host.id:
            await ctx.response.send_message("❌ القائد صاحب التحدي فقط يستطيع البدء!", ephemeral=True)
            return
        if len(self.team1) != self.required_per_team or len(self.team2) != self.required_per_team:
            await ctx.response.send_message(f"❌ الفرق غير مكتملة! يلزم {self.required_per_team} لاعب في كل فريق.", ephemeral=True)
            return

        for child in self.children: child.disabled = True
        await ctx.response.edit_message(view=self)
        await start_pvp_battle(ctx, self.team1, self.team2, self.mode)

    async def update_lobby(self, ctx: discord.Interaction):
        t1_str = "\n".join([f"• {p.mention}" for p in self.team1]) or "لا يوجد"
        t2_str = "\n".join([f"• {p.mention}" for p in self.team2]) or "لا يوجد"

        emb = discord.Embed(
            title=f"⚔️ │ تجهيز ساحة المعارك — طور [{self.mode}]",
            description=(
                f"🔥 **تحدي ساحة القتال المباشرة!**\n"
                f"انضم إلى أحد الفريقين لجهيز عتادك وبدء القتال الواقعي.\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔴 **الفريق الأول (A) [{len(self.team1)}/{self.required_per_team}]:**\n{t1_str}\n\n"
                f"🔵 **الفريق الثاني (B) [{len(self.team2)}/{self.required_per_team}]:**\n{t2_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.red()
        )
        await ctx.response.edit_message(embed=emb, view=self)

class BattlesModeSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="مواجهة 1v1 (قتال فردي مدمي)", value="1v1", emoji="🗡️", description="مواجهة واقعية تعرض العتاد وشريط الصحة القتالي"),
            discord.SelectOption(label="مواجهة 2v2 (قتال ثنائي دامي)", value="2v2", emoji="⚔️", description="معركة ثنائية بالأسلحة المجهزة"),
            discord.SelectOption(label="مواجهة 3v3 (ملحمة الفرسان)", value="3v3", emoji="🛡️", description="حرب طاحنة بين 6 مقاتلين بعتادهم")
        ]
        super().__init__(placeholder="⚔️ اختر نمط المعركة للبدء...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        mode = self.values[0]
        lobby_view = PvPBattleLobbyView(ctx.user, mode)
        emb = discord.Embed(
            title=f"⚔️ │ غرفة التحدي — طور [{mode}]",
            description=f"🔥 أطلق **{ctx.user.mention}** تحدياً جديداً! انضموا للفريقين لبدء الملحمة الواقعية.",
            color=discord.Color.red()
        )
        await ctx.response.send_message(embed=emb, view=lobby_view)

class BattlesMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(BattlesModeSelect())

# ==================== تسجيل كافة الأوامر للبوت ====================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✨ تم مزامنة البوت بنجاح! يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ المزامنة: {e}")

@bot.tree.command(name="تسجيل", description="📜 تسجيل حساب أسطوري جديد في الإمبراطورية")
async def register_command(ctx: discord.Interaction):
    if is_user_registered(ctx.user.id):
        await ctx.response.send_message("⚠️ أنت مسجل بالفعل وبطل من أبطال المملكة!", ephemeral=True)
        return
    await ctx.response.send_modal(RegisterModal())

@bot.tree.command(name="المتجر_العام", description="🏛️ فتح المتجر العام لشراء الأسلحة والدروع")
async def general_store(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل` لتفتح أبواب المتجر!", ephemeral=True)
        return
    await ctx.response.send_message(embed=discord.Embed(title="🏛️ السوق العام", description="اختر المعدات القتالية من المنيو بالأسفل:", color=discord.Color.gold()), view=GeneralStoreView())

@bot.tree.command(name="بروفايل", description="🪪 عرض بطاقة المقاتل الفخمة والشاملة")
async def profile_command(ctx: discord.Interaction, target: discord.User = None):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    target_user = target or ctx.user
    u = users_col.find_one({"user_id": str(target_user.id)})
    if not u:
        await ctx.response.send_message("❌ هذا المستخدم غير مسجل!", ephemeral=True)
        return

    emb = discord.Embed(
        title=f"👑 │ بطاقة المقاتل — {u.get('name', 'غير معروف')}",
        description=f"✨ **اللقب:** `[ {u.get('custom_title', 'المبتدئ الأسطوري')} ]`\n━━━━━━━━━━━━━━━━━━━━",
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=target_user.display_avatar.url)
    emb.add_field(name="💰 **الثروة**", value=f"• الكاش: `{format_num(u.get('balance', 0))}` 🪙\n• الألماس: `{format_num(u.get('diamonds', 0))}` 💎", inline=True)
    emb.add_field(name="📊 **الإحصائيات**", value=f"• القوة: `{format_num(u.get('power', 0))}` ⚡\n• القتلات: `{format_num(u.get('kills', 0))}` 🩸", inline=True)
    await ctx.response.send_message(embed=emb)

@bot.tree.command(name="الحقيبة", description="🎒 عرض العتاد الممتلك وخانات الارتداء الفخمة")
async def inventory_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    uid = str(ctx.user.id)
    u = users_col.find_one({"user_id": uid}) or {}
    inv = u.get("inventory", [])
    equipped = u.get("equipped_gear", {})

    slots_txt = [f"• **{cat}:** {equipped.get(cat, '`[فارغ]`')}" for cat in CATEGORIES]

    emb = discord.Embed(
        title=f"🎒 │ حقيبة المقاتل وخانات التجهيز والارتداء",
        description=(
            f"🛡️ **العتاد المرتدى حالياً على الجسم:**\n" + "\n".join(slots_txt) + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 **المعدات بالحقيبة:** `{len(inv)}` قطعة"
        ),
        color=discord.Color.gold()
    )
    await ctx.response.send_message(embed=emb, view=InventoryMainView(inv, equipped), ephemeral=True)

@bot.tree.command(name="المعارك", description="⚔️ قاعة المعارك المباشرة والقتال الجماعي (1v1 / 2v2 / 3v3)")
async def pvp_battles_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل` لتشارك في ساحة المعارك!", ephemeral=True)
        return

    emb = discord.Embed(
        title="⚔️ │ ساحة المعارك والقتال الجماعي — IMPERIAL ARENA",
        description="اختر نمط المعركة المطلوبة لخوض قتال ملحمي واقعي يُعرض فيه عتاد فرسان القتال وتفاصيل صحتك الضخمة بدون خربشة!",
        color=discord.Color.red()
    )
    await ctx.response.send_message(embed=emb, view=BattlesMainView())

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
