import os
import random
import re
import asyncio
import discord
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# ==========================================
# إعداد البوت
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "❌ متغير MONGO_URI غير موجود في Railway Environment Variables."
    )

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]
config_col = db["config"]  # مجموعة خاصة لحفظ إعدادات المطورين

# ضع هنا الآيدي الأساسي الخاص بك (المطور الأساسي الذي لا يمكن حذفه أبداً)
OWNER_ID = "YOUR_DISCORD_USER_ID_HERE" # <--- استبدل هذا الرقم بآيدي حسابك في ديسكورد

# ==========================================
# توليد 500 قطعة عتاد لكل فئة ديناميكياً
# ==========================================
CATEGORIES = ["خناجر", "سيوف", "مطرقات", "خوذ", "دروع", "ساق", "حذاء"]

def generate_shop_items(shop_type):
    items_dict = {}
    prefixes = [
        "ظلال", "صاعقة", "لهب", "دمار", "ملعون", "مبارك",
        "أبدي", "فاني", "جلمود", "برق", "سحيق", "أساطير",
        "ملوكي", "عاصف", "حارق"
    ]
    suffixes = [
        "الردى", "الخلود", "الفناء", "الجهنم", "الظلام", "النور",
        "الشفق", "الجبابرة", "الأسسياد", "التنين", "الموت",
        "السيوف", "الدم", "الفرسان", "العرش"
    ]

    for cat in CATEGORIES:
        cat_items = []

        for i in range(1, 501):
            p = random.choice(prefixes)
            s = random.choice(suffixes)
            name = f"{cat} {p} {s} #{i}"

            if shop_type == "dark":
                if i > 480:
                    tier = "الشيطان"
                elif i > 440:
                    tier = "الجحيم"
                elif i > 380:
                    tier = "السفاح"
                elif i > 250:
                    tier = "أسطوري"
                elif i > 150:
                    tier = "ملحمي"
                elif i > 50:
                    tier = "نادر"
                else:
                    tier = "شائع"

                power = i * 3 + random.randint(15, 60)
                price = i * 4 + random.randint(10, 50)
            else:
                if i > 450:
                    tier = "مقدس"
                elif i > 350:
                    tier = "فريد"
                elif i > 250:
                    tier = "أسطوري"
                elif i > 150:
                    tier = "ملحمي"
                elif i > 50:
                    tier = "نادر"
                else:
                    tier = "شائع"

                power = i * 2 + random.randint(5, 30)
                price = i * 15 + random.randint(50, 200)

            cat_items.append({
                "id": f"{shop_type[0]}_{cat}_{i}",
                "name": name,
                "tier": tier,
                "power": power,
                "price": price
            })

        items_dict[cat] = cat_items

    return items_dict

NORMAL_SHOP_ITEMS = generate_shop_items("normal")
DARK_SHOP_ITEMS = generate_shop_items("dark")

# دمج كل العناصر لتسهيل البحث عليها من قبل المطور
ALL_ITEMS_FLAT = []
for cat, items in NORMAL_SHOP_ITEMS.items():
    ALL_ITEMS_FLAT.extend(items)
for cat, items in DARK_SHOP_ITEMS.items():
    ALL_ITEMS_FLAT.extend(items)

# ==========================================
# وظائف التحقق المساعدة
# ==========================================
def is_registered(user_id: str) -> bool:
    user = users_col.find_one({"user_id": user_id})
    return bool(user and user.get("registered", False))

def is_developer(user_id: str) -> bool:
    if str(user_id) == str(OWNER_ID):
        return True
    
    config = config_col.find_one({"type": "developers"})
    if config and str(user_id) in config.get("devs", []):
        return True
    return False

# ==========================================
# نافذة التسجيل (Modal)
# ==========================================
class RegisterModal(Modal, title="تسجيل بيانات المستخدم الجديد"):
    name_input = TextInput(label="الاسم", placeholder="أدخل اسمك الحقيقي أو المستعار", style=discord.TextStyle.short, required=True)
    age_input = TextInput(label="العمر", placeholder="أدخل عمرك بالأرقام (مثال: 20)", style=discord.TextStyle.short, required=True)
    gender_input = TextInput(label="الجنس", placeholder="ذكر / أنثى", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        name = self.name_input.value.strip()
        raw_age = self.age_input.value.strip()
        gender = self.gender_input.value.strip()

        try:
            age = int(raw_age)
            if age <= 0 or age > 120:
                raise ValueError()
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال عمر صحيح وبمنطقية.", ephemeral=True)

        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {"registered": True, "name": name, "age": age, "gender": gender},
                "$setOnInsert": {"balance": 1000, "inventory": []}
            },
            upsert=True
        )

        await interaction.response.send_message(
            f"✅ **تم تسجيلك بنجاح تام!**\n👤 **الاسم:** {name}\n🎂 **العمر:** {age}\n⚧ **الجنس:** {gender}\n\nيمكنك الآن استخدام أوامر البوت.",
            ephemeral=True
        )

# ==========================================
# نوافذ وأوامر لوحة المطورين
# ==========================================

# 1. نافذة إضافة أو حذف مطور
class DevManageModal(Modal, title="إدارة المطورين"):
    target_input = TextInput(label="منشن الشخص أو آيدي المستخدم (ID)", placeholder="مثال: @user أو 123456789", style=discord.TextStyle.short, required=True)

    def __init__(self, action_type: str):
        super().__init__()
        self.action_type = action_type
        if action_type == "add":
            self.title = "إضافة مطور جديد"
        else:
            self.title = "إزالة مطور"

    async def on_submit(self, interaction: discord.Interaction):
        raw_target = self.target_input.value.strip()
        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ لم يتم التعرف على المستخدم بشكل صحيح.", ephemeral=True)
        
        target_id = match_id.group()

        if target_id == str(OWNER_ID) and self.action_type == "remove":
            return await interaction.response.send_message("❌ لا يمكنك إزالة المطور الأساسي للبوت!", ephemeral=True)

        config_col.update_one(
            {"type": "developers"},
            {"$setOnInsert": {"devs": []}},
            upsert=True
        )

        if self.action_type == "add":
            config_col.update_one({"type": "developers"}, {"$addToSet": {"devs": target_id}})
            await interaction.response.send_message(f"✅ تم إضافة العضو <@{target_id}> إلى قائمة المطورين بنجاح.", ephemeral=True)
        else:
            config_col.update_one({"type": "developers"}, {"$pull": {"devs": target_id}})
            await interaction.response.send_message(f"✅ تم إزالة العضو <@{target_id}> من قائمة المطورين.", ephemeral=True)

# 2. نافذة إضافة عملات غير محدودة
class DevAddCoinsModal(Modal, title="توليد عملات للمطور أو العضو"):
    target_input = TextInput(label="المنشن أو الآيدي (اتركه فارغاً لنفسك)", placeholder="اختياري: @user أو ID", style=discord.TextStyle.short, required=False)
    amount_input = TextInput(label="المبلغ المراد إضافته", placeholder="مثال: 999999999", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        raw_target = self.target_input.value.strip()
        raw_amount = self.amount_input.value.strip()

        try:
            amount = int(raw_amount)
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال رقم صحيح للمبلغ.", ephemeral=True)

        if raw_target:
            match_id = re.search(r'\d+', raw_target)
            if not match_id:
                return await interaction.response.send_message("❌ الآيدي المستهدف غير صحيح.", ephemeral=True)
            target_id = match_id.group()
        else:
            target_id = str(interaction.user.id)

        users_col.update_one(
            {"user_id": target_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )

        await interaction.response.send_message(
            f"⚡ **[لوحة المطور]:** تم إضافة مبلغ `{amount:,}` عملة إلى رصيد <@{target_id}> بنجاح!",
            ephemeral=True
        )

# 3. قائمة اختيار العتاد (منيو ديناميكي لكل الفئات والأنواع المتاحة)
class DevItemSelect(Select):
    def __init__(self, target_id: str):
        self.target_id = target_id
        # نأخذ عينة ديناميكية متجددة أو أول 25 عنصر كنموذج، ويمكن جعلها شاملة عبر الفئات
        options = []
        # عرض عينة ممثلة من الأنواع والدرجات المختلفة الموجودة تلقائياً
        sample_items = random.sample(ALL_ITEMS_FLAT, min(25, len(ALL_ITEMS_FLAT)))
        
        for item in sample_items:
            options.append(
                discord.SelectOption(
                    label=item["name"][:99],
                    description=f"الفئة: {item['tier']} | القوة: {item['power']}",
                    value=item["id"],
                    emoji="⚔️"
                )
            )
        super().__init__(placeholder="🛠️ اختر قطعة العتاد لإضافتها للحساب...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        selected_item = next((item for item in ALL_ITEMS_FLAT if item["id"] == item_id), None)

        if not selected_item:
            return await interaction.response.send_message("❌ العتاد غير موجود.", ephemeral=True)

        users_col.update_one(
            {"user_id": self.target_id},
            {"$push": {"inventory": selected_item}},
            upsert=True
        )

        await interaction.response.send_message(
            f"🛡️ **[لوحة المطور]:** تم منح العتاد **({selected_item['name']})** إلى المستخدم <@{self.target_id}> بنجاح!",
            ephemeral=True
        )

class DevItemView(View):
    def __init__(self, target_id: str):
        super().__init__(timeout=180)
        self.add_item(DevItemSelect(target_id))

# 4. نافذة اختيار الشخص للعتاد
class DevItemModal(Modal, title="منح عتاد لمستخدم"):
    target_input = TextInput(label="منشن الشخص أو الآيدي المستهدف", placeholder="مثال: @user أو ID", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        raw_target = self.target_input.value.strip()
        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ الآيدي غير صحيح.", ephemeral=True)
        
        target_id = match_id.group()
        await interaction.response.send_message(
            f"📦 اختر قطعة العتاد المطلوبة لإضافتها إلى حقيبة <@{target_id}> من القائمة أدناه:",
            view=DevItemView(target_id),
            ephemeral=True
        )

# واجهة لوحة المطور الرئيسية
class DevPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="توليد عملات لانهائية", style=discord.ButtonStyle.success, emoji="💰", custom_id="dev_coins_btn")
    async def dev_coins(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DevAddCoinsModal())

    @discord.ui.button(label="منح عتاد للمستخدِمين", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="dev_item_btn")
    async def dev_items(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DevItemModal())

    @discord.ui.button(label="إضافة مطور جديد", style=discord.ButtonStyle.secondary, emoji="➕", custom_id="dev_add_btn")
    async def dev_add(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(OWNER_ID):
            return await interaction.response.send_message("❌ هذا الزر مخصص للمطور الأساسي فقط!", ephemeral=True)
        await interaction.response.send_modal(DevManageModal("add"))

    @discord.ui.button(label="إزالة مطور", style=discord.ButtonStyle.danger, emoji="➖", custom_id="dev_remove_btn")
    async def dev_remove(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(OWNER_ID):
            return await interaction.response.send_message("❌ هذا الزر مخصص للمطور الأساسي فقط!", ephemeral=True)
        await interaction.response.send_modal(DevManageModal("remove"))

# ==========================================
# أمر لوحة المطورين (Slash Command)
# ==========================================
@bot.tree.command(name="لوحة_المطور", description="اللوحة السرية الخاصة بالمطورين للتحكم الكامل باللعبة")
async def dev_panel(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_developer(user_id):
        return await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص للمطورين المعتمدين فقط!", ephemeral=True)

    embed = discord.Embed(
        title="⚙️ | لوحة تحكم المطورين الملكية",
        description=(
            "مرحباً بك في لوحة السيطرة الخاصة بالمطورين.\n"
            "من هنا يمكنك إدارة الاقتصاد، منح الثروات، توزيع العتاد، وإدارة فريق المطورين الفرعيين.\n\n"
            "✨ **الخيارات المتاحة:**\n"
            "• `💰` **توليد عملات:** ضخ أموال لا نهائية لك أو لأي لاعب.\n"
            "• `⚔️` **منح عتاد:** تصفح كل أنواع العتاد وإرساله لمن تريد.\n"
            "• `➕` **إضافة مطور:** تفويض صديقك ليكون مطوراً معك (للمالك الأساسي).\n"
            "• `➖` **إزالة مطور:** سحب صلاحيات المطورين الفرعيين."
        ),
        color=0x2F3136
    )
    embed.set_footer(text=f"مطور معتمد: {interaction.user}", icon_url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed, view=DevPanelView(), ephemeral=True)

# ==========================================
# نافذة تحويل العملات وبقية الأوامر السابقة
# ==========================================
class TransferModal(Modal, title="تحويل العملات الفوري"):
    target_input = TextInput(label="منشن الشخص أو آيدي المستخدم (ID)", placeholder="مثال: @user أو 123456789012345678", style=discord.TextStyle.short, required=True)
    amount_input = TextInput(label="المبلغ المراد تحويله", placeholder="أدخل الرقم فقط (مثال: 500)", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sender_id = str(interaction.user.id)
        raw_target = self.target_input.value.strip()
        raw_amount = self.amount_input.value.strip()

        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ لم يتم التعرف على المستخدم المستهدف بشكل صحيح.", ephemeral=True)
        
        target_id = match_id.group()
        if target_id == sender_id:
            return await interaction.response.send_message("❌ لا يمكنك تحويل الأموال لنفسك!", ephemeral=True)

        try:
            amount = int(raw_amount)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال مبلغ صحيح وموجب.", ephemeral=True)

        sender_data = users_col.find_one({"user_id": sender_id})
        sender_balance = sender_data.get("balance", 0) if sender_data else 0

        if sender_balance < amount:
            return await interaction.response.send_message(f"❌ رصيدك غير كافٍ! رصيدك الحالي هو: `{sender_balance}` عملة.", ephemeral=True)

        users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount}}, upsert=True)
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount}}, upsert=True)

        await interaction.response.send_message(
            f"✅ **تمت عملية التحويل بنجاح!**\n💸 تم إرسال مبلغ ` {amount} ` عملة إلى <@{target_id}>.",
            ephemeral=True
        )

class BankSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الراتب اليومي", description="استلام مكافأتك المالية اليومية بانتظام.", value="bank_daily", emoji="💰"),
            discord.SelectOption(label="نظام القروض والمعدات", description="طلب قرض ورهن/بيع المعدات تلقائياً عند انتهاء المهلة.", value="bank_loans", emoji="📜"),
            discord.SelectOption(label="تحويل العملات", description="إرسال الأموال فورياً لأي عضو في السيرفر عبر المنشن.", value="bank_transfer", emoji="💸")
        ]
        super().__init__(placeholder="✨ اختر الخدمة المصرفية المطلوبة من هنا...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if not is_registered(user_id):
            return await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام الأمر `/تسجيل` لتتمكن من استخدام الخدمات المصرفية.", ephemeral=True)

        choice = self.values[0]
        if choice == "bank_daily":
            user_data = users_col.find_one({"user_id": user_id})
            now = datetime.now(timezone.utc)
            last_claim = user_data.get("last_daily") if user_data else None
            
            if last_claim and now - last_claim < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_claim)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes = remainder // 60
                return await interaction.response.send_message(
                    f"⏳ لقد استلمت راتبك اليومي مسبقاً! يمكنك الاستلام مرة أخرى بعد `{hours} ساعة و {minutes} دقيقة`.",
                    ephemeral=True
                )

            daily_amount = 5000
            users_col.update_one({"user_id": user_id}, {"$set": {"last_daily": now}, "$inc": {"balance": daily_amount}}, upsert=True)
            return await interaction.response.send_message(f"🎉 **مبروك!** تم إيداع الراتب اليومي بقيمة `{daily_amount}` عملة في حسابك بنجاح.", ephemeral=True)
        
        elif choice == "bank_loans":
            embed = discord.Embed(
                title="📜 | قسم القروض وضمان المعدات",
                description="نظام القروض لدينا صارم لضمان حقوق الجميع:\n\n⚠️ **شروط القرض:**\n1. مدة السداد 3 أيام.\n2. في حال انتهاء المهلة ولم تسدد، **سيقوم النظام تلقائياً ببيع معداتك** لسداد الدان!\n\nاضغط بالأسفل لتقديم طلب.",
                color=0x8B0000
            )
            class LoanView(View):
                def __init__(self):
                    super().__init__(timeout=180)
                @discord.ui.button(label="تقديم طلب قرض", style=discord.ButtonStyle.danger, emoji="⚖️", custom_id="req_loan")
                async def req_loan(self, interaction: discord.Interaction, button: Button):
                    loan_due = datetime.now(timezone.utc) + timedelta(days=3)
                    users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"loan_due": loan_due}, "$inc": {"balance": 20000}}, upsert=True)
                    await interaction.response.send_message("📝 **تم قبول طلب القرض!** تمت إضافة 20,000 عملة لحسابك.", ephemeral=True)
            return await interaction.response.send_message(embed=embed, view=LoanView(), ephemeral=True)
        
        elif choice == "bank_transfer":
            return await interaction.response.send_modal(TransferModal())

class BankView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BankSelect())

@bot.tree.command(name="تسجيل", description="تسجيل بياناتك الشخصية (الاسم، العمر، الجنس)")
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if is_registered(user_id):
        user_data = users_col.find_one({"user_id": user_id})
        return await interaction.response.send_message(
            f"ℹ️ أنت مسجل مسبقاً:\n👤 **الاسم:** {user_data.get('name')}\n🎂 **العمر:** {user_data.get('age')}\n⚧ **الجنس:** {user_data.get('gender')}",
            ephemeral=True
        )
    await interaction.response.send_modal(RegisterModal())

@bot.tree.command(name="البنك", description="النظام المصرفي الفاخر لإدارة الأموال، القروض، والتحويلات")
async def bank(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_registered(user_id):
        return await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام الأمر `/تسجيل` لفتح حساب بنكي.", ephemeral=True)

    bank_embed = discord.Embed(
        title="🏛️ | البنك المركزي الملكي - Royal Bank",
        description="مرحباً بك في النظام المصرفي الأكثر تطوراً.\n\n✨ **الخدمات المتاحة:**\n• `💰` **الراتب اليومي**\n• `📜` **نظام القروض**\n• `💸` **تحويل العملات الفوري**",
        color=0xD4AF37
    )
    bank_embed.set_thumbnail(url="https://i.imgur.com/3Z66v7q.png")
    bank_embed.set_footer(text=f"طلب بواسطة: {interaction.user}", icon_url=interaction.user.display_avatar.url)
    bank_embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=bank_embed, view=BankView(), ephemeral=False)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ متغير DISCORD_TOKEN غير موجود في البيئة.")
