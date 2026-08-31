import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import pymongo
from datetime import datetime

# ================== إعدادات الاتصال وقاعدة البيانات ==================
MONGO_URI = os.getenv("MONGO_URI", "رابط_الاتصال_الخاص_بـ_MongoDB")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col = db["users"]
guilds_col = db["guilds"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== دالة التحقق من التسجيل ==================
def is_user_registered(user_id: str) -> bool:
    return users_col.find_one({"user_id": str(user_id)}) is not None

# ================== 🏰 قاعدة بيانات المتاجر المحدثة (25 قطعة لكل فئة) ==================
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
        try:
            age = int(self.age_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة العمر كأرقام فقط!", ephemeral=True)

        if age < 1 or age > 3000:
            return await interaction.response.send_message("❌ يجب أن يكون العمر بين 1 و 3000 سنة!", ephemeral=True)

        gender = self.gender_input.value.strip()
        if gender not in ["ذكر", "أنثى"]:
            return await interaction.response.send_message("❌ يرجى كتابة كلمة ذكر أو أنثى فقط!", ephemeral=True)

        new_user = {
            "user_id": user_id,
            "name": self.name_input.value.strip(),
            "age": age,
            "gender": gender,
            "created_at": datetime.utcnow(),
            "balance": 5000,
            "bank": 0,
            "diamonds": 20,
            "power": 100,
            "kills": 0,
            "max_floor": 1,
            "inventory": [],
            "titles": ["المبتدئ الأسطوري"],
            "custom_title": "المبتدئ الأسطوري",
            "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
            "critical": 10, "magic": 10, "intelligence": 10, "defense": 10
        }
        users_col.insert_one(new_user)

        embed_success = discord.Embed(title="👑 أهلاً بك في عرش الإمبراطورية!", description="تمت معالجة وثيقة هويتك بنجاح.", color=discord.Color.gold())
        embed_success.add_field(name="🪪 الاسم", value=f"`{self.name_input.value.strip()}`", inline=True)
        embed_success.add_field(name="⏳ العمر", value=f"`{age}` سنة", inline=True)
        embed_success.add_field(name="👤 الجنس", value=f"`{gender}`", inline=True)
        embed_success.add_field(name="🎁 مكافأة البداية", value="• `5,000` 🪙 ذهب\n• `20` 💎 ألماس", inline=False)
        await interaction.response.send_message(embed=embed_success, ephemeral=False)

# ================== 🛒 2. المتجر العام (General Store) ==================
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
        
        user_data = users_col.find_one({"user_id": user_id})
        if user_data.get("balance", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ رصيدك الذهبي لا يكفي! تحتاج `{selected_item['price']:,}` 🪙", ephemeral=True)
        
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"balance": -selected_item["price"], "power": selected_item["power"]},
                "$push": {"inventory": selected_item["name"]}
            }
        )
        embed_bought = discord.Embed(
            title="🛍️ صفقة ناجحة — المتجر الإمبراطوري",
            description=f"مبروك! حصلت على **{selected_item['name']}**\n"
                        f"• ⚡ **القوة المضافة:** `+{selected_item['power']:,}`\n"
                        f"• 🪙 **المبلغ المدفوع:** `{selected_item['price']:,}` ذهبة",
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
            description="✨ **اختر المعدات المطلوبة للشراء بالعملات الذهبية (25 مستوى لكل فئة)**\n"
                        "━"*32 + "\n"
                        "🟢 `مبتدئ` (T1-T5) • 🪙 `فولاذي` (T6-T10)\n"
                        "👑 `ملكي` (T11-T15) • 🌟 `أسطوري` (T16-T20)\n"
                        "🐉 `إمبراطوري` (T21-T25)",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class GeneralStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GeneralCategorySelect())

# ================== 🔮 3. المتجر المظلم (Dark Store) ==================
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
        
        user_data = users_col.find_one({"user_id": user_id})
        if user_data.get("diamonds", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ ألماس غير كافٍ! تحتاج إلى `{selected_item['price']:,}` 💎 ألماس.", ephemeral=True)
        
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"diamonds": -selected_item["price"], "power": selected_item["power"]},
                "$push": {"inventory": selected_item["name"]}
            }
        )
        embed_buy = discord.Embed(
            title="⚡ امتلاك عتاد محرم أسطوري!",
            description=f"لقد حصلت على **{selected_item['name']}** برتبة **[{selected_item['rank']}]**!\n"
                        f"• ⚡ **طاقة قتالية مرعبة:** `+{selected_item['power']:,}`\n"
                        f"• 💎 **الألماس المستهلك:** `{selected_item['price']:,}` ألماس",
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
            description="⚠️ **سوق الأسلحة والعتاد المحرم (تتطلب 💎 الألماس فقط)**\n"
                        "━"*32 + "\n"
                        "🌑 `مشعوذ الظلال` (T1-T5) • 🩸 `السفاح القرمزي` (T6-T10)\n"
                        "🔥 `الجحيم القاتل` (T11-T15) • 😈 `الشيطان الأبدي` (T16-T20)\n"
                        "☠️ `حاكم الظلمات` (T21-T25)",
            color=discord.Color.from_rgb(45, 0, 60)
        )
        await interaction.response.edit_message(embed=embed, view=view)

class DarkStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DarkCategorySelect())

# ================== ⚡ 4. نظام تطوير المعدلات (Upgrade Stats) ==================
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
            placeholder="أدخل عدد النقاط المراد إضافتها (بلا حد أقصى)...",
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
        user_data = users_col.find_one({"user_id": user_id})

        if user_data.get("balance", 0) < total_cost:
            return await interaction.response.send_message(f"❌ لا تملك ذهبًا كافيًا! التكلفة: `{total_cost:,}` 🪙", ephemeral=True)

        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": -total_cost, self.stat_key: points, "power": points * 10}}
        )

        embed_success = discord.Embed(
            title=f"🔥 انطلاق القوة القتالية! — {self.stat_info['name']}",
            description=f"تم زيادة **{self.stat_info['emoji']} {self.stat_info['name']}** بـ `+{points:,}` نقطة!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed_success, ephemeral=False)

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

# ================== 🏰 5. محرك قتال البرج والـ 500 طابق (Tower Mechanics) ==================

def render_hp_bar(current: int, maximum: int, length: int = 10) -> str:
    """رسم شريط دماء وطاقة واقعي"""
    pct = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0
    filled = int(pct * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`[{bar}]` {current:,}/{maximum:,} HP"

def get_floor_enemy_info(floor_num: int) -> dict:
    """توليد صعوبة، وحوش، وزعماء الـ 500 طابق بشكل ديناميكي"""
    is_boss = (floor_num % 10 == 0)
    is_miniboss = (floor_num % 5 == 0 and not is_boss)

    if is_boss:
        names = ["💀 ملك الموت والمقابر", "🐉 التنين الإمبراطوري المظلم", "😈 شيطان الجحيم الأبدي", "☠️ حاكم الأرواح المفقودة"]
        quotes = [
            "لن تتخطى هذا الطابق حياً يا حشرة!",
            "دماؤك ستكون قرباناً لعرش الظلام!",
            "سأنزع روحك وأطعمها لزومبي الطوابق!"
        ]
        p_quotes = [
            "سيف الإمبراطورية سيشق جمجمتك اليوم!",
            "قوتي ستسحق عرشك المظلم إلى الأبد!",
            "لا يوجد زعيم يقف بوجه عزيمتي!"
        ]
        name = f"👑 [BOSS الطابق {floor_num}] {random.choice(names)}"
        hp = 500 + (floor_num * 350)
        atk = 40 + (floor_num * 30)
        dfs = 10 + (floor_num * 15)
        color = discord.Color.purple()
    elif is_miniboss:
        names = ["👹 قائد جيش الزومبي", "🧟‍♂️ زومبي الدماء المتجمدة", "🩸 السفاح الهائج"]
        quotes = ["اخترقت طوابق كثيرة... لكن هنا نهايتك!", "لحمك الطازج يثير جوعنا!"]
        p_quotes = ["أنت مجرد عقبة صغيرة في طريق قمتي!", "استعد للعودة إلى الجحيم!"]
        name = f"👹 [زعيم مصغر] {random.choice(names)}"
        hp = 300 + (floor_num * 200)
        atk = 25 + (floor_num * 20)
        dfs = 5 + (floor_num * 10)
        color = discord.Color.dark_red()
    else:
        names = ["🧟 زومبي مستنقع الأرواح", "🧟‍♀️ زومبي الظلال المظلمة", "💀 ميت متحرك مسلّح", "🐺 ذئب الجثث المفترس"]
        quotes = ["غغغغ... دماء جديدة!", "أرواح المقاتلين تأكلها الطوابق!", "سوف تنضم إلينا!"]
        p_quotes = ["ابتعد عن طريقي أيها الزومبي!", "ضربة واحدة تكفي لإبادتك!"]
        name = f"🧟 [طابق {floor_num}] {random.choice(names)}"
        hp = 150 + (floor_num * 100)
        atk = 15 + (floor_num * 12)
        dfs = 2 + (floor_num * 5)
        color = discord.Color.dark_green()

    return {
        "name": name,
        "is_boss": is_boss,
        "is_miniboss": is_miniboss,
        "hp": hp,
        "max_hp": hp,
        "atk": atk,
        "dfs": dfs,
        "enemy_quote": random.choice(quotes),
        "player_quote": random.choice(p_quotes),
        "color": color
    }

async def process_floor_battle(interaction: discord.Interaction, floor_num: int, is_boss_only: bool = False):
    """إدارة معركة واقعية وحساب الفوز والمكافآت المباشرة"""
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})

    if floor_num > 500:
        return await interaction.response.send_message("🏆 **تهانينا العظيمة!** لقد أتممت فتح جميع الـ 500 طابق بالكامل وأصبحت حاكم البرج الأسطوري!", ephemeral=True)

    enemy = get_floor_enemy_info(floor_num)
    
    # حساب إحصائيات اللاعب للقتال
    p_attack = user_data.get("attack", 10) * 12 + user_data.get("power", 100) * 1.2
    p_defense = user_data.get("defense", 10) * 8 + 20
    p_hp = 300 + user_data.get("defense", 10) * 25 + user_data.get("power", 100) * 2
    p_max_hp = p_hp

    embed = discord.Embed(
        title=f"⚔️ ساحة معركة البرج — الطابق [{floor_num}/500]",
        description=f"⚔️ **تواجَه الآن ضد:** `{enemy['name']}`\n"
                    f"💬 **الزومبي/الخصم:** \"{enemy['enemy_quote']}\"\n"
                    f"🗣️ **{user_data.get('name')}:** \"{enemy['player_quote']}\"\n"
                    "━"*32,
        color=enemy["color"]
    )
    embed.add_field(name=f"👤 {user_data.get('name')}", value=render_hp_bar(int(p_hp), int(p_max_hp)), inline=True)
    embed.add_field(name=f"👾 {enemy['name']}", value=render_hp_bar(int(enemy['hp']), int(enemy['max_hp'])), inline=True)
    embed.set_footer(text="جري حساب تبادل الضربات القاتلة... 💥")

    await interaction.response.send_message(embed=embed, ephemeral=False)
    message = await interaction.original_response()

    # محاكاة تبادل الضربات
    logs = []
    round_cnt = 1
    
    while p_hp > 0 and enemy["hp"] > 0 and round_cnt <= 5:
        await asyncio.sleep(1.2)
        
        # ضربة اللاعب
        dmg_to_enemy = max(10, int(p_attack - (enemy["dfs"] * 0.4)) + random.randint(-15, 25))
        is_crit = random.random() < (user_data.get("critical", 10) / 100)
        if is_crit:
            dmg_to_enemy = int(dmg_to_enemy * 1.8)
            logs.append(f"💥 **ضربة قاتلة!** وجهت `{dmg_to_enemy:,}` ضرر للخصم!")
        else:
            logs.append(f"🗡️ سددت ضربة بـ `{dmg_to_enemy:,}` ضرر!")
            
        enemy["hp"] -= dmg_to_enemy

        if enemy["hp"] <= 0:
            enemy["hp"] = 0
            break

        # ضربة الوحش
        dmg_to_player = max(5, int(enemy["atk"] - (p_defense * 0.3)) + random.randint(-10, 15))
        p_hp -= dmg_to_player
        if p_hp <= 0:
            p_hp = 0
            logs.append(f"🩸 **تلقيت ضربة قاضية!** سقطت في الطابق.")
            break
        else:
            logs.append(f"🩸 الزومبي هاجمك بـ `{dmg_to_player:,}` ضرر!")

        round_cnt += 1

    # النتيجة والمكافآت
    if enemy["hp"] <= 0:
        # فوز اللاعب
        gold_reward = floor_num * 300 + random.randint(200, 800)
        diamond_reward = random.randint(1, 4) if (enemy["is_boss"] or random.random() < 0.25) else 0
        
        # إمكانية الحصول على عتاد عادي أو محرم عشوائي
        dropped_gear = None
        gear_msg = "لا يوجد عتاد مسقط"
        
        if enemy["is_boss"] and random.random() < 0.4:
            dropped_gear = random.choice(ALL_DARK_ITEMS)
            gear_msg = f"🔮 **عتاد محرم أسطوري:** `{dropped_gear['name']}`"
        elif random.random() < 0.3:
            dropped_gear = random.choice(ALL_GENERAL_ITEMS)
            gear_msg = f"🗡️ **عتاد إمبراطوري:** `{dropped_gear['name']}`"

        # تحديث قاعدة البيانات
        update_doc = {
            "$inc": {"balance": gold_reward, "diamonds": diamond_reward, "kills": 1, "power": 30},
            "$set": {"max_floor": floor_num + 1}
        }
        if dropped_gear:
            update_doc["$push"] = {"inventory": dropped_gear["name"]}
            update_doc["$inc"]["power"] += dropped_gear["power"]

        users_col.update_one({"user_id": user_id}, update_doc)

        embed_win = discord.Embed(
            title=f"🎉 **انتصار ساحق في الطابق [{floor_num}]!**",
            description=f"👑 **تم سحق {enemy['name']} بنجاح!**\n"
                        f"✨ **الانتقال التلقائي:** تم فتح **الطابق [{floor_num + 1}]** بنجاح!\n\n"
                        f"🎁 **غنائم الانتصار والمكافآت:**\n"
                        f"• 🪙 **ذهب عادي:** `+{gold_reward:,}`\n"
                        f"• 💎 **عملات نادرة (ألماس):** `+{diamond_reward}`\n"
                        f"• ⚡ **زيادة طاقة:** `+30` نقطة\n"
                        f"• 📦 **إسقاط العتاد:** {gear_msg}\n"
                        "━"*32,
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
        # خسارة اللاعب
        embed_lose = discord.Embed(
            title=f"💀 **هزيمة في الطابق [{floor_num}]!**",
            description=f"لم تستطع الصمود بوجه `{enemy['name']}`.\n"
                        f"💡 **نصيحة الإمبراطورية:** قم بتطوير معداتك من المذبح أو شراء أسلحة قوية ثم أعد المحاولة!",
            color=discord.Color.red()
        )
        embed_lose.add_field(name="📜 مجريات اللحظات الأخيرة", value="\n".join(logs[-4:]), inline=False)
        await message.edit(embed=embed_lose)

# ================== 🎒 view الحقيبة ومستعرض العتاد ==================
class InventoryView(discord.ui.View):
    def __init__(self, user_data: dict):
        super().__init__()
        inv = user_data.get("inventory", [])
        if not inv:
            self.add_item(discord.ui.Button(label="الحقيبة فارغة حالياً", disabled=True))
        else:
            options = [discord.SelectOption(label=item[:25], value=f"{idx}_{item}", emoji="🎒") for idx, item in enumerate(inv[:25])]
            select = discord.ui.Select(placeholder="🎒 اختر قطعة عتاد لمعاينة تفاصيلها...", options=options)
            
            async def inv_callback(interaction: discord.Interaction):
                item_name = select.values[0].split("_", 1)[1]
                embed = discord.Embed(title="🔍 معاينة قطعة العتاد", description=f"القطعة: **{item_name}**\nمجهزة بحقيبتك الشخصية وتمنحك القوة والمعدلات.", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)

            select.callback = inv_callback
            self.add_item(select)

# ================== 🏰 6. القائمة الرئيسية الشاملة لأمر /الطوابق ==================
class TowerMainSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="بدء المغامرة (تسلق البرج)", value="start_adv", description="خوض معارك الطوابق الـ 500 فوراً مع انتقال تلقائي", emoji="⚔️"),
            discord.SelectOption(label="قتال الزعيم (Boss)", value="boss_fight", description="مواجهة زعيم الطابق الحالي لحصد الجوائز النادرة", emoji="💀"),
            discord.SelectOption(label="المتجر العادي", value="gen_store", description="شراء الأسلحة والعتاد بالعملات الذهبية", emoji="🛒"),
            discord.SelectOption(label="المتجر المظلم", value="dark_store", description="شراء أعتى العتاد المحرم بالألماس 💎", emoji="🔮"),
            discord.SelectOption(label="تطوير معداتي", value="upgrade_stats", description="رفع معدلات الهجوم والدفاع والسحر بلا حدود", emoji="⚡"),
            discord.SelectOption(label="حقيبتي والعتاد", value="my_inventory", description="عرض الأسلحة والمعدات المملوكة بحقيبتك", emoji="🎒")
        ]
        super().__init__(placeholder="🏰 اختر الإجراء المطلوب في برج الطوابق...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        val = self.values[0]

        # 1. بدء المغامرة تلقائياً
        if val == "start_adv":
            current_f = user_data.get("max_floor", 1)
            await process_floor_battle(interaction, current_f)

        # 2. قتال الزعيم مباشرة
        elif val == "boss_fight":
            current_f = user_data.get("max_floor", 1)
            # تقريب لأقرب طابق زعيم
            boss_f = current_f if current_f % 10 == 0 else ((current_f // 10 + 1) * 10)
            await process_floor_battle(interaction, boss_f, is_boss_only=True)

        # 3. المتجر العادي
        elif val == "gen_store":
            embed = discord.Embed(title="🏛️ متجر الإمبراطورية الملكي العام", description="اختر قسم العتاد للشراء بالذهب 🪙.", color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=True)

        # 4. المتجر المظلم
        elif val == "dark_store":
            embed = discord.Embed(title="🔮 المتجر المظلم المحرم — Dark Sanctuary", description="سوق العتاد المحرم بالألماس 💎.", color=discord.Color.from_rgb(20, 0, 35))
            await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=True)

        # 5. تطوير معداتي
        elif val == "upgrade_stats":
            embed = discord.Embed(title="✨ مذبح الصقل وتطوير القوى الإمبراطورية", description="ترقية معدلات القوة القتالية بلا حدود.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=True)

        # 6. حقيبتي
        elif val == "my_inventory":
            inv = user_data.get("inventory", [])
            embed = discord.Embed(
                title=f"🎒 حقيبة المقاتل [{user_data.get('name')}]",
                description=f"• 📦 **إجمالي القطع المملوكة:** `{len(inv)}` قطعة\n"
                            f"• ⚡ **الطاقة الإجمالية:** `{user_data.get('power', 0):,}`\n\n"
                            f"📜 **قائمة الأسلحة الأخيرة:**\n" +
                            ("\n".join([f"• {item}" for item in inv[-10:]]) if inv else "الحقيبة فارغة حالياً."),
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=InventoryView(user_data), ephemeral=True)

class TowerMainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TowerMainSelect())

# ================== 🏆 7. نظام الليدربورد والترتيب الفخم (Leaderboard System) ==================

def get_prestigious_badge(rank_num: int) -> str:
    badges = {
        1: "👑 **[الملك - المركز الأول]**",
        2: "🥇 **[المركز الثاني]**",
        3: "🥈 **[المركز الثالث]**",
        4: "🥉 **[المركز الرابع]**"
    }
    return badges.get(rank_num, f"🔹 `#{rank_num}`")

class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ترتيب أغنى شخص", value="rich", description="أثرى أباطرة الإمبراطورية ثروة وذهباً", emoji="🪙"),
            discord.SelectOption(label="ترتيب أقوى شخص", value="power", description="أعظم أبطال القوة القتالية الشاملة ⚡", emoji="⚡"),
            discord.SelectOption(label="ترتيب قاهر اللاعبين", value="kills", description="سجل أكثر المقاتلين إبادة وسحقاً للخصوم", emoji="💀"),
            discord.SelectOption(label="ترتيب الأسحلة الإمبراطورية", value="imp_gear", description="أكبر ملاك العتاد والمعدات الملكية", emoji="🗡️"),
            discord.SelectOption(label="ترتيب الأسلحة المحرمة", value="dark_gear", description="نخب أسياد أسلحة الظلال والجحيم", emoji="🔮"),
            discord.SelectOption(label="ترتيب الألقاب", value="titles", description="أصحاب أكثر الألقاب والرتب الشرفية", emoji="👑"),
            discord.SelectOption(label="ترتيب الطوابق", value="floors", description="أعلى الفاتحين تسلقاً لطوابق البرج", emoji="🏰"),
            discord.SelectOption(label="ترتيب أقوى النقابات", value="guilds", description="أقوى التحالفات والنقابات العسكرية", emoji="🛡️")
        ]
        super().__init__(placeholder="🏆 اختر تصنيف العظماء للاطلاع على الليدربورد...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        # 1. ترتيب أغنى شخص
        if category == "rich":
            all_users = list(users_col.find())
            all_users.sort(key=lambda u: u.get("balance", 0) + u.get("bank", 0), reverse=True)
            top_users = all_users[:10]
            
            embed = discord.Embed(
                title="🏛️ قاعة الذهب — ترتيب أثرى شخصيات الإمبراطورية",
                description="✨ **قائمة القارونين والأباطرة الأكثر ثروة بالذهب (محفظة + بنك)**\n" + "━"*32,
                color=discord.Color.gold()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                total = user.get("balance", 0) + user.get("bank", 0)
                wallet = user.get("balance", 0)
                bank = user.get("bank", 0)
                text += f"{badge} **{user.get('name', 'مقاتل')}**\n└ 🪙 مجموع الثروة: `{total:,}` (💼 `{wallet:,}` | 🏦 `{bank:,}`)\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 2. ترتيب أقوى شخص
        elif category == "power":
            top_users = list(users_col.find().sort([("power", -1)]).limit(10))
            embed = discord.Embed(
                title="⚡ عرش القوة — ترتيب أعتى مقاتلي الإمبراطورية",
                description="✨ **قائمة أصحاب أعتى طاقة قتالية مدمرة بلا منازع**\n" + "━"*32,
                color=discord.Color.red()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                pwr = user.get("power", 0)
                title = user.get("custom_title", "المبتدئ الأسطوري")
                text += f"{badge} **{user.get('name', 'مقاتل')}** `[{title}]` \n└ ⚡ الطاقة القتالية: `{pwr:,}`\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 3. ترتيب قاهر اللاعبين
        elif category == "kills":
            top_users = list(users_col.find().sort([("kills", -1)]).limit(10))
            embed = discord.Embed(
                title="💀 سجل الإبادة — ترتيب سفاحي وقاهري اللاعبين",
                description="✨ **قائمة المقاتلين الأكثر إبادة للخصوم وسحقاً للعداة**\n" + "━"*32,
                color=discord.Color.dark_red()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                kills = user.get("kills", 0)
                text += f"{badge} **{user.get('name', 'مقاتل')}**\n└ 💀 ضحايا تم سحقهم: `{kills:,}` مقاتل\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 4. ترتيب الأسلحة الإمبراطورية
        elif category == "imp_gear":
            all_users = list(users_col.find())
            scored_users = []
            for u in all_users:
                inv = u.get("inventory", [])
                imp_count = sum(1 for item in inv if not any(rk in item for rk in DARK_RANKS))
                scored_users.append((u.get("name", "مقاتل"), imp_count, len(inv)))
            scored_users.sort(key=lambda x: x[1], reverse=True)
            
            embed = discord.Embed(
                title="🗡️ ترسانة الملوك — ترتيب أصحاب الأسلحة الإمبراطورية",
                description="✨ **قائمة أثرى الترسانات العسكرية بالمعدات الملكية العامة**\n" + "━"*32,
                color=discord.Color.blue()
            )
            text = ""
            for idx, (name, imp_count, total_inv) in enumerate(scored_users[:10], 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}**\n└ ⚔️ عتاد إمبراطوري: `{imp_count:,}` قطعة (من إجمالي `{total_inv:,}`)\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 5. ترتيب الأسلحة المحرمة
        elif category == "dark_gear":
            all_users = list(users_col.find())
            scored_users = []
            for u in all_users:
                inv = u.get("inventory", [])
                dark_count = sum(1 for item in inv if any(rk in item for rk in DARK_RANKS))
                scored_users.append((u.get("name", "مقاتل"), dark_count))
            scored_users.sort(key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title="🔮 سوق الظلال المحرم — ترتيب ملاك أسلحة الجحيم",
                description="✨ **قائمة النخبة المستحوذة على أعتى عتاد محرم من Dark Sanctuary**\n" + "━"*32,
                color=discord.Color.from_rgb(85, 0, 110)
            )
            text = ""
            for idx, (name, count) in enumerate(scored_users[:10], 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}**\n└ 💀 أسلحة محرمة أسطورية: `{count:,}` سلاح\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 6. ترتيب الألقاب
        elif category == "titles":
            all_users = list(users_col.find())
            scored_users = []
            for u in all_users:
                titles_list = u.get("titles", ["المبتدئ الأسطوري"])
                active_t = u.get("custom_title", "المبتدئ الأسطوري")
                scored_users.append((u.get("name", "مقاتل"), len(titles_list), active_t))
            scored_users.sort(key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title="👑 عرش الألقاب — ترتيب أصحاب الشرف والمجد الملكي",
                description="✨ **قائمة القادة الحاملين لأكبر عدد من الألقاب والرتب الإمبراطورية**\n" + "━"*32,
                color=discord.Color.purple()
            )
            text = ""
            for idx, (name, count, active_t) in enumerate(scored_users[:10], 1):
                badge = get_prestigious_badge(idx)
                text += f"{badge} **{name}**\n└ 👑 عدد الألقاب: `{count:,}` | اللقب المجهز: `[{active_t}]`\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 7. ترتيب الطوابق
        elif category == "floors":
            top_users = list(users_col.find().sort([("max_floor", -1)]).limit(10))
            embed = discord.Embed(
                title="🏰 فاتحو البرج — ترتيب قادة الطوابق العليا",
                description="✨ **قائمة أبطال التسلق الشاهق الذين اخترقوا أعتى طوابق برج التحدي**\n" + "━"*32,
                color=discord.Color.dark_green()
            )
            text = ""
            for idx, user in enumerate(top_users, 1):
                badge = get_prestigious_badge(idx)
                floor = user.get("max_floor", 1)
                text += f"{badge} **{user.get('name', 'مقاتل')}**\n└ 🏢 الطابق المفتوح: `{floor:,}` 🏰\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد بيانات مسجلة حالياً."

        # 8. ترتيب أقوى النقابات
        elif category == "guilds":
            top_guilds = list(guilds_col.find().sort([("level", -1)]).limit(10))
            embed = discord.Embed(
                title="🛡️ حلف العظماء — ترتيب أقوى النقابات والتحالفات",
                description="✨ **قائمة أقوى النقابات العسكرية المسيطرة على أرض الإمبراطورية**\n" + "━"*32,
                color=discord.Color.magenta()
            )
            text = ""
            for idx, g in enumerate(top_guilds, 1):
                badge = get_prestigious_badge(idx)
                lvl = g.get('level', 1)
                m_count = len(g.get('members', []))
                text += f"{badge} **نقابة [{g.get('name', 'نقابة')}]**\n└ ⚜️ المستوى: `{lvl:,}` | 👥 الأعضاء: `{m_count:,}` مقاتل\n\n"
            embed.description += f"\n{text}" if text else "\nلا توجد نقابات مسجلة حالياً."

        embed.set_footer(text="👑 يتم التحديث المباشر وتصنيف المراكز تلقائياً عبر قاعدة البيانات • الإمبراطورية العظمى")
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        view = discord.ui.View()
        view.add_item(LeaderboardSelect())
        await interaction.response.edit_message(embed=embed, view=view)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())


# ================== تسجيل وتنسيق الأوامر ==================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✨ تم مزامنة {len(synced)} أمر بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")
    print(f"👑 البوت يعمل الآن باسم: {bot.user}")

@bot.tree.command(name="تسجيل", description="📜 فتح استمارة التسجيل في الإمبراطورية")
async def register_command(interaction: discord.Interaction):
    if is_user_registered(interaction.user.id):
        return await interaction.response.send_message("⚠️ أنت مسجل بالفعل!", ephemeral=True)
    await interaction.response.send_modal(RegisterModal())

@bot.tree.command(name="المتجر_العام", description="🏛️ فتح متجر الإمبراطورية العام لشراء العتاد بالذهب")
async def general_store(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    
    embed = discord.Embed(
        title="🏛️ متجر الإمبراطورية الملكي العام",
        description="تصفح العتاد والشراء بالذهب 🪙. اختر قسم العتاد المطلوبة من القائمة المنسدلة أسفله (25 قطعة لكل فئة).",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=False)

@bot.tree.command(name="المتجر_المظلم", description="👁️ دخول سوق الظلال السري لشراء العتاد الأسطوري بالألماس")
async def dark_store(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    
    embed = discord.Embed(
        title="🔮 المتجر المظلم المحرم — Dark Sanctuary",
        description="سوق الأسلحة والعتاد المحرمة بالألماس 💎 (25 قطعة أسطورية لكل قسم).",
        color=discord.Color.from_rgb(20, 0, 35)
    )
    await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=False)

@bot.tree.command(name="تطوير_المعدلات", description="⚡ فتح مذبح تطوير المعدلات القتالية كسر الحدود إلى المليارات")
async def upgrade_stats_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    embed = discord.Embed(title="✨ مذبح الصقل وتطوير القوى الإمبراطورية", description="تطوير المعدلات القتالية بلا حدود حتى المليارات.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=False)

@bot.tree.command(name="الطوابق", description="🏰 فتح بوابات برج الـ 500 طابق والبدء بالمغامرة التلقائية وشراء المعدات")
async def tower_floors_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    user_data = users_col.find_one({"user_id": user_id})
    current_floor = user_data.get("max_floor", 1)

    embed = discord.Embed(
        title="🏰 عرش البرج العظيم — بوابات الـ 500 طابق",
        description=f"✨ **مرحباً بك يا كابتن `{user_data.get('name')}`!**\n"
                    f"• 🏢 **طابقك الحالي المستهدف:** `الطابق [{current_floor}/500]`\n"
                    f"• ⚡ **طاقاتك القتالية:** `{user_data.get('power', 0):,}` ⚡\n"
                    f"• 🪙 **رصيد المحفظة:** `{user_data.get('balance', 0):,}` 🪙 | 💎 `{user_data.get('diamonds', 0):,}`\n\n"
                    "اختر الخيار المطلوب من القائمة المنسدلة للبدء فوراً بالقتال والتنقل بين المتاجر وتحديث معداتك!",
        color=discord.Color.dark_green()
    )
    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    embed.set_footer(text="برج المغامرات الإمبراطوري • القتال والتنقل تلقائي")
    await interaction.response.send_message(embed=embed, view=TowerMainView(), ephemeral=False)

@bot.tree.command(name="الليدربورد", description="👑 عرض قاعة العظماء وتصنيفات الشرف التلقائية بالإمبراطورية")
async def leaderboard_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    embed = discord.Embed(
        title="👑 قاعة العظماء وليدربورد الإمبراطورية الفخم",
        description="✨ **مرحباً بك في مجلس الشرف المباشر!**\n"
                    "اختر التصنيف المطلوب من القائمة المنسدلة بالأسفل لعرض ترتيب العظماء تلقائياً بحسب إحصائيات قاعدة البيانات المباشرة.",
        color=discord.Color.gold()
    )
    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    embed.add_field(
        name="📜 التصنيفات المتاحة للترتيب التلقائي:",
        value="• 🪙 **أغنى شخص:** (مجموع الذهب بالبنك والمحفظة)\n"
              "• ⚡ **أقوى شخص:** (إجمالي الطاقة القتالية)\n"
              "• 💀 **قاهر اللاعبين:** (عدد الانتصارات والقتلات)\n"
              "• 🗡️ **الأسلحة الإمبراطورية:** (عدد معدات المتجر العام)\n"
              "• 🔮 **الأسلحة المحرمة:** (ترسانة المتجر المظلم)\n"
              "• 👑 **الألقاب:** (أصحاب الرتب والألقاب الملكية)\n"
              "• 🏰 **الطوابق:** (أعلى طابق تم اختراقه بالبرج)\n"
              "• 🛡️ **أقوى النقابات:** (ترتيب التحالفات العسكرية)",
        inline=False
    )
    embed.set_footer(text="الإمبراطورية العظمى • التحديث تلقائي ومباشر")
    await interaction.response.send_message(embed=embed, view=LeaderboardView(), ephemeral=False)

# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
