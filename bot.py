import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import pymongo
from datetime import datetime, timezone

# ================== إعدادات الاتصال وقاعدة البيانات ==================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# الآيدي الخاص بالمطور الرئيسي والمالك للإمبراطورية
MAIN_DEV_ID = "1103985971638325269"

# ربط قاعدة البيانات مع تحديد مهلة اتصال لمنع تعليق الاستجابة
try:
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["game_database"]
    users_col = db["users"]
    guilds_col = db["guilds"]
    devs_col = db["devs"]
except Exception as e:
    print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== دالة التحقق من التسجيل والمطورين ==================
def is_user_registered(user_id: str) -> bool:
    try:
        return users_col.find_one({"user_id": str(user_id)}) is not None
    except Exception as e:
        print(f"❌ خطأ فحص التسجيل: {e}")
        return False

def is_dev(user_id: str) -> bool:
    try:
        str_id = str(user_id)
        if str_id == MAIN_DEV_ID:
            return True
        user_data = users_col.find_one({"user_id": str_id})
        if user_data and user_data.get("is_dev", False):
            return True
        return devs_col.find_one({"user_id": str_id}) is not None
    except Exception as e:
        print(f"❌ خطأ فحص صلاحيات المطور: {e}")
        return str(user_id) == MAIN_DEV_ID

# ================== 🏰 قاعدة بيانات المتاجر المحدثة ==================
CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]
DARK_RANKS = ["مشعوذ الظلال", "السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي", "حاكم الظلمات"]

GEAR_DATA = {}
ALL_GENERAL_ITEMS = []
ALL_DARK_ITEMS = []

for cat in CATEGORIES:
    GEAR_DATA[cat] = []
    
    # 25 قطعة للمتجر العام
    for i in range(1, 26):
        if i <= 5:
            rank, emoji = "مبتدئ", "🟢"
        elif i <= 10:
            rank, emoji = "فولاذي", "🪙"
        elif i <= 15:
            rank, emoji = "ملكي", "👑"
        elif i <= 20:
            rank, emoji = "أسطوري", "🌟"
        else:
            rank, emoji = "إمبراطوري", "🐉"

        item = {
            "id": f"gen_{cat}_{i}",
            "name": f"{emoji} {cat} [{rank}] T{i}",
            "rank": rank,
            "emoji": emoji,
            "power": i * 50,
            "price": i * 400,
            "currency": "gold",
            "store": "general"
        }
        GEAR_DATA[cat].append(item)
        ALL_GENERAL_ITEMS.append(item)

    # 25 قطعة للمتجر المظلم
    for i in range(1, 26):
        if i <= 5:
            rank, emoji = "مشعوذ الظلال", "🌑"
        elif i <= 10:
            rank, emoji = "السفاح القرمزي", "🩸"
        elif i <= 15:
            rank, emoji = "الجحيم القاتل", "🔥"
        elif i <= 20:
            rank, emoji = "الشيطان الأبدي", "😈"
        else:
            rank, emoji = "حاكم الظلمات", "☠️"

        item = {
            "id": f"dark_{cat}_{i}",
            "name": f"💀 {cat} [{rank}] T{i}",
            "rank": rank,
            "emoji": emoji,
            "power": i * 250,
            "price": i * 8,
            "currency": "diamonds",
            "store": "dark"
        }
        GEAR_DATA[cat].append(item)
        ALL_DARK_ITEMS.append(item)

# ================== 1. نافذة منيو التسجيل (Modal) ==================
class RegisterModal(discord.ui.Modal, title="📜 استمارة التسجيل في الإمبراطورية"):
    name_input = discord.ui.TextInput(label="الاسم الخاص بك", placeholder="أدخل اسم شخصيتك...", min_length=2, max_length=30, required=True)
    age_input = discord.ui.TextInput(label="العمر (أرقام فقط كحد أقصى 3000)", placeholder="مثال: 25", min_length=1, max_length=4, required=True)
    gender_input = discord.ui.TextInput(label="الجنس (اكتب: ذكر أو أنثى)", placeholder="ذكر / أنثى", min_length=3, max_length=4, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        registered = await asyncio.to_thread(is_user_registered, user_id)
        if registered:
            return await interaction.response.send_message("❌ أنت مسجل بالفعل في الإمبراطورية!", ephemeral=True)

        try:
            age = int(self.age_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة العمر كأرقام فقط!", ephemeral=True)

        if age < 1 or age > 3000:
            return await interaction.response.send_message("❌ يجب أن يكون العمر بين 1 و 3000 سنة!", ephemeral=True)

        gender = self.gender_input.value.strip()
        if gender not in ["ذكر", "أنثى"]:
            return await interaction.response.send_message("❌ يرجى كتابة كلمة ذكر أو أنثى فقط!", ephemeral=True)

        is_dev_user = (user_id == MAIN_DEV_ID)

        new_user = {
            "user_id": user_id,
            "name": self.name_input.value.strip(),
            "age": age,
            "gender": gender,
            "created_at": datetime.now(timezone.utc),
            "balance": 5000,
            "bank": 0,
            "diamonds": 20,
            "power": 100,
            "kills": 0,
            "max_floor": 1,
            "inventory": [],
            "titles": ["المبتدئ الأسطوري"],
            "custom_title": "المبتدئ الأسطوري",
            "is_dev": is_dev_user,
            "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
            "critical": 10, "magic": 10, "intelligence": 10, "defense": 10
        }
        
        await asyncio.to_thread(users_col.insert_one, new_user)

        embed_success = discord.Embed(title="👑 أهلاً بك في عرش الإمبراطورية!", description="تمت معالجة وثيقة هويتك بنجاح.", color=discord.Color.gold())
        embed_success.add_field(name="🪪 الاسم", value=f"`{self.name_input.value.strip()}`", inline=True)
        embed_success.add_field(name="⏳ العمر", value=f"`{age}` سنة", inline=True)
        embed_success.add_field(name="👤 الجنس", value=f"`{gender}`", inline=True)
        embed_success.add_field(name="🎁 مكافأة البداية", value="• `5,000` 🪙 ذهب\n• `20` 💎 ألماس", inline=False)
        await interaction.response.send_message(embed=embed_success, ephemeral=False)

# ================== 🛒 2. المتجر العام ==================
class GeneralItemSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        items = [item for item in GEAR_DATA[category] if item["store"] == "general"][:25]
        options = [
            discord.SelectOption(
                label=item["name"],
                value=item["id"],
                description=f"الرتبة: {item['rank']} | ⚡ +{item['power']:,} | 🪙 {item['price']:,}",
                emoji=item["emoji"]
            ) for item in items
        ]
        super().__init__(placeholder=f"⚔️ تصفح عتاد [{category}] (25 قطعة)...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        selected_id = self.values[0]
        selected_item = next(item for item in GEAR_DATA[self.category] if item["id"] == selected_id)
        
        user_data = await asyncio.to_thread(users_col.find_one, {"user_id": user_id}) or {}
        if user_data.get("balance", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ رصيدك الذهبي لا يكفي! تحتاج `{selected_item['price']:,}` 🪙", ephemeral=True)
        
        def _update():
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"balance": -selected_item["price"], "power": selected_item["power"]},
                    "$push": {"inventory": selected_item["name"]}
                }
            )
        await asyncio.to_thread(_update)

        embed_bought = discord.Embed(
            title="🛍️ صفقة ناجحة — المتجر الإمبراطوري",
            description=f"مبروك! حصلت على **{selected_item['name']}**\n• ⚡ **القوة المضافة:** `+{selected_item['power']:,}`\n• 🪙 **المبلغ المدفوع:** `{selected_item['price']:,}` ذهبة",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed_bought, ephemeral=True)

class GeneralCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"قسم: {cat}", value=cat, emoji="🛡️") for cat in CATEGORIES]
        super().__init__(placeholder="🏰 اختر قسم العتاد للعرض...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        view = discord.ui.View()
        view.add_item(GeneralCategorySelect())
        view.add_item(GeneralItemSelect(cat))
        
        embed = discord.Embed(
            title=f"🏛️ المتجر الإمبراطوري العام — قسم [{cat}]",
            description="✨ **اختر المعدات المطلوبة للشراء بالعملات الذهبية (25 مستوى لكل فئة)**",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class GeneralStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GeneralCategorySelect())

# ================== 🔮 3. المتجر المظلم ==================
class DarkItemSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        items = [item for item in GEAR_DATA[category] if item["store"] == "dark"][:25]
        options = [
            discord.SelectOption(
                label=item["name"],
                value=item["id"],
                description=f"الرتبة: {item['rank']} | ⚡ +{item['power']:,} | 💎 {item['price']:,}",
                emoji=item["emoji"]
            ) for item in items
        ]
        super().__init__(placeholder=f"🔮 عتاد الظلال المحرم [{category}] (25 قطعة)...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        selected_id = self.values[0]
        selected_item = next(item for item in GEAR_DATA[self.category] if item["id"] == selected_id)
        
        user_data = await asyncio.to_thread(users_col.find_one, {"user_id": user_id}) or {}
        if user_data.get("diamonds", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ ألماس غير كافٍ! تحتاج إلى `{selected_item['price']:,}` 💎 ألماس.", ephemeral=True)
        
        def _update():
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"diamonds": -selected_item["price"], "power": selected_item["power"]},
                    "$push": {"inventory": selected_item["name"]}
                }
            )
        await asyncio.to_thread(_update)

        embed_buy = discord.Embed(
            title="⚡ امتلاك عتاد محرم أسطوري!",
            description=f"لقد حصلت على **{selected_item['name']}** برتبة **[{selected_item['rank']}]**!",
            color=discord.Color.dark_purple()
        )
        await interaction.response.send_message(embed=embed_buy, ephemeral=True)

class DarkCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"عتاد محرم: {cat}", value=cat, emoji="🌑") for cat in CATEGORIES]
        super().__init__(placeholder="👁️ اختر قسم خزنة الظلال السري...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        view = discord.ui.View()
        view.add_item(DarkCategorySelect())
        view.add_item(DarkItemSelect(cat))
        
        embed = discord.Embed(
            title=f"🖤 خزنة الظلال المحرمة — [{cat}]",
            description="⚠️ **سوق الأسلحة والعتاد المحرم (تتطلب 💎 الألماس فقط)**",
            color=discord.Color.from_rgb(45, 0, 60)
        )
        await interaction.response.edit_message(embed=embed, view=view)

class DarkStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DarkCategorySelect())

# ================== ⚡ 4. نظام تطوير المعدلات ==================
STATS_CONFIG = {
    "aim": {"name": "التصويب", "emoji": "🎯", "cost": 100},
    "evasion": {"name": "المراوغة", "emoji": "💨", "cost": 100},
    "attack": {"name": "الهجوم", "emoji": "🗡️", "cost": 100},
    "accuracy": {"name": "الدقة", "emoji": "👁️", "cost": 100},
    "critical": {"name": "الضربات القاتلة", "emoji": "💥", "cost": 100},
    "magic": {"name": "السحر", "emoji": "🔮", "cost": 100},
    "intelligence": {"name": "الذكاء", "emoji": "🧠", "cost": 100},
    "defense": {"name": "الدفاع", "emoji": "🛡️", "cost": 100}
}

class StatUpgradeModal(discord.ui.Modal):
    def __init__(self, stat_key: str, stat_info: dict):
        super().__init__(title=f"🚀 ترقية معدل: {stat_info['name']}")
        self.stat_key = stat_key
        self.stat_info = stat_info

        self.amount_input = discord.ui.TextInput(
            label=f"عدد النقاط (سعر النقطة: {stat_info['cost']} 🪙)",
            placeholder="أدخل عدد النقاط...",
            min_length=1, max_length=20, required=True
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            points = int(self.amount_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة أرقام صحيحة!", ephemeral=True)

        if points <= 0:
            return await interaction.response.send_message("❌ يجب أن تكون النقاط أكبر من 0!", ephemeral=True)

        total_cost = points * self.stat_info["cost"]
        user_data = await asyncio.to_thread(users_col.find_one, {"user_id": user_id}) or {}

        if user_data.get("balance", 0) < total_cost:
            return await interaction.response.send_message(f"❌ لا تملك ذهبًا كافيًا! التكلفة: `{total_cost:,}` 🪙", ephemeral=True)

        def _update():
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": -total_cost, self.stat_key: points, "power": points * 10}}
            )
        await asyncio.to_thread(_update)

        embed_success = discord.Embed(
            title=f"🔥 انطلاق القوة القتالية! — {self.stat_info['name']}",
            description=f"تم زيادة **{self.stat_info['emoji']} {self.stat_info['name']}** بـ `+{points:,}` نقطة!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed_success, ephemeral=False)

class StatSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=info["name"], value=key, description=f"تكلفة النقطة: {info['cost']} 🪙", emoji=info["emoji"])
            for key, info in STATS_CONFIG.items()
        ]
        super().__init__(placeholder="🔥 اختر المعدل لتطويره...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        await interaction.response.send_modal(StatUpgradeModal(selected_key, STATS_CONFIG[selected_key]))

class StatsUpgradeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(StatSelect())

# ================== 🏰 5. محرك قتال البرج ==================

def render_hp_bar(current: int, maximum: int, length: int = 10) -> str:
    pct = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0
    filled = int(pct * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`[{bar}]` {current:,}/{maximum:,} HP"

def get_floor_enemy_info(floor_num: int) -> dict:
    is_boss = (floor_num % 10 == 0)
    is_miniboss = (floor_num % 5 == 0 and not is_boss)

    if is_boss:
        names = ["💀 ملك الموت والمقابر", "🐉 التنين الإمبراطوري المظلم", "😈 شيطان الجحيم الأبدي"]
        quotes = ["لن تتخطى هذا الطابق حياً يا حشرة!", "دماؤك ستكون قرباناً لعرش الظلام!"]
        p_quotes = ["سيف الإمبراطورية سيشق جمجمتك اليوم!", "قوتي ستسحق عرشك المظلم!"]
        name = f"👑 [BOSS الطابق {floor_num}] {random.choice(names)}"
        hp = 500 + (floor_num * 350)
        atk = 40 + (floor_num * 30)
        dfs = 10 + (floor_num * 15)
        color = discord.Color.purple()
    elif is_miniboss:
        names = ["👹 قائد جيش الزومبي", "🧟‍♂️ زومبي الدماء المتجمدة", "🩸 السفاح الهائج"]
        quotes = ["اخترقت طوابق كثيرة... لكن هنا نهايتك!"]
        p_quotes = ["أنت مجرد عقبة صغيرة في طريق قمتي!"]
        name = f"👹 [زعيم مصغر] {random.choice(names)}"
        hp = 300 + (floor_num * 200)
        atk = 25 + (floor_num * 20)
        dfs = 5 + (floor_num * 10)
        color = discord.Color.dark_red()
    else:
        names = ["🧟 زومبي مستنقع الأرواح", "🧟‍♀️ زومبي الظلال المظلمة"]
        quotes = ["غغغغ... دماء جديدة!"]
        p_quotes = ["ابتعد عن طريقي أيها الزومبي!"]
        name = f"🧟 [طابق {floor_num}] {random.choice(names)}"
        hp = 150 + (floor_num * 100)
        atk = 15 + (floor_num * 12)
        dfs = 2 + (floor_num * 5)
        color = discord.Color.dark_green()

    return {
        "name": name, "is_boss": is_boss, "is_miniboss": is_miniboss,
        "hp": hp, "max_hp": hp, "atk": atk, "dfs": dfs,
        "enemy_quote": random.choice(quotes), "player_quote": random.choice(p_quotes), "color": color
    }

async def process_floor_battle(interaction: discord.Interaction, floor_num: int, is_boss_only: bool = False):
    user_id = str(interaction.user.id)
    user_data = await asyncio.to_thread(users_col.find_one, {"user_id": user_id}) or {}

    if floor_num > 500:
        if not interaction.response.is_done():
            return await interaction.response.send_message("🏆 **تهانينا العظيمة!** لقد أتممت فتح جميع الـ 500 طابق بالكامل!", ephemeral=True)
        else:
            return await interaction.followup.send("🏆 **تهانينا العظيمة!** لقد أتممت فتح جميع الـ 500 طابق بالكامل!", ephemeral=True)

    enemy = get_floor_enemy_info(floor_num)
    p_attack = user_data.get("attack", 10) * 12 + user_data.get("power", 100) * 1.2
    p_defense = user_data.get("defense", 10) * 8 + 20
    p_hp = 300 + user_data.get("defense", 10) * 25 + user_data.get("power", 100) * 2
    p_max_hp = p_hp

    e_name = enemy["name"]
    e_quote = enemy["enemy_quote"]
    p_quote = enemy["player_quote"]
    p_name = user_data.get("name", "المقاتل")

    embed = discord.Embed(
        title=f"⚔️ ساحة معركة البرج — الطابق [{floor_num}/500]",
        description=f"⚔️ **تواجَه الآن ضد:** `{e_name}`\n💬 **الخصم:** {e_quote}\n🗣️ **{p_name}:** {p_quote}\n",
        color=enemy["color"]
    )
    embed.add_field(name=f"👤 {p_name}", value=render_hp_bar(int(p_hp), int(p_max_hp)), inline=True)
    embed.add_field(name=f"👾 {e_name}", value=render_hp_bar(int(enemy['hp']), int(enemy['max_hp'])), inline=True)

    if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=False)
        message = await interaction.original_response()
    else:
        message = await interaction.followup.send(embed=embed, ephemeral=False)

    logs = []
    round_cnt = 1
    
    while p_hp > 0 and enemy["hp"] > 0 and round_cnt <= 5:
        await asyncio.sleep(1.2)
        dmg_to_enemy = max(10, int(p_attack - (enemy["dfs"] * 0.4)) + random.randint(-15, 25))
        if random.random() < (user_data.get("critical", 10) / 100):
            dmg_to_enemy = int(dmg_to_enemy * 1.8)
            logs.append(f"💥 **ضربة قاتلة!** وجهت `{dmg_to_enemy:,}` ضرر للخصم!")
        else:
            logs.append(f"🗡️ سددت ضربة بـ `{dmg_to_enemy:,}` ضرر!")
            
        enemy["hp"] -= dmg_to_enemy
        if enemy["hp"] <= 0:
            enemy["hp"] = 0
            break

        dmg_to_player = max(5, int(enemy["atk"] - (p_defense * 0.3)) + random.randint(-10, 15))
        p_hp -= dmg_to_player
        if p_hp <= 0:
            p_hp = 0
            logs.append("🩸 **تلقيت ضربة قاضية!** سقطت في الطابق.")
            break
        else:
            logs.append(f"🩸 هاجمك الخصم بـ `{dmg_to_player:,}` ضرر!")

        round_cnt += 1

    if enemy["hp"] <= 0:
        gold_reward = floor_num * 300 + random.randint(200, 800)
        diamond_reward = random.randint(1, 4) if (enemy["is_boss"] or random.random() < 0.25) else 0
        
        dropped_gear = None
        gear_msg = "لا يوجد عتاد مسقط"
        
        if enemy["is_boss"] and random.random() < 0.4:
            dropped_gear = random.choice(ALL_DARK_ITEMS)
            gear_msg = f"🔮 **عتاد محرم أسطوري:** `{dropped_gear['name']}`"
        elif random.random() < 0.3:
            dropped_gear = random.choice(ALL_GENERAL_ITEMS)
            gear_msg = f"🗡️ **عتاد إمبراطوري:** `{dropped_gear['name']}`"

        update_doc = {
            "$inc": {"balance": gold_reward, "diamonds": diamond_reward, "kills": 1, "power": 30},
            "$set": {"max_floor": floor_num + 1}
        }
        if dropped_gear:
            update_doc["$push"] = {"inventory": dropped_gear["name"]}
            update_doc["$inc"]["power"] += dropped_gear["power"]

        def _update_win():
            users_col.update_one({"user_id": user_id}, update_doc)
        await asyncio.to_thread(_update_win)

        embed_win = discord.Embed(
            title=f"🎉 **انتصار ساحق في الطابق [{floor_num}]!**",
            description=f"👑 **تم سحق {enemy['name']} بنجاح!**\n🎁 **المكافآت:** 🪙 `{gold_reward:,}` | 💎 `{diamond_reward}` | {gear_msg}\n",
            color=discord.Color.gold()
        )
        embed_win.add_field(name="📜 سجل القتال النهائي", value="\n".join(logs[-4:]), inline=False)
        
        view = discord.ui.View()
        next_btn = discord.ui.Button(label=f"➡️ خوض القتال في الطابق [{floor_num + 1}] فوراً", style=discord.ButtonStyle.success, emoji="⚔️")
        
        async def next_floor_callback(btn_inter: discord.Interaction):
            if str(btn_inter.user.id) != user_id:
                return await btn_inter.response.send_message("❌ هذه المعركة ليست لك!", ephemeral=True)
            await process_floor_battle(btn_inter, floor_num + 1)

        next_btn.callback = next_floor_callback
        view.add_item(next_btn)
        await message.edit(embed=embed_win, view=view)
    else:
        embed_lose = discord.Embed(title=f"💀 **هزيمة في الطابق [{floor_num}]!**", description=f"لم تستطع الصمود بوجه `{enemy['name']}`.", color=discord.Color.red())
        embed_lose.add_field(name="📜 مجريات اللحظات الأخيرة", value="\n".join(logs[-4:]), inline=False)
        await message.edit(embed=embed_lose)

# ================== 🎒 view الحقيبة ==================
class InventoryView(discord.ui.View):
    def __init__(self, user_data: dict):
        super().__init__()
        inv = user_data.get("inventory", [])
        if not inv:
            self.add_item(discord.ui.Button(label="الحقيبة فارغة حالياً", disabled=True))
        else:
            options = [discord.SelectOption(label=item[:25], value=f"{idx}_{item}", emoji="🎒") for idx, item in enumerate(inv[:25])]
            select = discord.ui.Select(placeholder="🎒 اختر قطعة عتاد لمعاينتها...", options=options)
            
            async def inv_callback(interaction: discord.Interaction):
                item_name = select.values[0].split("_", 1)[1]
                embed = discord.Embed(title="🔍 معاينة قطعة العتاد", description=f"القطعة: **{item_name}**", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)

            select.callback = inv_callback
            self.add_item(select)

# ================== 🏰 6. القائمة الرئيسية لأمر /الطوابق ==================
class TowerMainSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="بدء المغامرة (تسلق البرج)", value="start_adv", emoji="⚔️"),
            discord.SelectOption(label="قتال الزعيم (Boss)", value="boss_fight", emoji="💀"),
            discord.SelectOption(label="المتجر العادي", value="gen_store", emoji="🛒"),
            discord.SelectOption(label="المتجر المظلم", value="dark_store", emoji="🔮"),
            discord.SelectOption(label="تطوير معداتي", value="upgrade_stats", emoji="⚡"),
            discord.SelectOption(label="حقيبتي والعتاد", value="my_inventory", emoji="🎒")
        ]
        super().__init__(placeholder="🏰 اختر الإجراء المطلوب في برج الطوابق...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = await asyncio.to_thread(users_col.find_one, {"user_id": user_id}) or {}
        val = self.values[0]

        if val == "start_adv":
            await process_floor_battle(interaction, user_data.get("max_floor", 1))
        elif val == "boss_fight":
            cf = user_data.get("max_floor", 1)
            boss_f = cf if cf % 10 == 0 else ((cf // 10 + 1) * 10)
            await process_floor_battle(interaction, boss_f, is_boss_only=True)
        elif val == "gen_store":
            await interaction.response.send_message(embed=discord.Embed(title="🏛️ متجر الإمبراطورية الملكي العام", color=discord.Color.gold()), view=GeneralStoreView(), ephemeral=True)
        elif val == "dark_store":
            await interaction.response.send_message(embed=discord.Embed(title="🔮 المتجر المظلم المحرم — Dark Sanctuary", color=discord.Color.from_rgb(20, 0, 35)), view=DarkStoreView(), ephemeral=True)
        elif val == "upgrade_stats":
            await interaction.response.send_message(embed=discord.Embed(title="✨ مذبح الصقل وتطوير القوى الإمبراطورية", color=discord.Color.red()), view=StatsUpgradeView(), ephemeral=True)
        elif val == "my_inventory":
            inv = user_data.get("inventory", [])
            embed = discord.Embed(title=f"🎒 حقيبة المقاتل [{user_data.get('name', 'المقاتل')}]", description="\n".join([f"• {i}" for i in inv[-10:]]) if inv else "الحقيبة فارغة.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=InventoryView(user_data), ephemeral=True)

class TowerMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TowerMainSelect())

# ================== ⚔️ 7. نظام المعارك المباشرة PvP ==================

class BattleLobbyView(discord.ui.View):
    def __init__(self, mode: str, host_user: discord.User):
        super().__init__(timeout=300)
        self.mode = mode
        self.team_size = int(mode[0])
        self.team_red = [host_user]
        self.team_blue = []
        self.host_user = host_user

    def is_full(self) -> bool:
        return len(self.team_red) == self.team_size and len(self.team_blue) == self.team_size

    def get_embed(self) -> discord.Embed:
        red_names = "\n".join([f"• 🔴 **{u.display_name}**" for u in self.team_red]) if self.team_red else "بانتظار المقاتلين..."
        blue_names = "\n".join([f"• 🔵 **{u.display_name}**" for u in self.team_blue]) if self.team_blue else "بانتظار المقاتلين..."
        
        embed = discord.Embed(title=f"⚔️ حلبة الصراع — معركة [{self.mode}]", color=discord.Color.dark_gold())
        embed.add_field(name=f"🔴 الفريق الأحمر ({len(self.team_red)}/{self.team_size})", value=red_names, inline=True)
        embed.add_field(name=f"🔵 الفريق الأزرق ({len(self.team_blue)}/{self.team_size})", value=blue_names, inline=True)
        return embed

    @discord.ui.button(label="انضمام للفريق الأحمر 🔴", style=discord.ButtonStyle.danger)
    async def join_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        reg = await asyncio.to_thread(is_user_registered, str(interaction.user.id))
        if not reg:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
        if interaction.user in self.team_red or interaction.user in self.team_blue:
            return await interaction.response.send_message("⚠️ أنت مشارك بالفعل!", ephemeral=True)
        if len(self.team_red) >= self.team_size:
            return await interaction.response.send_message("❌ الفريق مكتمل!", ephemeral=True)

        self.team_red.append(interaction.user)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
        if self.is_full():
            await self.start_pvp_battle(interaction)

    @discord.ui.button(label="انضمام للفريق الأزرق 🔵", style=discord.ButtonStyle.primary)
    async def join_blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        reg = await asyncio.to_thread(is_user_registered, str(interaction.user.id))
        if not reg:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
        if interaction.user in self.team_red or interaction.user in self.team_blue:
            return await interaction.response.send_message("⚠️ أنت مشارك بالفعل!", ephemeral=True)
        if len(self.team_blue) >= self.team_size:
            return await interaction.response.send_message("❌ الفريق مكتمل!", ephemeral=True)

        self.team_blue.append(interaction.user)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
        if self.is_full():
            await self.start_pvp_battle(interaction)

    async def start_pvp_battle(self, interaction: discord.Interaction):
        def _get_data():
            r_data = [users_col.find_one({"user_id": str(u.id)}) or {} for u in self.team_red]
            b_data = [users_col.find_one({"user_id": str(u.id)}) or {} for u in self.team_blue]
            return r_data, b_data

        red_data_list, blue_data_list = await asyncio.to_thread(_get_data)

        red_atk = sum(d.get("attack", 10) * 12 + d.get("power", 100) * 1.1 for d in red_data_list)
        red_def = sum(d.get("defense", 10) * 8 + 20 for d in red_data_list)
        red_hp = int(sum(400 + d.get("defense", 10) * 30 + d.get("power", 100) * 2.5 for d in red_data_list))
        red_max_hp = red_hp

        blue_atk = sum(d.get("attack", 10) * 12 + d.get("power", 100) * 1.1 for d in blue_data_list)
        blue_def = sum(d.get("defense", 10) * 8 + 20 for d in blue_data_list)
        blue_hp = int(sum(400 + d.get("defense", 10) * 30 + d.get("power", 100) * 2.5 for d in blue_data_list))
        blue_max_hp = blue_hp

        embed_battle = discord.Embed(title=f"🔥 انطلاق معركة [{self.mode}] الحية!", color=discord.Color.red())
        embed_battle.add_field(name="🩸 شريط دماء الفريق الأحمر", value=render_hp_bar(red_hp, red_max_hp), inline=True)
        embed_battle.add_field(name="🩸 شريط دماء الفريق الأزرق", value=render_hp_bar(blue_hp, blue_max_hp), inline=True)
        message = await interaction.channel.send(embed=embed_battle)

        logs = []
        round_cnt = 1

        while red_hp > 0 and blue_hp > 0 and round_cnt <= 6:
            await asyncio.sleep(2.0)
            dmg_to_blue = max(20, int(red_atk - (blue_def * 0.35)) + random.randint(-20, 35))
            blue_hp -= dmg_to_blue
            logs.append(f"🔴 الفريق الأحمر وجه `{dmg_to_blue:,}` ضرر!")
            if blue_hp <= 0:
                blue_hp = 0
                break

            dmg_to_red = max(20, int(blue_atk - (red_def * 0.35)) + random.randint(-20, 35))
            red_hp -= dmg_to_red
            logs.append(f"🔵 الفريق الأزرق رد بـ `{dmg_to_red:,}` ضرر!")
            if red_hp <= 0:
                red_hp = 0
                break

            round_cnt += 1

        winners = self.team_red if red_hp > blue_hp else self.team_blue
        win_title = "🔴 الفريق الأحمر" if red_hp > blue_hp else "🔵 الفريق الأزرق"
        gold_reward = 3000 * self.team_size

        def _award_winners():
            for u in winners:
                users_col.update_one({"user_id": str(u.id)}, {"$inc": {"balance": gold_reward, "power": 50, "kills": 1}})
        await asyncio.to_thread(_award_winners)

        embed_final = discord.Embed(
            title=f"👑 انتصار {win_title}!",
            description=f"🎁 **المكافأة:** `{gold_reward:,}` 🪙 ذهب لكل بطل!",
            color=discord.Color.gold()
        )
        embed_final.add_field(name="📜 سجل القتال", value="\n".join(logs[-4:]), inline=False)
        await message.edit(embed=embed_final)

class BattleModeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="مواجهة فردية 1v1", value="1v1", emoji="⚔️"),
            discord.SelectOption(label="معركة ثنائية 2v2", value="2v2", emoji="🛡️"),
            discord.SelectOption(label="ملحمة ثلاثية 3v3", value="3v3", emoji="🔥")
        ]
        super().__init__(placeholder="⚔️ اختر نمط المعركة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        reg = await asyncio.to_thread(is_user_registered, str(interaction.user.id))
        if not reg:
            return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
        lobby = BattleLobbyView(self.values[0], interaction.user)
        await interaction.response.send_message(embed=lobby.get_embed(), view=lobby)

class BattleMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(BattleModeSelect())

# ================== 🏆 8. نظام الليدربورد والترتيب التلقائي ==================

def get_prestigious_badge(rank_num: int) -> str:
    badges = {1: "👑 **[الملك - المركز الأول]**", 2: "🥇 **[المركز الثاني]**", 3: "🥈 **[المركز الثالث]**", 4: "🥉 **[المركز الرابع]**"}
    return badges.get(rank_num, f"🔹 `#{rank_num}`")

class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ترتيب أغنى شخص", value="rich", description="أثرى أباطرة الإمبراطورية بالذهب والثروة", emoji="🪙"),
            discord.SelectOption(label="ترتيب الأقوى دائماً", value="power", description="أعلى طاقة قتالية مدمرة شاملاً", emoji="⚡"),
            discord.SelectOption(label="ترتيب غزو الطوابق", value="floors", description="أعلى الفاتحين تسلقاً لطوابق البرج الـ 500", emoji="🏰"),
            discord.SelectOption(label="ترتيب قاهر اللاعبين", value="kills", description="أكثر المقاتلين إبادة وسحقاً للخصوم", emoji="💀"),
            discord.SelectOption(label="ترتيب أقوى العتاد العادي", value="normal_gear", description="أكثر المالكين للعتاد والأسلحة الملكية", emoji="🛡️"),
            discord.SelectOption(label="ترتيب أقوى العتاد المحرم", value="dark_gear", description="أعتى أسياد العتاد المحرم وسوق الظلال", emoji="🔮"),
            discord.SelectOption(label="ترتيب جامع الألقاب", value="titles_collector", description="أصحاب أكبر عدد من الألقاب والرتب", emoji="👑")
        ]
        super().__init__(placeholder="🏆 اختر تصنيف العظماء للاطلاع على الترتيب التلقائي...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        await interaction.response.defer()
        
        if category == "rich":
            def _fetch_rich():
                all_u = list(users_col.find())
                all_u.sort(key=lambda u: u.get("balance", 0) + u.get("bank", 0), reverse=True)
                return all_u[:10]
            top_users = await asyncio.to_thread(_fetch_rich)
            
            embed = discord.Embed(
                title="🪙 ترتيب أغنى شخص — ثروة الإمبراطورية",
                description="✨ **أثرى الشخصيات بالذهب والعملات (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.gold()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                total = user.get("balance", 0) + user.get("bank", 0)
                text += f"{badge} **{user.get('name', 'مقاتل')}** — 🪙 `{total:,}` ذهب\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "power":
            def _fetch_power():
                return list(users_col.find().sort([("power", -1)]).limit(10))
            top_users = await asyncio.to_thread(_fetch_power)

            embed = discord.Embed(
                title="⚡ ترتيب الأقوى دائماً — عرش القوة القتالية",
                description="✨ **أعتى مقاتلي الإمبراطورية طاقة وقوة (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.red()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                pwr = user.get("power", 0)
                title = user.get("custom_title", "المبتدئ الأسطوري")
                text += f"{badge} **{user.get('name', 'مقاتل')}** `[{title}]` — ⚡ `{pwr:,}` طاقة\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "floors":
            def _fetch_floors():
                return list(users_col.find().sort([("max_floor", -1)]).limit(10))
            top_users = await asyncio.to_thread(_fetch_floors)

            embed = discord.Embed(
                title="🏰 ترتيب غزو الطوابق — فاتحو البرج العظيم",
                description="✨ **أعلى الفاتحين تسلقاً لطوابق البرج الـ 500 (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.dark_green()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                floor = user.get("max_floor", 1)
                text += f"{badge} **{user.get('name', 'مقاتل')}** — 🏢 الطابق `{floor:,}` 🏰\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "kills":
            def _fetch_kills():
                return list(users_col.find().sort([("kills", -1)]).limit(10))
            top_users = await asyncio.to_thread(_fetch_kills)

            embed = discord.Embed(
                title="💀 ترتيب قاهر اللاعبين — سجل الإبادة والضحايا",
                description="✨ **أكثر المقاتلين سحقاً وإبادة للخصوم (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.dark_red()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                kills = user.get("kills", 0)
                text += f"{badge} **{user.get('name', 'مقاتل')}** — 💀 `{kills:,}` قتلة\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "normal_gear":
            def _fetch_normal():
                all_users = list(users_col.find())
                scored = []
                for u in all_users:
                    inv = u.get("inventory", [])
                    norm_count = sum(1 for item in inv if not any(rk in item for rk in DARK_RANKS))
                    scored.append((u.get("name", "مقاتل"), norm_count))
                scored.sort(key=lambda x: x[1], reverse=True)
                return scored[:10]
            scored_users = await asyncio.to_thread(_fetch_normal)
            
            embed = discord.Embed(
                title="🛡️ ترتيب أقوى العتاد العادي — ترسانة العتاد الملكي",
                description="✨ **أكثر المالكين للعتاد والأسلحة العامة (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.blue()
            )
            text = ""
            for idx, (name, norm_count) in enumerate(scored_users, 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}** — ⚔️ `{norm_count:,}` قطعة عتاد عادي\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "dark_gear":
            def _fetch_dark():
                all_users = list(users_col.find())
                scored = []
                for u in all_users:
                    inv = u.get("inventory", [])
                    dark_count = sum(1 for item in inv if any(rk in item for rk in DARK_RANKS))
                    scored.append((u.get("name", "مقاتل"), dark_count))
                scored.sort(key=lambda x: x[1], reverse=True)
                return scored[:10]
            scored_users = await asyncio.to_thread(_fetch_dark)

            embed = discord.Embed(
                title="🔮 ترتيب أقوى العتاد المحرم — أسياد سوق الظلال",
                description="✨ **أكثر المالكين للأسلحة والعتاد المحرم الأسطوري (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.from_rgb(85, 0, 110)
            )
            text = ""
            for idx, (name, count) in enumerate(scored_users, 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}** — 💀 `{count:,}` سلاح محرم\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        elif category == "titles_collector":
            def _fetch_titles():
                all_users = list(users_col.find())
                scored = []
                for u in all_users:
                    titles_list = u.get("titles", ["المبتدئ الأسطوري"])
                    active_t = u.get("custom_title", "المبتدئ الأسطوري")
                    scored.append((u.get("name", "مقاتل"), len(titles_list), active_t))
                scored.sort(key=lambda x: x[1], reverse=True)
                return scored[:10]
            scored_users = await asyncio.to_thread(_fetch_titles)

            embed = discord.Embed(
                title="👑 ترتيب جامع الألقاب — قاعة الشرف والألقاب",
                description="✨ **أكثر المقاتلين حاصدي الألقاب والرتب (تحديث تلقائي):**\n" + "━"*32,
                color=discord.Color.purple()
            )
            text = ""
            for idx, (name, count, active_t) in enumerate(scored_users, 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}** — 👑 `{count:,}` ألقاب `[{active_t}]`\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        embed.set_footer(text="👑 يتم التحديث التلقائي لجميع المراكز حسب إنجازات اللاعبين في قاعدة البيانات")
        view = discord.ui.View()
        view.add_item(LeaderboardSelect())
        await interaction.edit_original_response(embed=embed, view=view)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())

# ================== 👑 9. لوحة المطورين المدمجة التفاعلية (Dev Panel) ==================

class DevTransferCoinsModal(discord.ui.Modal, title="🪙 تحويل عملات إداري للاعب"):
    gold_input = discord.ui.TextInput(label="كمية الذهب 🪙", placeholder="مثال: 500000", min_length=1, max_length=15, required=False, default="0")
    diamonds_input = discord.ui.TextInput(label="كمية الألماس 💎", placeholder="مثال: 100", min_length=1, max_length=10, required=False, default="0")

    def __init__(self, target_user: discord.User):
        super().__init__()
        self.target_user = target_user

    async def on_submit(self, interaction: discord.Interaction):
        try:
            gold = int(self.gold_input.value.strip() or 0)
            diamonds = int(self.diamonds_input.value.strip() or 0)
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة أرقام صحيحة!", ephemeral=True)

        def _update():
            users_col.update_one(
                {"user_id": str(self.target_user.id)},
                {"$inc": {"balance": max(0, gold), "diamonds": max(0, diamonds)}}
            )
        await asyncio.to_thread(_update)

        embed = discord.Embed(
            title="🎁 تحويل إداري ناجح!",
            description=f"تم إضافة الرصيد لحساب {self.target_user.mention}:\n• 🪙 **ذهب مضاف:** `+{gold:,}`\n• 💎 **ألماس مضاف:** `+{diamonds:,}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)

class DevGiftGearModal(discord.ui.Modal, title="🎁 إهداء عتاد وسلاح أسطوري"):
    gear_name_input = discord.ui.TextInput(label="اسم العتاد والسلاح", placeholder="مثال: ⚔️ سيف التنين المظلم الأسطوري", min_length=2, max_length=50, required=True)
    power_input = discord.ui.TextInput(label="مقدار زيادة الطاقة ⚡", placeholder="مثال: 10000", min_length=1, max_length=10, required=True, default="5000")

    def __init__(self, target_user: discord.User):
        super().__init__()
        self.target_user = target_user

    async def on_submit(self, interaction: discord.Interaction):
        try:
            power_boost = int(self.power_input.value.strip() or 5000)
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة رقم صحيح للطاقة!", ephemeral=True)

        gear_name = self.gear_name_input.value.strip()

        def _update():
            users_col.update_one(
                {"user_id": str(self.target_user.id)},
                {
                    "$push": {"inventory": gear_name},
                    "$inc": {"power": power_boost}
                }
            )
        await asyncio.to_thread(_update)

        embed = discord.Embed(
            title="🎁 إهداء عتاد إداري أسطوري!",
            description=f"تم إهداء العتاد للاعب {self.target_user.mention}:\n• 🗡️ **العتاد:** `{gear_name}`\n• ⚡ **مكافأة الطاقة:** `+{power_boost:,}`",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)

class DevUserSelectMenu(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="👤 اختر اللاعب المستهدف بالتعديل/الترقية...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.target_user = self.values[0]
        await interaction.response.send_message(
            f"🎯 **تم تحديد اللاعب المستهدف:** {self.values[0].mention}\nالآن اختر الإجراء المطلوب من القائمة المنسدلة.",
            ephemeral=True
        )

class DevActionSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="عملات لا نهائية", value="infinite_coins", description="شحن ثروة غير محدودة للذهب والألماس", emoji="♾️"),
            discord.SelectOption(label="تحويل عملات مطور", value="transfer_coins", description="إدخال وتحويل كمية مخصصة من الذهب والألماس", emoji="🪙"),
            discord.SelectOption(label="إهداء عتاد", value="gift_gear", description="منح سلاح وعتاد خاص مع رفع الطاقة القتالية", emoji="🎁"),
            discord.SelectOption(label="إضافة مطور", value="add_dev", description="منح رتبة المطور للاعب المحدد", emoji="👑"),
            discord.SelectOption(label="حذف مطور", value="remove_dev", description="سحب صلاحية المطور من اللاعب المحدد", emoji="❌"),
            discord.SelectOption(label="شخصية السفاح", value="activate_assassin", description="تفعيل الشخصية الخارقة وسلاح العرش المحرم", emoji="🩸")
        ]
        super().__init__(placeholder="⚙️ اختر الإجراء المطلوب تنفيذه من لوحة التحكم...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            dev_check = await asyncio.to_thread(is_dev, str(interaction.user.id))
            if not dev_check:
                return await interaction.response.send_message("❌ **عذراً!** لا تملك صلاحية مطور!", ephemeral=True)

            target_user = getattr(self.view, "target_user", None) or interaction.user
            action = self.values[0]

            if action == "infinite_coins":
                reg_check = await asyncio.to_thread(is_user_registered, str(target_user.id))
                if not reg_check:
                    return await interaction.response.send_message("❌ المستخدم المحدد غير مسجل باللعبة!", ephemeral=True)

                await asyncio.to_thread(
                    users_col.update_one,
                    {"user_id": str(target_user.id)},
                    {"$set": {"balance": 999999999999, "diamonds": 999999999}}
                )
                embed = discord.Embed(
                    title="♾️ شحن العملات اللانهائية!",
                    description=f"تم منح {target_user.mention} ثروة غير محدودة:\n• 🪙 **ذهب:** `999,999,999,999`\n• 💎 **ألماس:** `999,999,999`",
                    color=discord.Color.gold()
                )
                await interaction.response.send_message(embed=embed, ephemeral=False)

            elif action == "transfer_coins":
                reg_check = await asyncio.to_thread(is_user_registered, str(target_user.id))
                if not reg_check:
                    return await interaction.response.send_message("❌ المستخدم المحدد غير مسجل باللعبة!", ephemeral=True)
                await interaction.response.send_modal(DevTransferCoinsModal(target_user))

            elif action == "gift_gear":
                reg_check = await asyncio.to_thread(is_user_registered, str(target_user.id))
                if not reg_check:
                    return await interaction.response.send_message("❌ المستخدم المحدد غير مسجل باللعبة!", ephemeral=True)
                await interaction.response.send_modal(DevGiftGearModal(target_user))

            elif action == "add_dev":
                user_id = str(target_user.id)
                target_is_dev = await asyncio.to_thread(is_dev, user_id)
                if target_is_dev:
                    return await interaction.response.send_message(f"⚠️ {target_user.mention} مطور بالفعل!", ephemeral=True)

                def _add():
                    devs_col.update_one({"user_id": user_id}, {"$set": {"added_by": str(interaction.user.id), "added_at": datetime.now(timezone.utc)}}, upsert=True)
                    users_col.update_one({"user_id": user_id}, {"$set": {"is_dev"
