import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pymongo

# ================== ⚙️ 1. إعدادات البوت وقاعدة البيانات ==================

# ⚠️ ضع هنا ايدي (ID) حسابك الرئيسي في ديسكورد للتملك المطلق للبوت وشخصية السفاح
PRIMARY_DEV_ID = "1103985971638325269"

# الاتصال بقاعدة البيانات MongoDB (يمكنك وضع رابط الاتصال الخاص بك هنا)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = pymongo.MongoClient(MONGO_URI)
db = client["discord_rpg_bot"]

users_col = db["users"]
devs_col = db["developers"]

# إعدادات نوايا البوت (Intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== 🛠️ 2. الدوال المساعدة والحماية ==================

def is_user_registered(user_id: str) -> bool:
    """التحقق مما إذا كان المستخدم مسجلاً في البوت"""
    return users_col.find_one({"user_id": str(user_id)}) is not None

def is_developer(user_id: str) -> bool:
    """التحقق مما إذا كان المستخدم مطوراً"""
    if str(user_id) == str(PRIMARY_DEV_ID):
        return True
    return devs_col.find_one({"user_id": str(user_id)}) is not None

# بيانات عتاد افتراضية للوحة المطورين
CATEGORIES = ["أسلحة", "دروع"]
GEAR_DATA = {
    "أسلحة": [
        {"name": "⚔️ سيف التنين الأسطوري", "power": 15000, "rank": "UR", "store": "dark"},
        {"name": "🪄 عصا الفراغ المحرمة", "power": 18000, "rank": "UR", "store": "dark"},
        {"name": "🏹 قوس النجوم الفضي", "power": 12000, "rank": "SSR", "store": "dark"}
    ],
    "دروع": [
        {"name": "🛡️ درع الماجما الأسطوري", "power": 14000, "rank": "UR", "store": "dark"},
        {"name": "👑 تاج الملوك القدامى", "power": 16000, "rank": "UR", "store": "dark"}
    ]
}

# ================== 🏰 3. بيانات ونظام قاعة الأبطال (5 ذكور و 5 إناث) ==================

HEROES_DATA = {
    "male": [
        {
            "id": "m1",
            "name": "فاليريون — فارس التنين الخالد",
            "emoji": "🐉",
            "story": "وُلد من قلب بركان محترق وتمتع بدم التنانين القديمة. يحمل سيفاً مصقولاً بنار التنين الأسطورية التي لا تنطفئ أبداً.",
            "power": 12500,
            "stats": {"الهجوم": 95, "الدفاع": 90, "السحر": 70, "السرعة": 80, "ضربة قاتلة": 85}
        },
        {
            "id": "m2",
            "name": "كاليان — شبح الظلال السري",
            "emoji": "🗡️",
            "story": "سياف خفي يمتلك قدرة التنقل عبر الأبعاد والذوبان في الظلال. ضرباته خاطفة ولا تترك أثراً.",
            "power": 11800,
            "stats": {"الهجوم": 98, "الدفاع": 50, "السحر": 65, "السرعة": 100, "ضربة قاتلة": 99}
        },
        {
            "id": "m3",
            "name": "إغنيس — أمير اللهب الأبدي",
            "emoji": "🔥",
            "story": "ساحر قديم يسيطر على ألسنة الجحيم النارية. أحرق جيوشاً كاملة بكلمة واحدة من تعاويذه المحرمة.",
            "power": 13000,
            "stats": {"الهجوم": 100, "الدفاع": 60, "السحر": 100, "السرعة": 75, "ضربة قاتلة": 90}
        },
        {
            "id": "m4",
            "name": "أوريون — حارس الغابات الأسطوري",
            "emoji": "🏹",
            "story": "رامٍ استثنائي تستجيب لنقرات قوسه الوحوش الضارية. أسهمه السحرية لا تخطئ هدفها أبداً.",
            "power": 11200,
            "stats": {"الهجوم": 92, "الدفاع": 65, "السحر": 60, "السرعة": 95, "ضربة قاتلة": 92}
        },
        {
            "id": "m5",
            "name": "مالاكاي — ملك الأرواح المستدعاة",
            "emoji": "💀",
            "story": "حكيم سحري استطاع كسر حدود الموت، يستدعي جيوشاً من الفرسان العظميين لحمايته وتدمير أعدائه.",
            "power": 14000,
            "stats": {"الهجوم": 85, "الدفاع": 75, "السحر": 100, "السرعة": 60, "ضربة قاتلة": 80}
        }
    ],
    "female": [
        {
            "id": "f1",
            "name": "أليستريا — قدسية الضوء السماوي",
            "emoji": "✨",
            "story": "كاهنة نادرة تمتلك هالة شفائية قدسية تبدد الظلمات وتبطل السحر الأسود بلمسة واحدة.",
            "power": 12000,
            "stats": {"الهجوم": 70, "الدفاع": 85, "السحر": 98, "السرعة": 85, "ضربة قاتلة": 75}
        },
        {
            "id": "f2",
            "name": "سيرابينا — ملكة العواصف والرعد",
            "emoji": "⚡",
            "story": "ولدت في قلب إعصار مدمر واستوعبت طاقة الصواعق السماوية. تستدعي البرق لتشطير الجبال.",
            "power": 13500,
            "stats": {"الهجوم": 98, "الدفاع": 65, "السحر": 99, "السرعة": 90, "ضربة قاتلة": 95}
        },
        {
            "id": "f3",
            "name": "ليثيا — صيادة القمر المظلم",
            "emoji": "🌙",
            "story": "محاربة غامضة تتضاعف قوتها القتالية عند اكتمال القمر. تستخدم قوساً فضياً مصنوعاً من شظايا النجوم.",
            "power": 11900,
            "stats": {"الهجوم": 94, "الدفاع": 60, "السحر": 75, "السرعة": 98, "ضربة قاتلة": 96}
        },
        {
            "id": "f4",
            "name": "فالينتيا — الفالكيري الحديدية",
            "emoji": "🛡️",
            "story": "قائدة الجيوش الملكية وحاملة الدرع الأسطوري. تقف في الخطوط الأمامية وتستقبل أعتى الضربات دون تتزحزح.",
            "power": 12800,
            "stats": {"الهجوم": 88, "الدفاع": 100, "السحر": 50, "السرعة": 70, "ضربة قاتلة": 80}
        },
        {
            "id": "f5",
            "name": "مورغانا — سيدة الفراغ المحرم",
            "emoji": "🔮",
            "story": "ساحرة غامضة تتقن سحر الأبعاد والفراغ. قادرة على ابتلاع هجمات الخصوم وحبس الأعداء داخل ثقوب سوداء.",
            "power": 13800,
            "stats": {"الهجوم": 96, "الدفاع": 70, "السحر": 100, "السرعة": 80, "ضربة قاتلة": 88}
        }
    ]
}

class SpecificHeroSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        heroes = HEROES_DATA[category]
        options = [
            discord.SelectOption(
                label=h["name"],
                value=h["id"],
                description=f"القوة: {h['power']:,} ⚡ | اضغط لرؤية التفاصيل",
                emoji=h["emoji"]
            ) for h in heroes
        ]
        placeholder = "⚔️ اختر بطلاً..." if category == "male" else "🔮 اختر بطلة..."
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        hero_id = self.values[0]
        hero = next(h for h in HEROES_DATA[self.category] if h["id"] == hero_id)
        
        stats_text = "\n".join([f"• **{stat}:** `{val}`" for stat, val in hero["stats"].items()])
        
        embed = discord.Embed(
            title=f"{hero['emoji']} {hero['name']}",
            description=f"📜 **القصة والأسطورة:**\n*{hero['story']}*\n\n"
                        f"⚡ **القوة القتالية الأساسية:** `{hero['power']:,}`\n\n"
                        f"📊 **المعدلات والخصائص:**\n{stats_text}",
            color=discord.Color.gold() if self.category == "male" else discord.Color.purple()
        )
        embed.set_footer(text="🏰 قاعة عظماء إمبراطورية الفانتازيا")
        
        view = discord.ui.View()
        view.add_item(HeroCategorySelect())
        view.add_item(SpecificHeroSelect(self.category))
        await interaction.response.edit_message(embed=embed, view=view)

class HeroCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الأبطال الذكور (5 فرسان)", value="male", description="استعراض أعتى الفرسان والسحرة", emoji="⚔️"),
            discord.SelectOption(label="الأبطال الإناث (5 سيدات)", value="female", description="استعراض سيدات الحرب والسحر", emoji="🔮")
        ]
        super().__init__(placeholder="👑 اختر فئة الأبطال...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        view = discord.ui.View()
        view.add_item(HeroCategorySelect())
        view.add_item(SpecificHeroSelect(category))
        
        title_text = "⚔️ قاعة الأبطال الذكور" if category == "male" else "🔮 قاعة الأبطال الإناث"
        embed = discord.Embed(
            title=title_text,
            description="اختر البطل من القائمة المنسدلة الثانية لعرض التفاصيل!",
            color=discord.Color.blue() if category == "male" else discord.Color.magenta()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class HeroesHubView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HeroCategorySelect())

@bot.tree.command(name="الابطال", description="🏰 استعراض أبطال الإمبراطورية الأساطير (5 ذكور و 5 إناث)")
async def heroes_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    embed = discord.Embed(
        title="🏛️ قاعة أساطير الإمبراطورية — Heroes Sanctuary",
        description="أهلاً بك في قاعة الأبطال الأساطير!\n\n"
                    "• ⚔️ **5 أبطال ذكور:** القوة الساحقة، التنانين والظلال.\n"
                    "• 🔮 **5 أبطال إناث:** سحر الفراغ، العواصف، والضوء السماوي.\n\n"
                    "اختر الفئة التي تريد استعراضها من القائمة أسفله:",
        color=discord.Color.dark_gold()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=HeroesHubView(), ephemeral=False)

# ================== 👑 4. نظام لوحة المطورين والشخصية الخارقة ==================

SAFFAH_HERO_DATA = {
    "name": "🩸 السفاح — سيد الفراغ والعرش المحرم",
    "emoji": "☠️",
    "story": (
        "سليل الظلمات الأولى وقاطن عرش الجماجم.. كيان أسطوري لا يُقهر، وُلد قبل قيام البرج وعوالم الفانتازيا.\n"
        "تحت قاطعي سيفه تنهار الممالك، وتتلاشى طاقة العظماء إلى رماد بمجرد نظرة من عينيه الحمراوين.\n"
        "لا يجرؤ حاكم ولا إله في هذا العالم على مواجهته؛ فهو تجسيد مطلق للموت والسيادة!"
    ),
    "power": 999999999999,
    "stats": {
        "الهجوم": 999999,
        "الدفاع": 999999,
        "السحر": 999999,
        "السرعة": 999999,
        "الدقة": 999999,
        "الضربة القاتلة": 100
    }
}

class TransferMoneyModal(discord.ui.Modal, title="💸 شحن وتحويل الثروات الإمبراطورية"):
    gold_input = discord.ui.TextInput(label="مقدار الذهب 🪙", placeholder="مثال: 1000000", min_length=1, required=True)
    diamonds_input = discord.ui.TextInput(label="مقدار الألماس 💎", placeholder="مثال: 50000", min_length=1, required=True)

    def __init__(self, target_user: discord.User):
        super().__init__()
        self.target_user = target_user

    async def on_submit(self, interaction: discord.Interaction):
        try:
            gold = int(self.gold_input.value.strip())
            diamonds = int(self.diamonds_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ يرجى كتابة أرقام صحيحة!", ephemeral=True)

        target_id = str(self.target_user.id)
        if not is_user_registered(target_id):
            return await interaction.response.send_message("❌ هذا العضو غير مسجل في قاعدة البيانات!", ephemeral=True)

        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": gold, "diamonds": diamonds}})
        
        embed = discord.Embed(
            title="✨ تم ضخ العملات بنجاح!",
            description=f"👑 تم منح المقاتل {self.target_user.mention}:\n"
                        f"• 🪙 **ذهب:** `+{gold:,}`\n"
                        f"• 💎 **ألماس:** `+{diamonds:,}`",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AddDevUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="👤 اختر العضو بالمنشن لإضافته كمطور...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_user = self.values[0]
        user_id_str = str(selected_user.id)

        if is_developer(user_id_str):
            return await interaction.response.send_message(f"⚠️ **{selected_user.name}** مسجل بالفعل كمطور!", ephemeral=True)

        devs_col.insert_one({"user_id": user_id_str, "added_by": str(interaction.user.id), "added_at": datetime.utcnow()})
        
        embed = discord.Embed(
            title="🔱 إضافة مطور جديد!",
            description=f"تم منح **{selected_user.mention}** صلاحيات المطور ولوحة التحكم!",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TransferUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="💸 اختر العضو بالمنشن لتحويل العملات له...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_user = self.values[0]
        await interaction.response.send_modal(TransferMoneyModal(target_user=selected_user))

class GiveGearUserSelect(discord.ui.UserSelect):
    def __init__(self, item_name: str, item_power: int):
        super().__init__(placeholder="🎁 اختر العضو بالمنشن لإهدائه العتاد...", min_values=1, max_values=1)
        self.item_name = item_name
        self.item_power = item_power

    async def callback(self, interaction: discord.Interaction):
        selected_user = self.values[0]
        target_id = str(selected_user.id)
        
        if not is_user_registered(target_id):
            return await interaction.response.send_message("❌ هذا العضو غير مسجل في قاعدة البيانات!", ephemeral=True)

        users_col.update_one(
            {"user_id": target_id},
            {"$push": {"inventory": self.item_name}, "$inc": {"power": self.item_power}}
        )
        
        embed = discord.Embed(
            title="⚔️ منح عتاد أسطوري!",
            description=f"تم إرسال العتاد **[{self.item_name}]** إلى حقيبة {selected_user.mention} وزادت طاقته بـ `+{self.item_power:,}` ⚡!",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SelectGearForTarget(discord.ui.Select):
    def __init__(self, mode: str):
        self.mode = mode
        all_gear = []
        for cat in CATEGORIES:
            all_gear.extend(GEAR_DATA[cat])
        
        options = [
            discord.SelectOption(
                label=g["name"], value=f"{g['name']}|{g['power']}",
                description=f"القوة: +{g['power']:,} | الرتبة: {g['rank']}", emoji="🔥"
            ) for g in all_gear
        ]
        placeholder = "⚔️ اختر العتاد لنفسك..." if mode == "self" else "🎁 اختر العتاد للعضو..."
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        item_name, item_power = self.values[0].split("|")
        item_power = int(item_power)

        if self.mode == "self":
            users_col.update_one(
                {"user_id": str(interaction.user.id)},
                {"$push": {"inventory": item_name}, "$inc": {"power": item_power}}
            )
            return await interaction.response.send_message(f"⚔️ تم إضافة **[{item_name}]** بحقيبتك وزيادة طاقتك بـ `+{item_power:,}` ⚡!", ephemeral=True)
        else:
            view = discord.ui.View()
            view.add_item(GiveGearUserSelect(item_name=item_name, item_power=item_power))
            await interaction.response.send_message("👇 **حدد العضو من القائمة المنسدلة بالمنشن المباشر:**", view=view, ephemeral=True)

class DevPanelOptionsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="إضافة مطور جديد", value="add_dev", description="منح رتبة المطور بالمنشن المباشر", emoji="👑"),
            discord.SelectOption(label="عملات لا نهائية", value="inf_money", description="شحن ذهب وألماس لا نهائي لحسابك", emoji="♾️"),
            discord.SelectOption(label="تحويل عملات لأي عضو", value="transfer_money", description="إرسال ثروات لأي شخص بالمنشن المباشر", emoji="💸"),
            discord.SelectOption(label="إضافة عتاد لنفسك", value="gear_self", description="منح أعتى الأسلحة والعتاد لنفسك", emoji="⚔️"),
            discord.SelectOption(label="إضافة عتاد لأي شخص", value="gear_other", description="إرسال عتاد أسطوري لأي شخص بالمنشن", emoji="🎁"),
            discord.SelectOption(label="استدعاء شخصية السفاح الخارقة", value="saffah_hero", description="خاص بالمطور الأساسي فقط — تفعيل الهيمنة المطلقة", emoji="🩸")
        ]
        super().__init__(placeholder="🌌 اختر إجراءً من لوحة السيادة المطلقة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        val = self.values[0]

        if val == "add_dev":
            view = discord.ui.View()
            view.add_item(AddDevUserSelect())
            await interaction.response.send_message("👑 **اختر الحساب المراد رفعه لدرجة مطور بالمنشن:**", view=view, ephemeral=True)

        elif val == "inf_money":
            users_col.update_one({"user_id": user_id}, {"$set": {"balance": 999999999999, "diamonds": 999999999}})
            embed = discord.Embed(
                title="♾️ تم تفعيل الثروة المطلقة!",
                description="تم إضافة `999,999,999,999` 🪙 ذهب و `999,999,999` 💎 ألماس لحسابك!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif val == "transfer_money":
            view = discord.ui.View()
            view.add_item(TransferUserSelect())
            await interaction.response.send_message("💸 **حدد العضو المراد شحن العملات له بالمنشن:**", view=view, ephemeral=True)

        elif val == "gear_self":
            view = discord.ui.View()
            view.add_item(SelectGearForTarget(mode="self"))
            await interaction.response.send_message("⚔️ **اختر القطعة المراد تزويد حقيبتك بها:**", view=view, ephemeral=True)

        elif val == "gear_other":
            view = discord.ui.View()
            view.add_item(SelectGearForTarget(mode="other"))
            await interaction.response.send_message("🎁 **اختر العتاد أولاً ثم حدد الشخص بالمنشن:**", view=view, ephemeral=True)

        elif val == "saffah_hero":
            if user_id != str(PRIMARY_DEV_ID):
                return await interaction.response.send_message("⛔ **هذا الخيار محرم تماماً!** خُصص فقط للمطور الأساسي!", ephemeral=True)

            stats_str = "\n".join([f"• **{k}:** `{v:,}`" for k, v in SAFFAH_HERO_DATA["stats"].items()])
            
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "custom_title": "🩸 السفاح الأعظم",
                        "power": SAFFAH_HERO_DATA["power"],
                        "attack": 999999,
                        "defense": 999999,
                        "magic": 999999,
                        "critical": 100
                    },
                    "$push": {"inventory": "🗡️ سيف السفاح المحرم (سلاح الفراغ)"}
                }
            )

            embed = discord.Embed(
                title=f"{SAFFAH_HERO_DATA['emoji']} {SAFFAH_HERO_DATA['name']}",
                description=f"📜 **الأسطورة المحرمة:**\n*{SAFFAH_HERO_DATA['story']}*\n\n"
                            f"⚡ **القوة القتالية المطلقة:** `{SAFFAH_HERO_DATA['power']:,}`\n\n"
                            f"📊 **المعدلات الخارقة المفعلة:**\n{stats_str}\n\n"
                            f"🔥 **تم تزويد حسابك بلقب وقوة وسلاح السفاح فوراً!**",
                color=discord.Color.from_rgb(139, 0, 0)
            )
            embed.set_footer(text="🩸 الحصانة المطلقة للمطور الأساسي")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class DevPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DevPanelOptionsSelect())

@bot.tree.command(name="لوحة_المطورين", description="👑 فتح لوحة السيادة الإمبراطورية (للمطورين فقط)")
async def dev_panel_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if not is_developer(user_id):
        return await interaction.response.send_message(
            "🛑 **وصول مرفوض!** هذه القاعة محمية بسحر المطورين العظماء!",
            ephemeral=True
        )

    embed = discord.Embed(
        title="🌌 لوحة السيادة الملكية للمطورين — Dev Imperial Sanctuary",
        description="أهلاً بك يا سيد العرش والمطور القدير!\n\n"
                    "👑 **صلاحياتك المتاحة:**\n"
                    "• 👤 **تعيين مطورين:** إضافة مطور جديد عبر المنشن.\n"
                    "• ♾️ **الثروة المطلقة:** شحن مليارات الذهب والألماس.\n"
                    "• 💸 **تحويل الثروات:** ضخ عملات لأي عضو بالمنشن.\n"
                    "• ⚔️ **العتاد الملكي:** إهداء الأسلحة لنفسك أو لأي مقاتل.\n"
                    "• 🩸 **شخصية السفاح:** تفعيل قوة وسلاح السفاح الخارق (للمطور الأساسي).\n",
        color=discord.Color.dark_purple()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=DevPanelView(), ephemeral=True)

# ================== 📝 5. أمر التسجيل الأولي ==================

@bot.tree.command(name="تسجيل", description="📝 التسجيل وبدء مغامرتك في الإمبراطورية")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if is_user_registered(user_id):
        return await interaction.response.send_message("⚠️ أنت مسجل بالفعل في نظام الإمبراطورية!", ephemeral=True)

    users_col.insert_one({
        "user_id": user_id,
        "username": interaction.user.name,
        "balance": 1000,
        "diamonds": 50,
        "power": 100,
        "inventory": [],
        "created_at": datetime.utcnow()
    })
    
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح في الإمبراطورية!** يمكنك الآن استخدام أمر `/الابطال`.", ephemeral=True)

# ================== 🚀 6. تشغيل البوت ومزامنة الأوامر ==================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح باسم: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"⚡ تم مزامنة {len(synced)} أمر من أوامر Slash بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء مزامنة الأوامر: {e}")

# تشغيل البوت باستعمال التوكين من المتغيرات البيئية أو كتابته مباشرة
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "ضع_توكين_البوت_هنا")
bot.run(BOT_TOKEN)
