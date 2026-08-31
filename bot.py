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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== دالة التحقق من التسجيل ==================
def is_user_registered(user_id: str) -> bool:
    return users_col.find_one({"user_id": str(user_id)}) is not None


# ================== قاعدة بيانات 25 قطعة لكل فئة (المتاجر) ==================
CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]

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
    dark_ranks = ["السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي"]
    for i in range(21, 26):
        r_index = 0 if i <= 22 else (1 if i <= 24 else 2)
        rank_name = dark_ranks[r_index]
        GEAR_DATA[cat].append({
            "id": f"{cat}_{i}",
            "name": f"💀 {cat} [{rank_name}] T{i-20}",
            "rank": rank_name,
            "power": i * 180,
            "price": (i - 20) * 15,
            "currency": "diamonds",
            "store": "dark"
        })


# ================== نافذة منيو التسجيل (Modal) ==================
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
            "inventory": [],
            # المعدلات القتالية الأساسية
            "aim": 10,
            "evasion": 10,
            "attack": 10,
            "accuracy": 10,
            "critical": 10,
            "magic": 10,
            "intelligence": 10,
            "defense": 10
        }
        users_col.insert_one(new_user)

        embed_success = discord.Embed(title="👑 أهلاً بك في عرش الإمبراطورية!", description="تمت معالجة وثيقة هويتك بنجاح.", color=discord.Color.gold())
        embed_success.add_field(name="🪪 الاسم", value=f"`{self.name_input.value.strip()}`", inline=True)
        embed_success.add_field(name="⏳ العمر", value=f"`{age}` سنة", inline=True)
        embed_success.add_field(name="👤 الجنس", value=f"`{gender}`", inline=True)
        embed_success.add_field(name="🎁 مكافأة البداية", value="• `5,000` 🪙 ذهب\n• `20` 💎 ألماس", inline=False)
        await interaction.response.send_message(embed=embed_success, ephemeral=False)


# ================== 🛒 المتجر العام (General Store) ==================
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


# ================== 💀 المتجر المظلم (Dark Store) ==================
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


# ================== ⚡ نظام تطوير المعدلات (Upgrade Stats System) ==================

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
            min_length=1,
            max_length=20,
            required=True
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        try:
            points = int(self.amount_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة عدد نقاط صحيح كأرقام فقط!", ephemeral=True)

        if points <= 0:
            return await interaction.response.send_message("❌ يجب أن يكون عدد النقاط أكبر من 0!", ephemeral=True)

        total_cost = points * self.stat_info["cost"]
        user_data = users_col.find_one({"user_id": user_id})

        if user_data.get("balance", 0) < total_cost:
            return await interaction.response.send_message(
                f"❌ لا تملك ذهبًا كافيًا!\n• التكلفة المطلوبة: `{total_cost:,}` 🪙\n• رصيدك الحالي: `{user_data.get('balance', 0):,}` 🪙",
                ephemeral=True
            )

        # التحديث في قاعدة البيانات بحدود مفتوحة حتى المليارات
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": -total_cost,
                    self.stat_key: points,
                    "power": points * 10
                }
            }
        )

        embed_success = discord.Embed(
            title=f"🔥 انفجار القوة القتالية! — {self.stat_info['name']}",
            description=f"تم تطوير معدل **{self.stat_info['emoji']} {self.stat_info['name']}** بنجاح بلا حدود!",
            color=discord.Color.red()
        )
        embed_success.add_field(name="➕ النقاط المضافة", value=f"`+{points:,}` نقطة", inline=True)
        embed_success.add_field(name="💸 التكلفة الإجمالية", value=f"`{total_cost:,}` 🪙", inline=True)
        embed_success.add_field(name="⚡ القوة القتالية المكتسبة", value=f"`+{points * 10:,}` ⚡", inline=True)
        embed_success.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed_success, ephemeral=False)

class StatSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["name"],
                value=key,
                description=f"تطوير معدل {info['name']} (تكلفة النقطة: {info['cost']} 🪙)",
                emoji=info["emoji"]
            ) for key, info in STATS_CONFIG.items()
        ]
        super().__init__(placeholder="🔥 اختر المعدل الذي ترغب بتطويره...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        stat_info = STATS_CONFIG[selected_key]
        await interaction.response.send_modal(StatUpgradeModal(selected_key, stat_info))

class StatsUpgradeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(StatSelect())


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
        description="مرحباً بك في السوق الإمبراطوري. تصفح الأقسام واشترِ بالعملات الذهبية 🪙.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=GeneralStoreView(), ephemeral=False)

@bot.tree.command(name="المتجر_المظلم", description="👁️ دخول سوق الظلال السري لشراء العتاد الأسطوري بالألماس")
async def dark_store(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    
    embed = discord.Embed(
        title="🔮 المتجر المظلم المحرم — Dark Sanctuary",
        description="🌑 سوق الظلال السرية برتب الشيطان الأبدي، الجحيم القاتل، والسفاح القرمزي بالألماس 💎.",
        color=discord.Color.from_rgb(20, 0, 35)
    )
    await interaction.response.send_message(embed=embed, view=DarkStoreView(), ephemeral=False)

@bot.tree.command(name="تطوير_المعدلات", description="⚡ فتح مذبح تطوير المعدلات القتالية وكسر الحدود إلى المليارات")
async def upgrade_stats_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_user_registered(user_id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    user_data = users_col.find_one({"user_id": user_id})
    
    balance = user_data.get("balance", 0)
    power = user_data.get("power", 0)

    embed = discord.Embed(
        title="✨ مذبح الصقل وتطوير القوى الإمبراطورية",
        description="ارفع طاقتك و حَطِّم الحدود العظمى للمعدلات القتالية! لا يوجد حد أقصى للتطوير حتى لو تجاوزت ثروتك وقوتك المليارات.",
        color=discord.Color.red()
    )

    stats_display = (
        f"🎯 **التصويب:** `{user_data.get('aim', 10):,}`\n"
        f"💨 **المراوغة:** `{user_data.get('evasion', 10):,}`\n"
        f"🗡️ **الهجوم:** `{user_data.get('attack', 10):,}`\n"
        f"👁️ **الدقة:** `{user_data.get('accuracy', 10):,}`\n"
        f"💥 **الضربات القاتلة:** `{user_data.get('critical', 10):,}`\n"
        f"🔮 **السحر:** `{user_data.get('magic', 10):,}`\n"
        f"🧠 **الذكاء:** `{user_data.get('intelligence', 10):,}`\n"
        f"🛡️ **الدفاع:** `{user_data.get('defense', 10):,}`"
    )

    embed.add_field(name="📊 **سجل المعدلات الحالية**", value=stats_display, inline=False)
    embed.add_field(name="💰 **الذهب المتاح**", value=f"`{balance:,}` 🪙", inline=True)
    embed.add_field(name="⚡ **الطاقة الإجمالية**", value=f"`{power:,}` ⚡", inline=True)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="اختر المعدل من القائمة المنسدلة أدناه لفتح واجهة الترقيات اللافياسية.")

    await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=False)

# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
