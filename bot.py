import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]
devs_col = db["devs"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

OWNER_ID = 1103985971638325269

def is_developer(user_id):
    if user_id == OWNER_ID:
        return True
    return devs_col.find_one({"user_id": str(user_id)}) is not None

def extract_user_id(text):
    clean = text.strip().replace("<@", "").replace(">", "").replace("!", "")
    return str(int(clean))

# ================== قاعدة بيانات الأبطال ==================
HEROES_DATA = {
    "zeal": {
        "name": "زيل - كاسر الظلال (Zeal)",
        "gender": "ذكر",
        "emoji": "⚡",
        "power": "سرعة البرق الخاطفة والتحكم في طاقة البلازما المدمرة",
        "story": "محارب وُلِد في قلب العواصف الرعدية الكونية. استطاع دمج روحه بطاقة البرق، ليصبح شبحاً لا يطال."
    },
    "draven": {
        "name": "دريفان - سيد الجحيم (Draven)",
        "gender": "ذكر",
        "emoji": "🔥",
        "power": "استدعاء نيران التنانين الأسطورية وتصلب الجلد البركاني",
        "story": "قائد عسكري سابق لجيوش الحمم المظلمة. عاهد نفسه على حرق كل ظالم بسيفه الملتهب."
    },
    "kaelen": {
        "name": "كايلين - حارس الأبعاد (Kaelen)",
        "gender": "ذكر",
        "emoji": "🌌",
        "power": "التلاعب بالزمن والقدرة على فتح ثواني للقفز بين الأبعاد",
        "story": "حكيم كوني أمضى آلاف السنين يدرس أسرار الكون والفضاء السحيق."
    },
    "lyra": {
        "name": "ليرا - ملكة الصقيع (Lyra)",
        "gender": "أنثى",
        "emoji": "❄️",
        "power": "تجميد جزيئات الهواء المطلق وصنع أسلحة من الجليد الصلب",
        "story": "أميرة قطبية أُمطرت مدينتها بلعنة النار، فتحولت إلى عاصفة حية لا تقهر."
    },
    "vortexa": {
        "name": "فورتيكسا - ساحرة الثقوب السوداء (Vortexa)",
        "gender": "أنثى",
        "emoji": "🌀",
        "power": "امتصاص ضربات الخصوم وإطلاقها كطاقة جاذبية مميتة",
        "story": "مقاتلة استدمجت طاقة الثقوب السوداء في جسدها لتسحق كل معارض."
    },
    "valeria": {
        "name": "فاليريا - فارسة الفجر الذهبي (Valeria)",
        "gender": "أنثى",
        "emoji": "☀️",
        "power": "الشفاء السريع، القوة البدنية المطلقة، وهالة النور المقدس",
        "story": "قائدة حرس الفجر الأسطوريون تحمل درعاً مقدساً لا ينكسر."
    },
    "assassin_dev": {
        "name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)",
        "gender": "مطور مطلق",
        "emoji": "🩸",
        "power": "طمس الوجود، التحكم المطلق في الأكوان، ومحو أي كائن بنظرة واحدة",
        "story": "كيان مرعب هبط من الفراغ المطلق، وُجد ليكون اليد القاضية التي لا ترتجف.",
        "stats": {
            "power": 9999999,
            "max_floor": 999,
            "kills": 99999
        }
    }
}

# قائمة الأبطال العامة
class HeroSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=data["name"], description=f"الجنس: {data['gender']} | القوة: {data['power'][:35]}...", emoji=data["emoji"], value=key)
            for key, data in HEROES_DATA.items() if key != "assassin_dev"
        ]
        super().__init__(placeholder="اختر بطلك الأسطوري لتستعرض قصته وقوته...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        hero_key = self.values[0]
        hero = HEROES_DATA[hero_key]
        embed = discord.Embed(
            title=f"{hero['emoji']} تفاصيل البطل الأسطوري: {hero['name']}",
            description=f"**الجنس:** `{hero['gender']}`\n\n🛡️ **القدرة الخارقة:**\n{hero['power']}\n\n📜 **القصة الملحمية:**\n*{hero['story']}*",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"selected_hero": hero['name']}}, upsert=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HeroSelect())

@bot.tree.command(name="أبطال", description="استعراض قائمة الأبطال الأسطوريين واختيار بطلك المفضل")
async def heroes_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة اختيار الأبطال الأسطوريين 🛡️",
        description="«اختر بطلك بحكمة، فالقصة والقوة التي ستختارها سترافقك في جميع المعارك.»",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=HeroSelectView(), ephemeral=False)


# ================== نظام البنك الفخم (Menu & Modals) ==================

class BankDepositModal(discord.ui.Modal, title="إيداع أموال في خزينة البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد إيداعه", placeholder="مثال: 100000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value)
            user_id = str(interaction.user.id)
            user_data = users_col.find_one({"user_id": user_id})
            wallet = user_data.get("balance", 0)
            if wallet < val or val <= 0:
                return await interaction.response.send_message("❌ رصيدك النقدي لا يكفي أو المبلغ غير صالح!", ephemeral=True)
            
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -val, "bank": val}})
            await interaction.response.send_message(f"✅ تم تأمين وتخزين `{val:,}` 🪙 في خزينة البنك السيادية بنجاح!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class BankWithdrawModal(discord.ui.Modal, title="سحب أموال من خزينة البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد سحبه للمحفظة", placeholder="مثال: 50000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value)
            user_id = str(interaction.user.id)
            user_data = users_col.find_one({"user_id": user_id})
            bank = user_data.get("bank", 0)
            if bank < val or val <= 0:
                return await interaction.response.send_message("❌ لا يملك البنك هذا المبلغ في رصيدك أو القيمة غير صالحة!", ephemeral=True)
            
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": val, "bank": -val}})
            await interaction.response.send_message(f"✅ تم سحب `{val:,}` 🪙 وإضافتها إلى محفظتك الخاصة!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class BankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="عرض الحساب المالي الشامل", description="الاطلاع على رصيد المحفظة والخزينة السيادية", emoji="💼", value="view"),
            discord.SelectOption(label="إيداع نقدي في البنك", description="نقل الأموال من المحفظة إلى الخزينة الآمنة", emoji="📥", value="deposit"),
            discord.SelectOption(label="سحب نقدي من البنك", description="استخراج السيولة المالية وإنفاقها بالمعارك", emoji="📤", value="withdraw")
        ]
        super().__init__(placeholder="🌟 اختر المعاملة المصرفية المطلوبة من القائمة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.response.send_message("❌ أنت غير مسجل! استخدم `/تسجيل` أولاً.", ephemeral=True)
        
        wallet = user_data.get("balance", 0)
        bank = user_data.get("bank", 0)
        
        if self.values[0] == "view":
            embed = discord.Embed(
                title=f"🏛️ البنك المركزي الإمبراطوري - {interaction.user.display_name}",
                description="«حيث تُحفظ ثروات الأبطال وتصان مقدرات العوالم الكبرى من السرقة والتلف.»\n\n"
                            f"💵 **السيولة النقدية (المحفظة):** `{wallet:,}` 🪙\n"
                            f"🔐 **الودائع الملكية (البنك):** `{bank:,}` 🪙\n"
                            f"👑 **إجمالي الثروة الكلية:** `{wallet + bank:,}` 🪙",
                color=discord.Color.dark_gold()
            )
            embed.set_footer(text="النظام المصرفي الآمن - مؤمن ضد هجمات الوحوش والأعداء")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "deposit":
            await interaction.response.send_modal(BankDepositModal())
        elif self.values[0] == "withdraw":
            await interaction.response.send_modal(BankWithdrawModal())

class BankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(BankSelect())

@bot.tree.command(name="البنك", description="فتح البوابة المصرفية الإمبراطورية لإدارة ثروتك")
async def bank_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ القاعة المركزية للبنك الإمبراطوري ✨",
        description="مرحباً بك في أقدم وأعظم مؤسسة مالية في الأبعاد. استخدم القائمة المنسدلة أدناه للتحكم بأموالك:",
        color=discord.Color.from_rgb(218, 165, 32)
    )
    await interaction.response.send_message(embed=embed, view=BankView(), ephemeral=True)


# ================== لوحة المطور الفخمة والأوامر الخارقة ==================

class GiftGearModal(discord.ui.Modal, title="إهداء عتاد أسطوري (بالمنشن)"):
    target = discord.ui.TextInput(label="منشن العضو أو الآيدي الخاص به", placeholder="@User أو 123456789", required=True)
    gear_name = discord.ui.TextInput(label="اسم سلاح أو عتاد الأسطورة", placeholder="مثال: سيف التنين الخالد", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = extract_user_id(self.target.value)
            item = self.gear_name.value.strip()
            users_col.update_one({"user_id": uid}, {"$push": {"inventory": item}}, upsert=True)
            await interaction.response.send_message(f"🎁 **تم إرسال العتاد بنجاح!** حصل المستخدم `<@{uid}>` على القطعة: `{item}` ⚔️", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"❌ حدث خطأ في الآيدي أو المنشن: {e}", ephemeral=True)

class AddBalanceModal(discord.ui.Modal, title="إضافة رصيد عملات"):
    target = discord.ui.TextInput(label="آيدي المستخدم أو المنشن", placeholder="مثال: 123456789", required=True)
    amount = discord.ui.TextInput(label="المبلغ المضاف", placeholder="مثال: 50000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = extract_user_id(self.target.value)
            val = int(self.amount.value)
            users_col.update_one({"user_id": uid}, {"$inc": {"balance": val}}, upsert=True)
            await interaction.response.send_message(f"✅ تم إضافة `{val:,}` 🪙 للمستخدم بنجاح!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

class AddDevModal(discord.ui.Modal, title="إضافة مطور جديد"):
    target = discord.ui.TextInput(label="آيدي المستخدم الجديد للمطورين", placeholder="أدخل الآيدي...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.target.value.strip()
        devs_col.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
        await interaction.response.send_message(f"✅ تم منح صلاحيات المطور للعضو: `{uid}`", ephemeral=True)

class DevSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="تفعيل شخصية 'السفاح' المطلقة", description="رفع إحصائياتك وقوتك للحد الأقصى المدمر", emoji="🩸", value="assassin"),
            discord.SelectOption(label="الحصول على الثروات اللاانهائية", description="ضخ بلاهايد من العملات العادية والنادرة لمحفظتك", emoji="💎", value="wealth"),
            discord.SelectOption(label="تطوير العتاد والمعدلات لأقصى حد (بضغطة زر)", description="رفع كافة معدلاتك القتالية والعتاد للقمة المطلقة بلا حدود", emoji="⚡", value="max_gear"),
            discord.SelectOption(label="إهداء عتاد لعضو (بالمنشن)", description="منح أي لاعب قطعة عتاد فريدة باستخدام المنشن", emoji="🎁", value="gift_gear"),
            discord.SelectOption(label="إضافة رصيد عملات لعضو", description="حقن أرصدة مالية لـ حساب أي مستخدم", emoji="🪙", value="add_bal"),
            discord.SelectOption(label="إضافة مطور جديد للنظام", description="ترقية شخص جديد لرتبة مطور إمبراطوري", emoji="🛠️", value="add_dev")
        ]
        super().__init__(placeholder="⚡ اختر صلاحية المطور المطلقة للتنفيذ...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        choice = self.values[0]
        
        if choice == "assassin":
            assassin = HEROES_DATA["assassin_dev"]
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "selected_hero": assassin['name'],
                        "power": assassin['stats']['power'],
                        "max_floor": assassin['stats']['max_floor'],
                        "kills": assassin['stats']['kills'],
                        "custom_title": "💀 حاكم الأبعاد ومالك السفاح"
                    }
                },
                upsert=True
            )
            await interaction.response.send_message("🩸 **تم تفعيل طاقة السفاح المطلقة وإحصائياتك المرعبة بنجاح!**", ephemeral=True)
            
        elif choice == "wealth":
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": 999999999, "diamonds": 999999999}},
                upsert=True
            )
            await interaction.response.send_message("💎 **تم ضخ الثروات اللانهائية!** حصلت على عملات عادية ونادرة بلا حدود في خزنتك.", ephemeral=True)
            
        elif choice == "max_gear":
            # تطوير المعدلات الـ 8 بلا حدود للأبد (تصل لمليارات القيم)
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "aim": 999999999999,       # التصويب
                        "evasion": 999999999999,   # المراوغة
                        "attack": 999999999999,    # الهجوم
                        "accuracy": 999999999999,  # الدقة
                        "defense": 999999999999,   # الدفاع
                        "critical": 999999999999,  # القاتلة
                        "magic": 999999999999,     # السحر
                        "intelligence": 999999999999 # الذكاء
                    }
                },
                upsert=True
            )
            await interaction.response.send_message("⚡ **تمت ترقية كافة المعدلات والعتاد للأقصى المطلق (بلا حدود للأرقام والمليارات)!**", ephemeral=True)
            
        elif choice == "gift_gear":
            await interaction.response.send_modal(GiftGearModal())
        elif choice == "add_bal":
            await interaction.response.send_modal(AddBalanceModal())
        elif choice == "add_dev":
            await interaction.response.send_modal(AddDevModal())

class DevControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(DevSelect())

@bot.tree.command(name="المطور", description="لوحة التحكم الفخمة الخاصة بالمطورين والصلاحيات المطلقة")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة السيطرة والتحكم العليا للمطورين",
        description="أهلاً بك أيها الحاكم المطلق. استخدم القائمة المنسدلة أدناه لتنفيذ الأوامر الخارقة وإدارة العوالم:",
        color=discord.Color.dark_embed()
    )
    await interaction.response.send_message(embed=embed, view=DevControlView(), ephemeral=True)


# ================== أمر الملف الشخصي الشامل مع المعدلات الـ 8 ==================
@bot.tree.command(name="الملف", description="عرض السجل الأسطوري والمعدلات القتالية الشاملة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    selected_hero = user_data.get("selected_hero", "لم يتم اختيار بطل بعد")
    power = user_data.get("power", 100)
    kills = user_data.get("kills", 0)
    
    # المعدلات الـ 8 (بدون مستوى أقصى، تدعم المليارات)
    aim = user_data.get("aim", 10)
    evasion = user_data.get("evasion", 10)
    attack = user_data.get("attack", 10)
    accuracy = user_data.get("accuracy", 10)
    defense = user_data.get("defense", 10)
    critical = user_data.get("critical", 10)
    magic = user_data.get("magic", 10)
    intelligence = user_data.get("intelligence", 10)
    
    embed_color = discord.Color.dark_red() if "السفاح" in selected_hero else discord.Color.gold()
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=embed_color
    )
    embed.add_field(name="👑 اللقب الحالي", value=custom_title, inline=True)
    embed.add_field(name="🦸‍♂️ البطل المختار", value=selected_hero, inline=True)
    embed.add_field(name="⚡ طاقة القتال", value=f"{power:,}", inline=True)
    
    # عرض المعدلات القتالية الـ 8 الفخمة
    stats_text = (
        f"🎯 **التصويب:** `{aim:,}` | 💨 **المراوغة:** `{evasion:,}`\n"
        f"🗡️ **الهجوم:** `{attack:,}` | 👁️ **الدقة:** `{accuracy:,}`\n"
        f"🛡️ **الدفاع:** `{defense:,}` | 💥 **القاتلة:** `{critical:,}`\n"
        f"🔮 **السحر:** `{magic:,}` | 🧠 **الذكاء:** `{intelligence:,}`"
    )
    embed.add_field(name="📊 ترسانة المعدلات القتالية المطلقة", value=stats_text, inline=False)
    
    embed.add_field(name="🏢 أعلى طابق متجاوز", value=str(max_floor), inline=True)
    embed.add_field(name="💀 الخصوم المقضي عليهم", value=str(kills), inline=True)
    embed.add_field(name="💰 المحفظة والبنك", value=f"{balance:,} 🪙 | 💳 {bank:,} 🪙", inline=False)
    embed.add_field(name="💎 الألماس والنقاد", value=f"{diamonds:,} 💎", inline=True)
    
    if "السفاح" in selected_hero:
        embed.add_field(
            name="🩸 حالة الكيان المرعب",
            value="*«كيان مدمر يطمس الأبعاد ولا يرحم أحداً... طاقته تفوق مقاييس الكون.»*",
            inline=False
        )

    embed.set_footer(text=f"معرف المستخدم: {user_id}", icon_url=interaction.user.display_avatar.url)
    await interaction.followup.send(embed=embed, ephemeral=False)

@bot.tree.command(name="تسجيل", description="التسجيل في نظام اللعبة والحصول على لقب المبتدئ")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    if existing_user:
        return await interaction.response.send_message("❌ أنت مسجل بالفعل في قاعدة البيانات!", ephemeral=True)
    
    new_user = {
        "user_id": user_id,
        "balance": 1000,
        "bank": 0,
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "battles_played": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "unlocked_titles": ["المبتدئ"],
        "selected_hero": "لم يتم اختيار بطل بعد",
        "inventory": [],
        # تعيين القيم الأولية للمعدلات الـ 8
        "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
        "defense": 10, "critical": 10, "magic": 10, "intelligence": 10
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

bot.run(DISCORD_TOKEN)
