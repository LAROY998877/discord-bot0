import os
import random
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

# ================== قاعدة بيانات 25 قطعة لكل فئة (المتاجر) ==================
CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]
DARK_RANKS = ["السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي"]

GEAR_DATA = {}
for cat in CATEGORIES:
    GEAR_DATA[cat] = []
    # 20 قطعة للمتجر العام
    for i in range(1, 21):
        rank = "مبتدئ" if i <= 5 else ("فولاذي" if i <= 10 else ("ملكي" if i <= 15 else "أسطوري"))
        GEAR_DATA[cat].append({
            "id": f"{cat}_{i}",
            "name": f"{cat} {rank} المستوى {i}",
            "rank": rank,
            "power": i * 40,
            "price": i * 350,
            "currency": "gold",
            "store": "general"
        })
    # 5 قطع فائقة القوة للمتجر المظلم
    for i in range(21, 26):
        r_index = 0 if i <= 22 else (1 if i <= 24 else 2)
        rank_name = DARK_RANKS[r_index]
        GEAR_DATA[cat].append({
            "id": f"{cat}_{i}",
            "name": f"💀 {cat} [{rank_name}] T{i-20}",
            "rank": rank_name,
            "power": i * 180,
            "price": (i - 20) * 15,
            "currency": "diamonds",
            "store": "dark"
        })

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
            "current_floor": 1,
            "max_floor": 1,
            "inventory": [],
            "equipped": {},
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
                description=f"الرتبة: {item['rank']} | القوة: +{item['power']} | السعر: {item['price']} 🪙",
                emoji="⚔️"
            ) for item in items
        ]
        super().__init__(placeholder=f"اختر قطعة من فئة [{category}]...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        selected_id = self.values[0]
        selected_item = next(item for item in GEAR_DATA[self.category] if item["id"] == selected_id)
        
        user_data = users_col.find_one({"user_id": user_id})
        if user_data.get("balance", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ رصيدك الذهبي لا يكفي! تحتاج `{selected_item['price']}` 🪙", ephemeral=True)
        
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"balance": -selected_item["price"], "power": selected_item["power"]},
                "$push": {"inventory": selected_item["name"]}
            }
        )
        await interaction.response.send_message(f"🛍️ **تم الشراء بنجاح!** حصلت على `{selected_item['name']}` وزادت طاقتك بـ `+{selected_item['power']}` ⚡", ephemeral=True)

class GeneralCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=cat, value=cat, emoji="🛡️") for cat in CATEGORIES]
        super().__init__(placeholder="🏰 اختر فئة العتاد للعرض...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        view = discord.ui.View()
        view.add_item(GeneralCategorySelect())
        view.add_item(GeneralItemSelect(cat))
        
        embed = discord.Embed(title=f"🏛️ المتجر العام — فئة [{cat}]", description="اختر المعدات المطلوبة للشراء بالعملات الذهبية.", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=view)

class GeneralStoreView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GeneralCategorySelect())

# ================== 💀 3. المتجر المظلم (Dark Store) ==================
class DarkItemSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        items = [item for item in GEAR_DATA[category] if item["store"] == "dark"]
        options = [
            discord.SelectOption(
                label=item["name"],
                value=item["id"],
                description=f"الرتبة: {item['rank']} | القوة: +{item['power']} | السعر: {item['price']} 💎",
                emoji="🔥" if item["rank"] == "الجحيم القاتل" else ("🩸" if item["rank"] == "السفاح القرمزي" else "😈")
            ) for item in items
        ]
        super().__init__(placeholder=f"🔮 عتاد الظلال السرية [{category}]...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        selected_id = self.values[0]
        selected_item = next(item for item in GEAR_DATA[self.category] if item["id"] == selected_id)
        
        user_data = users_col.find_one({"user_id": user_id})
        if user_data.get("diamonds", 0) < selected_item["price"]:
            return await interaction.response.send_message(f"❌ ألماس غير كافٍ! تحتاج إلى `{selected_item['price']}` 💎 ألماس.", ephemeral=True)
        
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"diamonds": -selected_item["price"], "power": selected_item["power"]},
                "$push": {"inventory": selected_item["name"]}
            }
        )
        embed_buy = discord.Embed(
            title="⚡ امتلاك عتاد محرم!",
            description=f"لقد حصلت على **{selected_item['name']}** برتبة **[{selected_item['rank']}]**!\nارتفعت طاقتك بمقدار `+{selected_item['power']}` ⚡",
            color=discord.Color.dark_purple()
        )
        await interaction.response.send_message(embed=embed_buy, ephemeral=True)

class DarkCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"عتاد مظلم: {cat}", value=cat, emoji="🌑") for cat in CATEGORIES]
        super().__init__(placeholder="👁️ اختر قسم العتاد المظلم...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        view = discord.ui.View()
        view.add_item(DarkCategorySelect())
        view.add_item(DarkItemSelect(cat))
        
        embed = discord.Embed(
            title=f"🖤 خزنة الظلال السرية — [{cat}]",
            description="⚠️ **تنبيه:** المعدات المعروضة هنا تتطلب **💎 الألماس** فقط.\n\n"
                        "🏆 **الرتب العليا المتاحة:**\n"
                        "• 😈 **الشيطان الأبدي**\n"
                        "• 🔥 **الجحيم القاتل**\n"
                        "• 🩸 **السفاح القرمزي**",
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

# ================== 🏆 5. نظام الليدربورد والترتيب (Leaderboard System) ==================
def get_medal_emoji(rank_num: int) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(rank_num, f"`#{rank_num}`")

class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="أغنى شخص", value="rich", description="ترتيب أغنى مقاتلي الإمبراطورية", emoji="🪙"),
            discord.SelectOption(label="أقوى شخص", value="power", description="ترتيب أعلى المقاتلين قوة", emoji="⚡"),
            discord.SelectOption(label="قاهر اللاعبين", value="kills", description="ترتيب المقاتلين الأكثر إبادة للخصوم", emoji="💀"),
            discord.SelectOption(label="الأسلحة الإمبراطورية", value="imp_gear", description="ترتيب ملاك معدات المتجر العام", emoji="🗡️"),
            discord.SelectOption(label="الأسلحة المحرمة", value="dark_gear", description="ترتيب نخب أسلحة المتجر المظلم", emoji="🔮"),
            discord.SelectOption(label="الألقاب", value="titles", description="ترتيب أصحاب الألقاب الملكية", emoji="👑"),
            discord.SelectOption(label="الطوابق", value="floors", description="ترتيب الأبطال في البرج", emoji="🏰"),
            discord.SelectOption(label="أقوى النقابات", value="guilds", description="ترتيب أقوى النقابات", emoji="🛡️")
        ]
        super().__init__(placeholder="🏆 اختر فئة الترتيب لعرض العظماء...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        if category == "rich":
            top_users = list(users_col.find().sort([("balance", -1)]).limit(10))
            embed = discord.Embed(title="🪙 لوحة شرف أغنى الشخصيات", color=discord.Color.gold())
            text = "".join([f"{get_medal_emoji(i)} **{u.get('name','مقاتل')}** — `{u.get('balance',0)+u.get('bank',0):,}` 🪙\n" for i, u in enumerate(top_users, 1)])
            embed.description = text or "لا يوجد بيانات."
        elif category == "power":
            top_users = list(users_col.find().sort([("power", -1)]).limit(10))
            embed = discord.Embed(title="⚡ قائمة أقوى مقاتلي الإمبراطورية", color=discord.Color.red())
            text = "".join([f"{get_medal_emoji(i)} **{u.get('name','مقاتل')}** — `{u.get('power',0):,}` ⚡ طاقة\n" for i, u in enumerate(top_users, 1)])
            embed.description = text or "لا يوجد بيانات."
        elif category == "floors":
            top_users = list(users_col.find().sort([("max_floor", -1)]).limit(10))
            embed = discord.Embed(title="🏰 تسلق البرج — قادة الطوابق العليا", color=discord.Color.dark_green())
            text = "".join([f"{get_medal_emoji(i)} **{u.get('name','مقاتل')}** — الطابق `{u.get('max_floor',1):,}` 🏢\n" for i, u in enumerate(top_users, 1)])
            embed.description = text or "لا يوجد بيانات."
        else:
            embed = discord.Embed(title="🏆 الليدربورد الإمبراطوري", description="يتم تحديث الترتيب بشكل دوري.", color=discord.Color.gold())

        view = discord.ui.View()
        view.add_item(LeaderboardSelect())
        await interaction.response.edit_message(embed=embed, view=view)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())

# ================== 🎒 6. نظام الحقيبة والتجهيز (Inventory & Equipment) ==================
class EquipSelect(discord.ui.Select):
    def __init__(self, user_inventory: list):
        options = [
            discord.SelectOption(label=item, value=item, emoji="🛡️" if not any(rk in item for rk in DARK_RANKS) else "🔮")
            for item in set(user_inventory)
        ][:25]
        if not options:
            options = [discord.SelectOption(label="لا توجد معدات بالحقيبة", value="none")]
        super().__init__(placeholder="🎒 اختر قطعة عتاد لتجهيزها واستخدامها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        if item_name == "none":
            return await interaction.response.send_message("❌ حقيبتك فارغة!", ephemeral=True)
        
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$set": {"equipped.active_weapon": item_name}})
        
        embed = discord.Embed(
            title="⚔️ تم تجهيز العتاد بنجاح!",
            description=f"أصبح سلاحك/عتادك المجهز حالياً للقتال في الطوابق هو:\n**[{item_name}]** 💥",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class InventoryView(discord.ui.View):
    def __init__(self, user_inventory: list):
        super().__init__()
        self.add_item(EquipSelect(user_inventory))

# ================== 🏰 7. نظام الطوابق والمغامرة مع BOSS (Floors Hub System) ==================

ZOMBIE_QUOTES = [
    "🧟: 'سألتهم عظامك وأصنع منها قلادتي التالية!'",
    "🧟: 'رائحة دمائك تزكم الأنف.. تعال إلي!'",
    "🧟: 'لن تخرج حياً من هذا الطابق أبدًا!'",
    "🧟: 'صرخاتك ستكون ألحاني المفضلة اليوم!'"
]

PLAYER_QUOTES = [
    "🗡️: 'سيف القصاص سيشطر رأسك إلى نصفين!'",
    "🗡️: 'مجرد زومبي متعفن آخر يقف في طريقي!'",
    "🗡️: 'طاقتي ستسحق وجودك المظلم!'",
    "🗡️: 'تراجع وإلا محوتك من هذا العالم!'"
]

def make_hp_bar(current: int, maximum: int) -> str:
    ratio = max(0, min(1, current / maximum))
    filled = int(ratio * 10)
    return "❤️ " + "█" * filled + "░" * (10 - filled) + f" `{current}/{maximum}`"

async def execute_battle(interaction: discord.Interaction, is_boss: bool = False):
    user_id = str(interaction.user.id)
    user = users_col.find_one({"user_id": user_id})
    current_floor = user.get("current_floor", 1)

    if current_floor > 500:
        return await interaction.response.send_message("🏆 **أنت بالفعل قهرت البرج الكامل ووصلت للطابق 500 النهائي!**", ephemeral=True)

    player_power = user.get("power", 100) + user.get("attack", 10) * 5
    player_hp = 100 + user.get("defense", 10) * 10
    max_p_hp = player_hp

    # صعوبة الطابق والعدو
    multiplier = 2.5 if is_boss else 1.0
    enemy_hp = int((current_floor * 80 + 100) * multiplier)
    max_e_hp = enemy_hp
    enemy_atk = int((current_floor * 15 + 20) * multiplier)

    enemy_name = f"👹 الـ BOSS [سيد الظلام طابق {current_floor}]" if is_boss else f"🧟 زومبي الطابق [{current_floor}]"

    # المحاكاة الواقعية للقتال
    turn_log = []
    p_hp = max_p_hp
    e_hp = max_e_hp
    
    # محاكاة الضرر
    while p_hp > 0 and e_hp > 0:
        # هجوم اللاعب
        p_dmg = random.randint(int(player_power * 0.8), int(player_power * 1.2))
        e_hp -= p_dmg
        if e_hp <= 0:
            e_hp = 0
            break
        # هجوم الزومبي/البوس
        e_dmg = random.randint(int(enemy_atk * 0.7), int(enemy_atk * 1.3))
        p_hp -= e_dmg
        if p_hp <= 0:
            p_hp = 0

    p_bar = make_hp_bar(p_hp, max_p_hp)
    e_bar = make_hp_bar(e_hp, max_e_hp)

    p_quote = random.choice(PLAYER_QUOTES)
    z_quote = random.choice(ZOMBIE_QUOTES)

    if p_hp > 0:
        # انتصار
        next_floor = current_floor + 1
        gold_reward = current_floor * 250 + random.randint(50, 200)
        diamond_reward = random.randint(1, 5) if (current_floor % 5 == 0 or is_boss) else 0
        
        # مكافأة عتاد عشوائية حسب الصعوبة
        item_dropped = None
        if random.random() < 0.35 or is_boss:
            category = random.choice(CATEGORIES)
            if current_floor >= 50 and random.random() < 0.2:
                # عتاد مظلم محرم
                dark_item = random.choice([item for item in GEAR_DATA[category] if item["store"] == "dark"])
                item_dropped = dark_item["name"]
            else:
                # عتاد عادي
                gen_item = random.choice([item for item in GEAR_DATA[category] if item["store"] == "general"])
                item_dropped = gen_item["name"]

        # تحديث الحساب
        update_data = {
            "$inc": {"balance": gold_reward, "diamonds": diamond_reward, "kills": 1},
            "$set": {"current_floor": min(500, next_floor)}
        }
        if next_floor > user.get("max_floor", 1):
            update_data["$set"]["max_floor"] = min(500, next_floor)

        if item_dropped:
            update_data["$push"] = {"inventory": item_dropped}

        users_col.update_one({"user_id": user_id}, update_data)

        embed_win = discord.Embed(
            title=f"⚔️ نصر ساحق في الطابق [{current_floor}/500]!",
            description=f"**سقط {enemy_name} صريعاً أمام طاقتك المدمرة!**\n\n"
                        f"💬 {z_quote}\n"
                        f"💬 {p_quote}\n\n"
                        f"**حالة المقاتل:**\n{interaction.user.mention}: {p_bar}\n"
                        f"{enemy_name}: {e_bar}\n\n"
                        f"🎁 **المكافآت المكتسبة:**\n"
                        f"• 🪙 **ذهب:** `+{gold_reward:,}`\n"
                        + (f"• 💎 **ألماس نادر:** `+{diamond_reward}`\n" if diamond_reward else "")
                        + (f"• 🔮 **غنائم قطعت عتاد:** `{item_dropped}`\n" if item_dropped else "")
                        + f"\n🚀 **تم الانتقال تلقائياً إلى الطابق التالي: [{min(500, next_floor)}]**",
            color=discord.Color.gold()
        )
        embed_win.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed_win, ephemeral=False)
    else:
        # هزيمة
        embed_lose = discord.Embed(
            title=f"💀 هزيمة منكرة في الطابق [{current_floor}]",
            description=f"تم القضاء عليك بواسطة **{enemy_name}**!\n\n"
                        f"💬 {z_quote}\n\n"
                        f"**حالة المعركة الأخيرة:**\n"
                        f"{interaction.user.mention}: {p_bar}\n"
                        f"{enemy_name}: {e_bar}\n\n"
                        f"💡 **نصيحة الإمبراطورية:** طور معدلاتك القتالية أو اشترِ عتاداً أقوى من المتاجر قبل المحاولة مجدداً!",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed_lose, ephemeral=False)


class FloorsHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚔️ بدء المغامرة (الطابق الحالي)", style=discord.ButtonStyle.success, row=0)
    async def start_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await execute_battle(interaction, is_boss=False)

    @discord.ui.button(label="👹 مواجهة الـ BOSS", style=discord.ButtonStyle.danger, row=0)
    async def boss_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await execute_battle(interaction, is_boss=True)

    @discord.ui.button(label="🎒 حقيبتي والعتاد", style=discord.ButtonStyle.primary, row=1)
    async def view_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = users_col.find_one({"user_id": str(interaction.user.id)})
        inv = user.get("inventory", [])
        equipped = user.get("equipped", {}).get("active_weapon", "لا يوجد سلاح مجهز")
        
        embed = discord.Embed(
            title=f"🎒 حقيبة المقاتل — {user.get('name')}",
            description=f"⚔️ **السلاح المجهز حالياً:** `{equipped}`\n\n"
                        f"📦 **المحتويات المخزنة ({len(inv)} قطعة):**\n" +
                        ("\n".join([f"• {item}" for item in inv[:15]]) or "الحقيبة فارغة تماماً."),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, view=InventoryView(inv), ephemeral=True)

    @discord.ui.button(label="⚡ تطوير معداتي", style=discord.ButtonStyle.secondary, row=1)
    async def open_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = users_col.find_one({"user_id": str(interaction.user.id)})
        embed = discord.Embed(
            title="✨ مذبح تطوير القوى",
            description=f"رصيدك: `{user_data.get('balance', 0):,}` 🪙 | طاقتك: `{user_data.get('power', 0):,}` ⚡",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=True)

    @discord.ui.button(label="🏛️ المتجر العام", style=discord.ButtonStyle.secondary, row=2)
    async def open_general(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🏛️ متجر الإمبراطورية الملكي العام", description="تصفح العتاد والشراء بالذهب 🪙.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=True)

    @discord.ui.button(label="🔮 المتجر المظلم", style=discord.ButtonStyle.secondary, row=2)
    async def open_dark(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🔮 المتجر المظلم المحرم", description="سوق الأسلحة المحرمة برتب الشيطان الأبدي بالألماس 💎.", color=discord.Color.from_rgb(20, 0, 35))
        await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=True)


# ================== تسجيل وتنسيق الأوامر الرئيسية ==================
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
    embed = discord.Embed(title="🏛️ متجر الإمبراطورية الملكي العام", description="تصفح العتاد والشراء بالذهب 🪙.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=False)

@bot.tree.command(name="المتجر_المظلم", description="👁️ دخول سوق الظلال السري لشراء العتاد الأسطوري بالألماس")
async def dark_store(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    embed = discord.Embed(title="🔮 المتجر المظلم المحرم — Dark Sanctuary", description="سوق الأسلحة المحرمة بالألماس 💎.", color=discord.Color.from_rgb(20, 0, 35))
    await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=False)

@bot.tree.command(name="تطوير_المعدلات", description="⚡ فتح مذبح تطوير المعدلات القتالية كسر الحدود إلى المليارات")
async def upgrade_stats_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    embed = discord.Embed(title="✨ مذبح الصقل وتطوير القوى الإمبراطورية", description="تطوير المعدلات القتالية بلا حدود حتى المليارات.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=False)

@bot.tree.command(name="الترتيب", description="🏆 عرض لوحات الشرف والليدربورد لأعظم الشخصيات والنقابات")
async def leaderboard_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    embed = discord.Embed(title="👑 قاعة العظماء والليدربورد الإمبراطوري", description="اختر الفئة لعرض العظماء.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=LeaderboardView(), ephemeral=False)

@bot.tree.command(name="حقيبتي", description="🎒 فتح الحقيبة وتجهيز الأسلحة والمعدات")
async def inventory_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    user = users_col.find_one({"user_id": user_id})
    inv = user.get("inventory", [])
    equipped = user.get("equipped", {}).get("active_weapon", "لا يوجد سلاح مجهز")
    
    embed = discord.Embed(
        title=f"🎒 حقيبة المقاتل — {user.get('name')}",
        description=f"⚔️ **السلاح المجهز:** `{equipped}`\n\n"
                    f"📦 **المحتويات ({len(inv)} قطعة):**\n" +
                    ("\n".join([f"• {item}" for item in inv[:15]]) or "الحقيبة فارغة."),
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=InventoryView(inv), ephemeral=False)

@bot.tree.command(name="الطوابق", description="🏰 فتح مركز برج الـ 500 طابق وبدء المعارك والمغامرات")
async def floors_hub_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    user = users_col.find_one({"user_id": user_id})
    cur_floor = user.get("current_floor", 1)
    max_fl = user.get("max_floor", 1)

    embed = discord.Embed(
        title="🏰 برج التحدي الأسطوري — 500 طابق",
        description=f"مرحباً بك يا **{user.get('name')}** في مركز التحكم بالبرج!\n\n"
                    f"📍 **الطابق الحالي:** `{cur_floor} / 500`\n"
                    f"🏆 **أعلى طابق تم بلواغه:** `{max_fl}`\n"
                    f"⚡ **طاقتك القتالية:** `{user.get('power', 100):,}` ⚡\n\n"
                    "استخدم الأزرا أدناه للقتال والتنقل المباشر بين المتاجر وتطوير المعدلات والحقيبة:",
        color=discord.Color.dark_green()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=FloorsHubView(), ephemeral=False)

# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
