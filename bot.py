import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# ================== ⚙️ إعدادات الاتصال والبوت ==================
# قراءة رابط قاعدة البيانات والـ Token من متغيرات البيئة
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
db_client = MongoClient(MONGO_URL)
db = db_client["empire_bot"]
users_col = db["users"]

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)


def is_user_registered(user_id):
    """التحقق مما إذا كان المستخدم مسجلاً مسبقاً"""
    return users_col.find_one({"user_id": str(user_id)}) is not None


@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        print(f"✅ تم تسجيل دخول البوت بنجاح باسم: {client.user}")
        print(f"🔗 تم مزامنة {len(synced)} أمر (Slash Commands) بنجاح.")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")


# ================== 🏆 نظام الليدربورد والترتيبات الإمبراطورية ==================
from collections import defaultdict

# تجهيز قائمة مسطحة للأسلحة العادية والمظلمة عشان البحث السريع
NORMAL_GEAR_CATEGORIES = {
    "خوذة": [
        {"name": "🪖 خوذة الحرس الملكي", "power": 300, "price_gold": 1500, "rank": "عادي"},
        {"name": "🪖 خوذة الفولاذ الصلب", "power": 600, "price_gold": 3200, "rank": "مطور"},
        {"name": "🪖 خوذة الصقر الذهبي", "power": 1200, "price_gold": 7000, "rank": "نادر"}
    ],
    "درع": [
        {"name": "🛡️ درع الفرسان المشاة", "power": 500, "price_gold": 2500, "rank": "عادي"},
        {"name": "🛡️ درع الحديد المصفح", "power": 900, "price_gold": 5000, "rank": "مطور"},
        {"name": "🛡️ درع الفرسان الأحرار", "power": 1500, "price_gold": 9500, "rank": "نادر"}
    ],
    "بنطال": [
        {"name": "👖 بنطال الجلد القماشي", "power": 200, "price_gold": 1000, "rank": "عادي"},
        {"name": "👖 بنطال الحديد الملعون", "power": 450, "price_gold": 2200, "rank": "مطور"},
        {"name": "👖 بنطال الحراس الملكيين", "power": 850, "price_gold": 4500, "rank": "نادر"}
    ],
    "حذاء": [
        {"name": "👢 حذاء السفر الجلدي", "power": 150, "price_gold": 800, "rank": "عادي"},
        {"name": "👢 حذاء الفرسان السريع", "power": 350, "price_gold": 1800, "rank": "مطور"},
        {"name": "👢 حذاء الرياح الخفية", "power": 700, "price_gold": 3800, "rank": "نادر"}
    ],
    "سيف": [
        {"name": "⚔️ سيف الجندي البسيط", "power": 700, "price_gold": 3000, "rank": "عادي"},
        {"name": "⚔️ سيف الفارس القاطع", "power": 1400, "price_gold": 6500, "rank": "مطور"},
        {"name": "⚔️ سيف اللهب الملكي", "power": 2500, "price_gold": 12000, "rank": "نادر"}
    ],
    "مطرقة": [
        {"name": "🔨 مطرقة الحداد الخشنة", "power": 800, "price_gold": 3500, "rank": "عادي"},
        {"name": "🔨 مطرقة الأرض المحطمة", "power": 1600, "price_gold": 7500, "rank": "مطور"},
        {"name": "🔨 مطرقة التيتانيوم الثقيلة", "power": 2800, "price_gold": 13500, "rank": "نادر"}
    ],
    "خنجر": [
        {"name": "🗡️ خنجر الظل الصغير", "power": 400, "price_gold": 2000, "rank": "عادي"},
        {"name": "🗡️ خنجر القاتل الخفي", "power": 900, "price_gold": 4500, "rank": "مطور"},
        {"name": "🗡️ خنجر الأفعى السامة", "power": 1700, "price_gold": 8500, "rank": "نادر"}
    ],
    "عصا سحرية": [
        {"name": "🪄 عصا المبتدئ السحرية", "power": 600, "price_gold": 2800, "rank": "عادي"},
        {"name": "🪄 عصا اللهب الأزرق", "power": 1300, "price_gold": 6000, "rank": "مطور"},
        {"name": "🪄 عصا النجوم المضيئة", "power": 2400, "price_gold": 11000, "rank": "نادر"}
    ]
}

DARK_GEAR_CATEGORIES = {
    "خوذة": [
        {"name": "🩸 خوذة الجحيم المظلمة", "power": 25000, "price_diamonds": 100, "rank": "الشيطان الأبدي"},
        {"name": "💀 خوذة الأرواح المعذبة", "power": 18000, "price_diamonds": 70, "rank": "الجحيم القاتل"},
        {"name": "🗡️ خوذة الظل الدموي", "power": 12000, "price_diamonds": 45, "rank": "السفاح القرمزي"}
    ],
    "درع": [
        {"name": "🩸 درع التنين الأسود الأبدي", "power": 35000, "price_diamonds": 150, "rank": "الشيطان الأبدي"},
        {"name": "💀 درع الفوضى العارمة", "power": 26000, "price_diamonds": 110, "rank": "الجحيم القاتل"},
        {"name": "🗡️ درع الهلاك القرمزي", "power": 19000, "price_diamonds": 80, "rank": "السفاح القرمزي"}
    ],
    "بنطال": [
        {"name": "🩸 بنطال الهاوية السوداء", "power": 22000, "price_diamonds": 90, "rank": "الشيطان الأبدي"},
        {"name": "💀 بنطال رعب الكهوف", "power": 16000, "price_diamonds": 60, "rank": "الجحيم القاتل"},
        {"name": "🗡️ بنطال القاتل الصامت", "power": 11000, "price_diamonds": 40, "rank": "السفاح القرمزي"}
    ],
    "حذاء": [
        {"name": "🩸 حذاء خطوات الجحيم", "power": 20000, "price_diamonds": 85, "rank": "الشيطان الأبدي"},
        {"name": "💀 حذاء البرق الأسود", "power": 15000, "price_diamonds": 55, "rank": "الجحيم القاتل"},
        {"name": "🗡️ حذاء الانقضاض السريع", "power": 10000, "price_diamonds": 35, "rank": "السفاح القرمزي"}
    ],
    "سيف": [
        {"name": "🩸 سيف عذاب الأرواح الأبدي", "power": 50000, "price_diamonds": 250, "rank": "الشيطان الأبدي"},
        {"name": "💀 سيف الهلاك الشامل", "power": 38000, "price_diamonds": 180, "rank": "الجحيم القاتل"},
        {"name": "🗡️ سيف الدم الشره", "power": 28000, "price_diamonds": 120, "rank": "السفاح القرمزي"}
    ],
    "مطرقة": [
        {"name": "🩸 مطرقة تحطيم العوالم الأبدية", "power": 55000, "price_diamonds": 270, "rank": "الشيطان الأبدي"},
        {"name": "💀 مطرقة زلازل الجحيم", "power": 40000, "price_diamonds": 190, "rank": "الجحيم القاتل"},
        {"name": "🗡️ مطرقة الغضب القرمزي", "power": 30000, "price_diamonds": 130, "rank": "السفاح القرمزي"}
    ],
    "خنجر": [
        {"name": "🩸 خنجر الموت المحتوم", "power": 45000, "price_diamonds": 220, "rank": "الشيطان الأبدي"},
        {"name": "💀 خنجر السموم القاتلة", "power": 33000, "price_diamonds": 150, "rank": "الجحيم القاتل"},
        {"name": "🗡️ خنجر الظل الدموي السريع", "power": 24000, "price_diamonds": 100, "rank": "السفاح القرمزي"}
    ],
    "عصا سحرية": [
        {"name": "🩸 عصا الفراغ والظلام المطلق", "power": 52000, "price_diamonds": 260, "rank": "الشيطان الأبدي"},
        {"name": "💀 عصا اللهب الأسود المحرق", "power": 39000, "price_diamonds": 185, "rank": "الجحيم القاتل"},
        {"name": "🗡️ عصا التعاويذ المحرمة", "power": 29000, "price_diamonds": 125, "rank": "السفاح القرمزي"}
    ]
}

FLAT_NORMAL_GEAR = {}
for category, items in NORMAL_GEAR_CATEGORIES.items():
    for item in items:
        FLAT_NORMAL_GEAR[item["name"]] = item["power"]

FLAT_DARK_GEAR = {}
for category, items in DARK_GEAR_CATEGORIES.items():
    for item in items:
        FLAT_DARK_GEAR[item["name"]] = item["power"]


class LeaderboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="👑 أغنى شخص", value="rich", description="ترتيب اللاعبين حسب كمية الذهب", emoji="🪙"),
            discord.SelectOption(label="⚡ أقوى شخص", value="power", description="ترتيب اللاعبين حسب القوة الكلية", emoji="💥"),
            discord.SelectOption(label="⚔️ قاهر اللاعبين", value="pvp", description="ترتيب اللاعبين حسب عدد الانتصارات", emoji="🏅"),
            discord.SelectOption(label="🗡️ الأسلحة الإمبراطورية", value="normal_gear", description="ترتيب اللاعبين حسب قوة الأسلحة العادية", emoji="🛡️"),
            discord.SelectOption(label="🩸 الأسلحة المحرمة", value="dark_gear", description="ترتيب اللاعبين حسب قوة الأسلحة المظلمة", emoji="🌑"),
            discord.SelectOption(label="🏷️ الألقاب", value="titles", description="ترتيب اللاعبين حسب عدد الألقاب", emoji="📜"),
            discord.SelectOption(label="🏰 الطوابق", value="floors", description="ترتيب اللاعبين حسب أعلى طابق وصلوا له", emoji="🏗️"),
            discord.SelectOption(label="🏴 نقابات", value="guilds", description="ترتيب النقابات حسب مجموع القوة", emoji="🚩"),
        ]
        super().__init__(placeholder="🏆 اختر نوع الترتيب الذي تريد عرضه...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        embed = discord.Embed(color=discord.Color.gold())
        
        # محاولة جلب صورة السيرفر إذا موجودة وإلا استخدم صورة المستخدم
        try:
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild else interaction.user.display_avatar.url)
        except:
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        all_users = list(users_col.find({}))

        if choice == "rich":
            sorted_users = sorted(all_users, key=lambda x: x.get("balance", 0), reverse=True)
            embed.title = "👑 قائمة أغنى أباطرة الإمبراطورية"
            embed.description = "ترتيب العظماء حسب ثروتهم الذهبية 🪙"
            for idx, user in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user["user_id"])
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"🪙 `{user.get('balance', 0):,}` ذهب",
                    inline=False
                )

        elif choice == "power":
            sorted_users = sorted(all_users, key=lambda x: x.get("power", 0), reverse=True)
            embed.title = "⚡ قائمة أقوى محاربي الإمبراطورية"
            embed.description = "ترتيب العمالقة حسب القوة المطلقة 💥"
            for idx, user in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user["user_id"])
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"⚡ `{user.get('power', 0):,}` قوة",
                    inline=False
                )

        elif choice == "pvp":
            sorted_users = sorted(all_users, key=lambda x: x.get("wins", 0), reverse=True)
            embed.title = "⚔️ قائمة قاهري اللاعبين"
            embed.description = "ترتيب الأساطير حسب عدد الانتصارات في المعارك 🏅"
            for idx, user in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user["user_id"])
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"🏅 `{user.get('wins', 0)}` فوز",
                    inline=False
                )

        elif choice == "normal_gear":
            user_gear_power = {}
            for user in all_users:
                total = 0
                for item_name in user.get("inventory", []):
                    total += FLAT_NORMAL_GEAR.get(item_name, 0)
                user_gear_power[user["user_id"]] = total
            sorted_users = sorted(user_gear_power.items(), key=lambda x: x[1], reverse=True)
            embed.title = "🗡️ ترتيب الأسلحة الإمبراطورية"
            embed.description = "ترتيب اللاعبين حسب قوة أسلحتهم العادية 🛡️"
            for idx, (user_id, total_power) in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user_id)
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"⚔️ `{total_power:,}` قوة أسلحة",
                    inline=False
                )

        elif choice == "dark_gear":
            user_gear_power = {}
            for user in all_users:
                total = 0
                for item_name in user.get("inventory", []):
                    total += FLAT_DARK_GEAR.get(item_name, 0)
                user_gear_power[user["user_id"]] = total
            sorted_users = sorted(user_gear_power.items(), key=lambda x: x[1], reverse=True)
            embed.title = "🩸 ترتيب الأسلحة المحرمة"
            embed.description = "ترتيب اللاعبين حسب قوة أسلحتهم المظلمة 🌑"
            for idx, (user_id, total_power) in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user_id)
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"🗡️ `{total_power:,}` قوة محرمة",
                    inline=False
                )

        elif choice == "titles":
            sorted_users = sorted(all_users, key=lambda x: len(x.get("titles", [])), reverse=True)
            embed.title = "🏷️ ترتيب الألقاب الإمبراطورية"
            embed.description = "ترتيب اللاعبين حسب عدد الألقاب التي حصلوا عليها 📜"
            for idx, user in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user["user_id"])
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"📜 `{len(user.get('titles', []))}` لقب",
                    inline=False
                )

        elif choice == "floors":
            sorted_users = sorted(all_users, key=lambda x: x.get("max_floor", 0), reverse=True)
            embed.title = "🏰 ترتيب الطوابق"
            embed.description = "ترتيب اللاعبين حسب أعلى طابق استطاعوا الوصول إليه 🏗️"
            for idx, user in enumerate(sorted_users[:10], 1):
                name = await self.get_user_name(interaction, user["user_id"])
                embed.add_field(
                    name=f"#{idx} {name}",
                    value=f"🏗️ الطابق `{user.get('max_floor', 0)}`",
                    inline=False
                )

        elif choice == "guilds":
            guild_power = defaultdict(int)
            for user in all_users:
                guild = user.get("guild")
                if guild:
                    guild_power[guild] += user.get("power", 0)
            sorted_guilds = sorted(guild_power.items(), key=lambda x: x[1], reverse=True)
            embed.title = "🏴 ترتيب أقوى النقابات"
            embed.description = "ترتيب النقابات حسب مجموع قوة أعضائها 🚩"
            for idx, (guild_name, total_power) in enumerate(sorted_guilds[:10], 1):
                embed.add_field(
                    name=f"#{idx} {guild_name}",
                    value=f"💥 `{total_power:,}` قوة إجمالية",
                    inline=False
                )

        if not embed.fields:
            embed.description = "❌ لا توجد بيانات كافية لعرض هذا الترتيب حالياً."

        embed.set_footer(text=f"طلب بواسطة {interaction.user.display_name} • تحديث فوري")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.edit_message(embed=embed, view=LeaderboardView())

    async def get_user_name(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await interaction.client.fetch_user(int(user_id))
            return user.display_name
        except:
            return f"مغامر مجهول"


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderboardSelect())

        # زر تحديث
        refresh_btn = discord.ui.Button(label="🔄 تحديث الترتيب", style=discord.ButtonStyle.primary)
        async def refresh_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🏆 لوحة الشرف الإمبراطورية",
                description="اختر نوع الترتيب الذي تريد عرضه من القائمة المنسدلة أدناه:\n\n"
                            "• **👑 أغنى شخص**\n• **⚡ أقوى شخص**\n• **⚔️ قاهر اللاعبين**\n"
                            "• **🗡️ الأسلحة الإمبراطورية**\n• **🩸 الأسلحة المحرمة**\n• **🏷️ الألقاب**\n"
                            "• **🏰 الطوابق**\n• **🏴 نقابات**",
                color=discord.Color.gold()
            )
            try:
                embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild else interaction.user.display_avatar.url)
            except:
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
        refresh_btn.callback = refresh_callback
        self.add_item(refresh_btn)


@client.tree.command(name="الترتيب", description="🏆 عرض لوحة الشرف والترتيبات الإمبراطورية")
async def leaderboard_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)
    
    embed = discord.Embed(
        title="🏆 لوحة الشرف الإمبراطورية",
        description="مرحباً بك في قاعة المجد!\nاختر نوع الترتيب الذي تريد عرضه من القائمة المنسدلة أدناه:\n\n"
                    "• **👑 أغنى شخص** - تصدر حسب الذهب\n"
                    "• **⚡ أقوى شخص** - تصدر حسب القوة\n"
                    "• **⚔️ قاهر اللاعبين** - تصدر حسب الانتصارات\n"
                    "• **🗡️ الأسلحة الإمبراطورية** - تصدر حسب قوة الأسلحة العادية\n"
                    "• **🩸 الأسلحة المحرمة** - تصدر حسب قوة الأسلحة المظلمة\n"
                    "• **🏷️ الألقاب** - تصدر حسب عدد الألقاب\n"
                    "• **🏰 الطوابق** - تصدر حسب أعلى طابق\n"
                    "• **🏴 نقابات** - تصدر حسب قوة النقابة",
        color=discord.Color.gold()
    )
    try:
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild else interaction.user.display_avatar.url)
    except:
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="جميع الترتيبات تُحدّث تلقائياً مع كل إجراء جديد")
    
    await interaction.response.send_message(embed=embed, view=LeaderboardView(), ephemeral=True)


# ================== 🚀 تشغيل البوت ==================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ خطأ: يرجى وضع التوكن الخاص بالبوت في متغير البيئة DISCORD_TOKEN.")
