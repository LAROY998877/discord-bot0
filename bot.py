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
config_col = db["config"]

# ضع هنا الآيدي الأساسي الخاص بك
OWNER_ID = "YOUR_DISCORD_USER_ID_HERE" # <--- استبدل هذا الرقم بآيدي حسابك

# ==========================================
# توليد 500 قطعة عتاد لكل فئة (8 فئات شاملة عصا سحرية)
# ==========================================
CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]

def generate_shop_items(shop_type):
    items_dict = {}
    prefixes = [
        "ظلال", "صاعقة", "لهب", "دمار", "ملعون", "مبارك",
        "أبدي", "فاني", "جلمود", "برق", "سحيق", "أساطير",
        "ملوكي", "عاصف", "حارق", "دبوي", "مرعب", "خفي"
    ]
    suffixes = [
        "الردى", "الخلود", "الفناء", "الجهنم", "الظلام", "النور",
        "الشفق", "الجبابرة", "الاسياد", "التنين", "الموت",
        "السيوف", "الدم", "الفرسان", "العرش", "الهلاك"
    ]

    for cat in CATEGORIES:
        cat_items = []

        for i in range(1, 501):
            p = random.choice(prefixes)
            s = random.choice(suffixes)
            name = f"{cat} {p} {s} #{i}"

            if shop_type == "dark":
                # المتجر المظلم: رتب قوية وملعونة تشمل الشيطان، الجحيم، السفاح كأعلى رتب
                if i > 480:
                    tier = "الشيطان"
                elif i > 430:
                    tier = "الجحيم"
                elif i > 360:
                    tier = "السفاح"
                elif i > 250:
                    tier = "ملعون أسطوري"
                elif i > 150:
                    tier = "ظلام دامس"
                elif i > 50:
                    tier = "مظلم نادر"
                else:
                    tier = "ضعيف مشؤوم"

                power = i * 4 + random.randint(20, 80)
                price = i * 5 + random.randint(15, 60) # سعر بالعملة النادرة
            else:
                # المتجر العادي: رتب عادية ومتدرجة
                if i > 450:
                    tier = "مقدس فريد"
                elif i > 350:
                    tier = "أسطوري"
                elif i > 250:
                    tier = "ملحمي"
                elif i > 150:
                    tier = "نادر متقدم"
                elif i > 50:
                    tier = "نادر"
                else:
                    tier = "شائع"

                power = i * 2 + random.randint(5, 25)
                price = i * 20 + random.randint(100, 500) # سعر بالعملة العادية

            cat_items.append({
                "id": f"{shop_type[0]}_{cat}_{i}",
                "name": name,
                "tier": tier,
                "power": power,
                "price": price,
                "type": shop_type
            })

        items_dict[cat] = cat_items

    return items_dict

NORMAL_SHOP_ITEMS = generate_shop_items("normal")
DARK_SHOP_ITEMS = generate_shop_items("dark")

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
                "$setOnInsert": {"balance": 5000, "diamonds": 10, "inventory": []}
            },
            upsert=True
        )

        await interaction.response.send_message(
            f"✅ **تم تسجيلك بنجاح تام!**\n👤 **الاسم:** {name}\n🎂 **العمر:** {age}\n⚧ **الجنس:** {gender}\n🎁 **هدية التسجيل:** 10 ألماس نادر و 5,000 عملة عادية.",
            ephemeral=True
        )

# ==========================================
# المتجر العادي والمتجر المظلم (قوائم الشراء)
# ==========================================
class ShopCategorySelect(Select):
    def __init__(self, shop_type: str):
        self.shop_type = shop_type
        options = []
        for cat in CATEGORIES:
            emoji = "⚔️" if "سيف" in cat or "خنجر" in cat else ("🛡️" in cat or "درع" in cat or "خوذة" in cat or "بنطال" in cat or "حذاء" in cat or "مطرقة" in cat or "عصا" in cat)
            options.append(
                discord.SelectOption(
                    label=f"فئة {cat}",
                    description=f"تصفح 500 قطعة عتاد ضمن فئة {cat}",
                    value=cat,
                    emoji="🛡️"
                )
            )
        super().__init__(placeholder="📂 اختر فئة العتاد التي تريد تصفحها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        items_pool = NORMAL_SHOP_ITEMS[cat] if self.shop_type == "normal" else DARK_SHOP_ITEMS[cat]
        
        # نعرض أول 25 قطعة كعينة اختيار سريعة لتجنب تجاوز حدود ديسكورد للقوائم
        sample_items = random.sample(items_pool, min(25, len(items_pool)))
        
        class SpecificItemSelect(Select):
            def __init__(self):
                sub_options = []
                for item in sample_items:
                    curr_name = "عملة" if self.shop_type == "normal" else "ألماس"
                    sub_options.append(
                        discord.SelectOption(
                            label=item["name"][:99],
                            description=f"الرتبة: {item['tier']} | القوة: {item['power']} | السعر: {item['price']} {curr_name}",
                            value=item["id"],
                            emoji="✨"
                        )
                    )
                super().__init__(placeholder=f"🛒 اختر قطعة من فئة ({cat}) للشراء...", min_values=1, max_values=1, options=sub_options)

            async def callback(self, sub_interaction: discord.Interaction):
                item_id = self.values[0]
                item = next((it for it in items_pool if it["id"] == item_id), None)
                if not item:
                    return await sub_interaction.response.send_message("❌ القطعة غير متوفرة.", ephemeral=True)

                user_id = str(sub_interaction.user.id)
                user_data = users_col.find_one({"user_id": user_id}) or {}

                if self.shop_type == "normal":
                    curr_balance = user_data.get("balance", 0)
                    if curr_balance < item["price"]:
                        return await sub_interaction.response.send_message(f"❌ رصيدك العادي غير كافٍ! تحتاج إلى `{item['price']}` عملة عادية.", ephemeral=True)
                    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}})
                else:
                    curr_diamonds = user_data.get("diamonds", 0)
                    if curr_diamonds < item["price"]:
                        return await sub_interaction.response.send_message(f"❌ رصيدك من الألماس النادر غير كافٍ! تحتاج إلى `💎 {item['price']}`.", ephemeral=True)
                    users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}})

                await sub_interaction.response.send_message(
                    f"🎉 **مبروك!** اشتريت بنجاح:\n⚔️ **القطعة:** {item['name']}\n🏷️ **الرتبة:** {item['tier']}\n💪 **القوة:** {item['power']}\nتمت إضافتها إلى حقيبتك الخاصة!",
                    ephemeral=True
                )

        class SpecificItemView(View):
            def __init__(self):
                super().__init__(timeout=180)
                self.add_item(SpecificItemSelect())

        await interaction.response.send_message(
            f"📦 إليك عينة من أروع قطع **{cat}** المتاحة في المتجر ({'العادي' if self.shop_type=='normal' else 'المظلم'}):",
            view=SpecificItemView(),
            ephemeral=True
        )

class ShopView(View):
    def __init__(self, shop_type: str):
        super().__init__(timeout=180)
        self.add_item(ShopCategorySelect(shop_type))

# ==========================================
# لوحة المطورين وأوامرها
# ==========================================
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

        config_col.update_one({"type": "developers"}, {"$setOnInsert": {"devs": []}}, upsert=True)

        if self.action_type == "add":
            config_col.update_one({"type": "developers"}, {"$addToSet": {"devs": target_id}})
            await interaction.response.send_message(f"✅ تم إضافة العضو <@{target_id}> إلى قائمة المطورين بنجاح.", ephemeral=True)
        else:
            config_col.update_one({"type": "developers"}, {"$pull": {"devs": target_id}})
            await interaction.response.send_message(f"✅ تم إزالة العضو <@{target_id}> من قائمة المطورين.", ephemeral=True)

class DevAddCurrencyModal(Modal, title="توليد العملات والألماس النادر"):
    target_input = TextInput(label="المنشن أو الآيدي (اتركه فارغاً لنفسك)", placeholder="اختياري: @user أو ID", style=discord.TextStyle.short, required=False)
    coins_amount = TextInput(label="كمية العملات العادية", placeholder="مثال: 999999999", style=discord.TextStyle.short, required=True)
    diamonds_amount = TextInput(label="كمية الألماس النادر 💎", placeholder="مثال: 5000", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        raw_target = self.target_input.value.strip()
        raw_coins = self.coins_amount.value.strip()
        raw_diamonds = self.diamonds_amount.value.strip()

        try:
            coins = int(raw_coins)
            diamonds = int(raw_diamonds)
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال أرقام صحيحة.", ephemeral=True)

        target_id = re.search(r'\d+', raw_target).group() if raw_target else str(interaction.user.id)

        users_col.update_one(
            {"user_id": target_id},
            {"$inc": {"balance": coins, "diamonds": diamonds}},
            upsert=True
        )

        await interaction.response.send_message(
            f"⚡ **[لوحة المطور]:** تم إضافة `{coins:,}` عملة عادية و `💎 {diamonds:,}` ألماس نادر إلى حساب <@{target_id}> بنجاح!",
            ephemeral=True
        )

class DevItemSelect(Select):
    def __init__(self, target_id: str):
        self.target_id = target_id
        options = []
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

        users_col.update_one({"user_id": self.target_id}, {"$push": {"inventory": selected_item}}, upsert=True)
        await interaction.response.send_message(f"🛡️ **[لوحة المطور]:** تم منح العتاد **({selected_item['name']})** للمستخدم <@{self.target_id}> بنجاح!", ephemeral=True)

class DevItemView(View):
    def __init__(self, target_id: str):
        super().__init__(timeout=180)
        self.add_item(DevItemSelect(target_id))

class DevItemModal(Modal, title="منح عتاد لمستخدم"):
    target_input = TextInput(label="منشن الشخص أو الآيدي المستهدف", placeholder="مثال: @user أو ID", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        raw_target = self.target_input.value.strip()
        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ الآيدي غير صحيح.", ephemeral=True)
        target_id = match_id.group()
        await interaction.response.send_message(f"📦 اختر قطعة العتاد المطلوبة لحقيبة <@{target_id}>:", view=DevItemView(target_id), ephemeral=True)

class DevPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="توليد عملات وألماس", style=discord.ButtonStyle.success, emoji="💎", custom_id="dev_coins_btn")
    async def dev_coins(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DevAddCurrencyModal())

    @discord.ui.button(label="منح عتاد للمستخدمين", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="dev_item_btn")
    async def dev_items(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DevItemModal())

    @discord.ui.button(label="إضافة مطور", style=discord.ButtonStyle.secondary, emoji="➕", custom_id="dev_add_btn")
    async def dev_add(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(OWNER_ID):
            return await interaction.response.send_message("❌ للمالك الأساسي فقط!", ephemeral=True)
        await interaction.response.send_modal(DevManageModal("add"))

    @discord.ui.button(label="إزالة مطور", style=discord.ButtonStyle.danger, emoji="➖", custom_id="dev_remove_btn")
    async def dev_remove(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(OWNER_ID):
            return await interaction.response.send_message("❌ للمالك الأساسي فقط!", ephemeral=True)
        await interaction.response.send_modal(DevManageModal("remove"))

@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطورين الخاصة بالعملات، الألماس، والعتاد")
async def dev_panel(interaction: discord.Interaction):
    if not is_developer(str(interaction.user.id)):
        return await interaction.response.send_message("❌ عذراً، هذا الأمر للمطورين فقط!", ephemeral=True)

    embed = discord.Embed(
        title="⚙️ | لوحة تحكم المطورين الملكية",
        description="تحكم كامل بالعملات العادية، الألماس النادر، والعتاد الأسطوري.",
        color=0x2F3136
    )
    await interaction.response.send_message(embed=embed, view=DevPanelView(), ephemeral=True)

# ==========================================
# الأوامر العامة (المتاجر، البنك، الحقيبة)
# ==========================================
@bot.tree.command(name="المتجر", description="فتح المتجر العادي لشراء المعدات والأسلحة بالعملة العادية")
async def shop_normal(interaction: discord.Interaction):
    if not is_registered(str(interaction.user.id)):
        return await interaction.response.send_message("❌ سجّل أولاً باستخدام `/تسجيل` لفتح المتجر.", ephemeral=True)
    
    embed = discord.Embed(
        title="🛒 | المتجر العادي الملكي",
        description="تصفح فئات العتاد (خوذة، درع، بنطال، حذاء، سيف، مطرقة، خنجر، عصا سحرية). اختر الفئة المناسبة وتجهّز للمغامرة!",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed, view=ShopView("normal"), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="فتح المتجر المظلم للعتاد الأسطوري والملعون (برتب الشيطان، الجحيم، السفاح)")
async def shop_dark(interaction: discord.Interaction):
    if not is_registered(str(interaction.user.id)):
        return await interaction.response.send_message("❌ سجّل أولاً باستخدام `/تسجيل` لفتح المتجر المظلم.", ephemeral=True)
    
    embed = discord.Embed(
        title="🌑 | المتجر المظلم المحرم",
        description="أخطر متاجر العالم السفلي! يحتوي على عتاد برتب **الشيطان**، **الجحيم**، **السفاح** وأخرى ملعونة تُشترى بالـ `💎 الألماس النادر`.",
        color=0x4B0082
    )
    await interaction.response.send_message(embed=embed, view=ShopView("dark"), ephemeral=True)

@bot.tree.command(name="حقيبتي", description="عرض المعدات والأسلحة المخزنة في حقيبتك")
async def inventory(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not is_registered(user_id):
        return await interaction.response.send_message("❌ يجب عليك التسجيل أولاً.", ephemeral=True)

    user_data = users_col.find_one({"user_id": user_id}) or {}
    inv = user_data.get("inventory", [])

    if not inv:
        return await interaction.response.send_message("🎒 حقيبتك فارغة تماماً! توجه إلى `/المتجر` أو `/المتجر_المظلم` لاقتناء العتاد.", ephemeral=True)

    desc = "\n".join([f"• **{item['name']}** | الرتبة: `{item['tier']}` | القوة: `{item['power']}`" for item in inv[:25]])
    embed = discord.Embed(
        title=f"🎒 | حقيبة المعدات الخاصة بـ {interaction.user.name}",
        description=desc + (f"\n\n*(عرض أول 25 قطعة من إجمالي {len(inv)})*" if len(inv) > 25 else ""),
        color=0x1E90FF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# نظام التحويلات المصرفية
class TransferModal(Modal, title="تحويل العملات والألماس الفوري"):
    target_input = TextInput(label="منشن الشخص أو الآيدي (ID)", placeholder="مثال: @user", style=discord.TextStyle.short, required=True)
    type_input = TextInput(label="نوع العملة (عادية / الماس)", placeholder="اكتب 'عادية' أو 'الماس'", style=discord.TextStyle.short, required=True)
    amount_input = TextInput(label="المبلغ المراد تحويله", placeholder="أدخل الرقم فقط", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sender_id = str(interaction.user.id)
        raw_target = self.target_input.value.strip()
        currency_type = self.type_input.value.strip().lower()
        raw_amount = self.amount_input.value.strip()

        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ المستخدم المستهدف غير صحيح.", ephemeral=True)
        target_id = match_id.group()
        if target_id == sender_id:
            return await interaction.response.send_message("❌ لا يمكنك التحويل لنفسك!", ephemeral=True)

        try:
            amount = int(raw_amount)
            if amount <= 0: raise ValueError()
        except ValueError:
            return await interaction.response.send_message("❌ مبلغ غير صحيح.", ephemeral=True)

        sender_data = users_col.find_one({"user_id": sender_id}) or {}
        field = "diamonds" if ("الماس" in currency_type or "diamond" in currency_type) else "balance"
        name_curr = "💎 ألماس نادر" if field == "diamonds" else "عملة عادية"

        if sender_data.get(field, 0) < amount:
            return await interaction.response.send_message(f"❌ رصيدك غير كافٍ من هذا النوع.", ephemeral=True)

        users_col.update_one({"user_id": sender_id}, {"$inc": {field: -amount}})
        users_col.update_one({"user_id": target_id}, {"$inc": {field: amount}}, upsert=True)
        await interaction.response.send_message(f"✅ تم بنجاح إرسال `{amount:,}` {name_curr} إلى <@{target_id}>.", ephemeral=True)

class BankSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="رصيدي والعملات", description="عرض رصيدك من العملات والألماس.", value="bank_balance", emoji="💳"),
            discord.SelectOption(label="الراتب اليومي", description="استلام مكافأتك اليومية (عملات + ألماس).", value="bank_daily", emoji="💰"),
            discord.SelectOption(label="تحويل العملات والألماس", description="إرسال أموال أو ألماس لأي عضو.", value="bank_transfer", emoji="💸")
        ]
        super().__init__(placeholder="✨ اختر الخدمة المصرفية...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if not is_registered(user_id):
            return await interaction.response.send_message("❌ يرجى التسجيل أولاً بـ `/تسجيل`.", ephemeral=True)

        choice = self.values[0]
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if choice == "bank_balance":
            embed = discord.Embed(
                title="💼 | رصيدك المصرفي",
                description=f"💰 العملات العادية: `{user_data.get('balance', 0):,}`\n💎 الألماس النادر: `{user_data.get('diamonds', 0):,}`",
                color=0xD4AF37
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        elif choice == "bank_daily":
            now = datetime.now(timezone.utc)
            last_claim = user_data.get("last_daily")
            if last_claim and now - last_claim < timedelta(hours=24):
                return await interaction.response.send_message("⏳ لقد استلمت راتبك اليومي مسبقاً، انتظر 24 ساعة.", ephemeral=True)
            
            users_col.update_one({"user_id": user_id}, {"$set": {"last_daily": now}, "$inc": {"balance": 10000, "diamonds": 5}}, upsert=True)
            return await interaction.response.send_message("🎉 تم إيداع الراتب اليومي: `10,000 عملة عادية` + `💎 5 ألماس نادر` في حسابك!", ephemeral=True)
        elif choice == "bank_transfer":
            return await interaction.response.send_modal(TransferModal())

class BankView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BankSelect())

@bot.tree.command(name="تسجيل", description="تسجيل حسابك الجديد في اللعبة")
async def register(interaction: discord.Interaction):
    if is_registered(str(interaction.user.id)):
        return await interaction.response.send_message("ℹ️ أنت مسجل مسبقاً بالفعل.", ephemeral=True)
    await interaction.response.send_modal(RegisterModal())

@bot.tree.command(name="البنك", description="النظام المصرفي وعرض الأرصدة")
async def bank(interaction: discord.Interaction):
    if not is_registered(str(interaction.user.id)):
        return await interaction.response.send_message("❌ سجل أولاً بـ `/تسجيل`.", ephemeral=True)
    embed = discord.Embed(title="🏛️ | البنك المركزي الملكي", description="أدر أموالك وألماسكَ من القائمة أدناه:", color=0xD4AF37)
    await interaction.response.send_message(embed=embed, view=BankView(), ephemeral=False)

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
