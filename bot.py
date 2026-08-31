import os
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

# ================== 🏆 5. نظام الليدربورد والترتيب الفخم (Leaderboard System) ==================

def get_prestigious_badge(rank_num: int) -> str:
    """إرجاع شارة ملكية فخمة لكل مركز بالليدربورد"""
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
    
    embed = discord.Embed(title="🏛️ متجر الإمبراطورية الملكي العام", description="تصفح العتاد والشراء بالذهب 🪙.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=False)

@bot.tree.command(name="المتجر_المظلم", description="👁️ دخول سوق الظلال السري لشراء العتاد الأسطوري بالألماس")
async def dark_store(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    
    embed = discord.Embed(title="🔮 المتجر المظلم المحرم — Dark Sanctuary", description="سوق الأسلحة المحرمة برتب الشيطان الأبدي بالألماس 💎.", color=discord.Color.from_rgb(20, 0, 35))
    await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=False)

@bot.tree.command(name="تطوير_المعدلات", description="⚡ فتح مذبح تطوير المعدلات القتالية كسر الحدود إلى المليارات")
async def upgrade_stats_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    user_data = users_col.find_one({"user_id": user_id})
    embed = discord.Embed(title="✨ مذبح الصقل وتطوير القوى الإمبراطورية", description="تطوير المعدلات القتالية بلا حدود حتى المليارات.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=False)

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
