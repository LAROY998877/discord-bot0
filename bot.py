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
        intents.members = True
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

# ================== قاعدة بيانات الأبطال والعتاد الضخم ==================
HEROES_DATA = {
    "assassin_dev": {"name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)", "emoji": "🩸", "power_boost": 999999}
}

CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]

def generate_normal_shop_items():
    items = {}
    for cat in CATEGORIES:
        cat_items = []
        for i in range(1, 26):
            cat_items.append({
                "name": f"{cat} إمبراطوري #{i}",
                "price": i * 1500,
                "power": i * 100,
                "category": cat
            })
        items[cat] = cat_items
    return items

def generate_dark_shop_items():
    items = {}
    dark_ranks = ["السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي"]
    
    for cat in CATEGORIES:
        cat_items = []
        for i in range(1, 26):
            if i >= 23:
                rank_title = dark_ranks[i - 23]
                cat_items.append({
                    "name": f"{cat} {rank_title} الخارق",
                    "price": i * 5000,
                    "power": i * 2500,
                    "rank": rank_title,
                    "category": cat
                })
            else:
                cat_items.append({
                    "name": f"{cat} ظلال العذاب #{i}",
                    "price": i * 800,
                    "power": i * 350,
                    "rank": "مظلم محرم",
                    "category": cat
                })
        items[cat] = cat_items
    return items

NORMAL_SHOP = generate_normal_shop_items()
DARK_SHOP = generate_dark_shop_items()

# ================== موديلات الإدخال (Modals) ==================

class DevGiftModal(discord.ui.Modal, title="إهداء عتاد لعضو"):
    gear_name = discord.ui.TextInput(label="اسم قطعة العتاد أو السلاح", placeholder="مثال: سيف التنين الاسطوري", required=True)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = str(self.target_member.id)
            users_col.update_one({"user_id": target_id}, {"$push": {"inventory": self.gear_name.value}}, upsert=True)
            await interaction.followup.send(f"🎁 **تم إرسال العتاد بنجاح!** حصل المستخدم {self.target_member.mention} على القطعة: `{self.gear_name.value}` ⚔️", ephemeral=True)
        except:
            await interaction.followup.send(f"❌ حدث خطأ أثناء إرسال العتاد.", ephemeral=True)

class DevAddBalanceModal(discord.ui.Modal, title="إضافة رصيد لعضو"):
    amount = discord.ui.TextInput(label="المبلغ المراد إضافته", placeholder="مثال: 500000", required=True)

    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = str(self.target_member.id)
            val = int(self.amount.value)
            users_col.update_one({"user_id": target_id}, {"$inc": {"balance": val}}, upsert=True)
            await interaction.followup.send(f"✅ تم إضافة `{val:,}` 🪙 إلى محفظة المستخدم {self.target_member.mention} بنجاح!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ!", ephemeral=True)


# ================== قوائم اختيار وشراء المتاجر (Select Menus) ==================

class NormalShopSelect(discord.ui.Select):
    def __init__(self, category_name: str):
        self.category_name = category_name
        items = NORMAL_SHOP.get(category_name, [])[:25]
        options = []
        for idx, item in enumerate(items):
            options.append(discord.SelectOption(
                label=item["name"][:100],
                description=f"السعر: {item['price']:,} ذهب | القوة: +{item['power']}",
                value=str(idx)
            ))
        super().__init__(placeholder=f"اختر من فئة {category_name}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        item_idx = int(self.values[0])
        item = NORMAL_SHOP[self.category_name][item_idx]
        price = item["price"]
        balance = user_data.get("balance", 0)

        if balance < price:
            return await interaction.followup.send(f"❌ رصيدك الإمبراطوري ({balance:,} 🪙) لا يكفي لشراء `{item['name']}` السعر المطلوب ({price:,} 🪙).", ephemeral=True)

        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"balance": -price, "power": item["power"]},
                "$push": {"inventory": item["name"]}
            }
        )
        await interaction.followup.send(f"✅ **تم الشراء بنجاح!** حصلت على `{item['name']}` وتمت إضافة طاقتها لرصيدك.", ephemeral=True)

class NormalShopCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=cat, description=f"تصفح قسم الـ {cat}", emoji="🛡️") for cat in CATEGORIES]
        super().__init__(placeholder="📁 اختر قسم العتاد الإمبراطوري...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_cat = self.values[0]
        view = discord.ui.View()
        view.add_item(NormalShopSelect(selected_cat))
        await interaction.response.send_message(f"🏛️ **أنت تستعرض الآن قسم: {selected_cat}**\nاختر القطعة المناسبة للشراء:", view=view, ephemeral=True)

class NormalShopDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(NormalShopCategorySelect())

    @discord.ui.button(label="الانتقال للسوق المظلم 🕳️", style=discord.ButtonStyle.danger, emoji="🩸", row=1)
    async def go_dark_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🩸 تحذير: سوق الظلال الملعون",
            description="هنا تُباع أسلحة الرتب الثلاث المرعبة:\n• **الشيطان الأبدي** 👑\n• **الجحيم القاتل** 🔥\n• **السفاح القرمزي** 🔴\n\nالعملة المستخدمة: **الألماس الأسود** 💎.",
            color=discord.Color.dark_embed()
        )
        await interaction.response.edit_message(embed=embed, view=DarkShopDropdownView())


class DarkShopSelect(discord.ui.Select):
    def __init__(self, category_name: str):
        self.category_name = category_name
        items = DARK_SHOP.get(category_name, [])[:25]
        options = []
        for idx, item in enumerate(items):
            options.append(discord.SelectOption(
                label=item["name"][:100],
                description=f"السعر: {item['price']:,} ألماس أسود | القوة: +{item['power']}",
                value=str(idx)
            ))
        super().__init__(placeholder=f"اختر من أسلحة الظلال {category_name}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        item_idx = int(self.values[0])
        item = DARK_SHOP[self.category_name][item_idx]
        price = item["price"]
        diamonds = user_data.get("diamonds", 0)

        if diamonds < price:
            return await interaction.followup.send(f"❌ رصيدك من الألماس الأسود ({diamonds:,} 💎) لا يكفي لشراء `{item['name']}` السعر المطلوب ({price:,} 💎).", ephemeral=True)

        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"diamonds": -price, "power": item["power"]},
                "$push": {"inventory": item["name"]}
            }
        )
        await interaction.followup.send(f"🩸 **تمت صفقة الظلال بنجاح!** اقتنيت `{item['name']}` المرعب وتمت إضافة طاقته الخارقة.", ephemeral=True)

class DarkShopCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=cat, description=f"تصفح قسم ظلال الـ {cat}", emoji="🔥") for cat in CATEGORIES]
        super().__init__(placeholder="🕳️ اختر قسم أسلحة الظلال المحرمة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_cat = self.values[0]
        view = discord.ui.View()
        view.add_item(DarkShopSelect(selected_cat))
        await interaction.response.send_message(f"🩸 **أنت تستعرض قسم الظلال المحرم: {selected_cat}**\nاختر السلاح المرعب لشرائه:", view=view, ephemeral=True)

class DarkShopDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(DarkShopCategorySelect())

    @discord.ui.button(label="العودة للمنطقة الآمنة 🏛️", style=discord.ButtonStyle.secondary, emoji="🔙", row=1)
    async def return_normal_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ متجر الإمبراطورية المركزي (المنطقة الآمنة)",
            description="أهلاً بك مجدداً في النور. اختر القسم المناسب لتجهيز بطلك.",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=NormalShopDropdownView())


# ================== واجهات البنك (Bank Views) ==================

class BankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="إيداع أموال", style=discord.ButtonStyle.success, emoji="📥", row=0)
    async def deposit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BankDepositModal())

    @discord.ui.button(label="سحب أموال", style=discord.ButtonStyle.danger, emoji="📤", row=0)
    async def withdraw_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BankWithdrawModal())

class BankDepositModal(discord.ui.Modal, title="إيداع أموال في البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد إيداعه (أو اكتب الكل)", placeholder="مثال: 5000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        wallet = user_data.get("balance", 0)
        val_text = self.amount.value.strip()
        
        if val_text.lower() in ["الكل", "all"]:
            val = wallet
        else:
            try:
                val = int(val_text)
            except:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك إيداع مبلغ صفر أو سالب!", ephemeral=True)
        if wallet < val:
            return await interaction.followup.send("❌ لا توجد لديك أموال كافية في محفظتك لإيداع هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -val, "bank": val}})
        await interaction.followup.send(f"✅ تم إيداع `{val:,}` 🪙 في البنك بنجاح!", ephemeral=True)

class BankWithdrawModal(discord.ui.Modal, title="سحب أموال من البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد سحبه (أو اكتب الكل)", placeholder="مثال: 5000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        bank_balance = user_data.get("bank", 0)
        val_text = self.amount.value.strip()
        
        if val_text.lower() in ["الكل", "all"]:
            val = bank_balance
        else:
            try:
                val = int(val_text)
            except:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك سحب مبلغ صفر أو سالب!", ephemeral=True)
        if bank_balance < val:
            return await interaction.followup.send("❌ رصيدك في البنك لا يكفي لسحب هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"bank": -val, "balance": val}})
        await interaction.followup.send(f"✅ تم سحب `{val:,}` 🪙 من البنك إلى محفظتك بنجاح!", ephemeral=True)


# ================== نظام تطوير المعدلات المنفصل (Stats Upgrade) ==================

STATS_COST = 5000  # تكلفة التطوير لكل ضغطة (تستطيع تعديلها حسب رغبتك)
STATS_INCREMENT = 100  # مقدار الزيادة في المعدل

class StatsUpgradeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="التصويب", description=f"زيادة معدل التصويب (التكلفة: {STATS_COST:,} 🪙)", emoji="🎯", value="aim"),
            discord.SelectOption(label="المراوغة", description=f"زيادة معدل المراوغة (التكلفة: {STATS_COST:,} 🪙)", emoji="💨", value="evasion"),
            discord.SelectOption(label="الهجوم", description=f"زيادة معدل الهجوم (التكلفة: {STATS_COST:,} 🪙)", emoji="🗡️", value="attack"),
            discord.SelectOption(label="الدقة", description=f"زيادة معدل الدقة (التكلفة: {STATS_COST:,} 🪙)", emoji="👁️", value="accuracy"),
            discord.SelectOption(label="القاتلة", description=f"زيادة معدل الضربة القاتلة (التكلفة: {STATS_COST:,} 🪙)", emoji="💥", value="critical"),
            discord.SelectOption(label="السحر", description=f"زيادة معدل السحر (التكلفة: {STATS_COST:,} 🪙)", emoji="🔮", value="magic"),
            discord.SelectOption(label="الذكاء", description=f"زيادة معدل الذكاء (التكلفة: {STATS_COST:,} 🪙)", emoji="🧠", value="intelligence"),
            discord.SelectOption(label="الدفاع", description=f"زيادة معدل الدفاع (التكلفة: {STATS_COST:,} 🪙)", emoji="🛡️", value="defense"),
        ]
        super().__init__(placeholder="📊 اختر المعدل المطلوب تطويره بلا حدود...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        balance = user_data.get("balance", 0)
        if balance < STATS_COST:
            return await interaction.followup.send(f"❌ رصيدك ({balance:,} 🪙) لا يكفي! تحتاج إلى `{STATS_COST:,}` ذهبة لتطوير هذا المعدل.", ephemeral=True)

        stat_key = self.values[0]
        
        # خصم العملات وزيادة المعدل المطلوب بلا حدود
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": -STATS_COST,
                    stat_key: STATS_INCREMENT
                }
            }
        )
        
        updated_user = users_col.find_one({"user_id": user_id})
        new_value = updated_user.get(stat_key, 0)
        
        await interaction.followup.send(f"✅ **تم تطوير المعدل بنجاح!** أصبحت قيمة `{stat_key}` الجديدة لديك: `{new_value:,}` 📈", ephemeral=True)

class StatsUpgradeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(StatsUpgradeSelect())


# ================== واجهات الطوابق الشاملة بالأزرار المطلوبة ==================

class FloorsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="الطابق التالي", style=discord.ButtonStyle.success, emoji="🏢", row=0)
    async def next_floor_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.response.send_message("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
        
        current_floor = user_data.get("max_floor", 0) + 1
        power = user_data.get("power", 100)
        required_power = current_floor * 80

        if power >= required_power:
            reward = current_floor * 500
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"balance": reward, "kills": 1},
                    "$set": {"max_floor": current_floor}
                }
            )
            embed = discord.Embed(
                title=f"🏢 الطابق #{current_floor} - انتصار باهر!",
                description=f"تم سحق وحوش الطابق `{current_floor}` بنجاح بفضل قوتك (`{power:,}`)!",
                color=discord.Color.green()
            )
            embed.add_field(name="🎁 مكافأة الصعود", value=f"+{reward:,} 🪙", inline=False)
        else:
            embed = discord.Embed(
                title=f"🏢 الطابق #{current_floor} - هزيمة قاسية!",
                description=f"طاقتك (`{power:,}`) غير كافية لصد وحوش هذا الطابق! المطلوب `{required_power:,}` طاقة كحد أدنى.",
                color=discord.Color.red()
            )
            embed.set_footer(text="قم بترقية معداتك لتجاوز هذا الطابق.")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="المتجر", style=discord.ButtonStyle.primary, emoji="🏛️", row=0)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ متجر الإمبراطورية المركزي",
            description="اختر القسم وتصفح العتاد عبر القوائم المنسدلة المتاحة بالأسفل.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=NormalShopDropdownView(), ephemeral=True)

    @discord.ui.button(label="تطوير معدات", style=discord.ButtonStyle.secondary, emoji="⚡", row=0)
    async def upgrade_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$inc": {"power": 500, "balance": -2000}}, upsert=True)
        await interaction.response.send_message("⚡ **تم تطوير معداتك!** زادت طاقتك بمقدار `500` مقابل خصم `2,000` ذهبة.", ephemeral=True)

    @discord.ui.button(label="حقيبتي", style=discord.ButtonStyle.secondary, emoji="🎒", row=1)
    async def inventory_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.response.send_message("❌ غير مسجل.", ephemeral=True)
        inv = user_data.get("inventory", [])
        inv_text = "\n".join([f"• {item}" for item in inv]) if inv else "الحقيبة فارغة حالياً."
        embed = discord.Embed(
            title=f"🎒 حقيبة العتاد الخاصة بك",
            description=inv_text,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="تطوير معدلاتي", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def upgrade_stats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📊 لوحة تطوير المعدلات القيصرية",
            description=f"اختر المعدل الذي تريد ترقيته من القائمة أدناه.\nكل ترقية تكلف `{STATS_COST:,}` ذهبة وتمنحك `+100` نقاط إضافية **بلا حدود قصوى**!",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=True)


# ================== واجهات واختيارات المطورين ==================

class DevAddUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🛠️ اختر العضو لترقيته لمطور بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chosen_member = self.values[0]
        target_id = str(chosen_member.id)
        devs_col.update_one({"user_id": target_id}, {"$set": {"user_id": target_id}}, upsert=True)
        await interaction.followup.send(f"🛠️ **تمت الترقية بنجاح!** أصبح العضو {chosen_member.mention} مطوراً معتمداً.", ephemeral=True)

class DevAddUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevAddUserSelect())

class DevGiftUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🎁 اختر العضو لإهداء العتاد له بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        chosen_member = self.values[0]
        await interaction.response.send_modal(DevGiftModal(target_member=chosen_member))

class DevGiftUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevGiftUserSelect())

class DevBalanceUserSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="🪙 اختر العضو لإضافة الرصيد له بالمنشن...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        chosen_member = self.values[0]
        await interaction.response.send_modal(DevAddBalanceModal(target_member=chosen_member))

class DevBalanceUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevBalanceUserSelect())

class DevControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="تفعيل السفاح", style=discord.ButtonStyle.danger, emoji="🩸", row=0)
    async def assassin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        assassin = HEROES_DATA["assassin_dev"]
        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "selected_hero": assassin['name'],
                    "power": assassin['power_boost'],
                    "max_floor": 999,
                    "kills": 99999,
                    "custom_title": "💀 حاكم الأبعاد ومالك السفاح"
                }
            },
            upsert=True
        )
        await interaction.followup.send("🩸 **تم تفعيل طاقة السفاح المطلقة وإحصائياتك المرعبة بنجاح!**", ephemeral=True)

    @discord.ui.button(label="ثروات لانهائية", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def wealth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": 999999999, "diamonds": 999999999}},
            upsert=True
        )
        await interaction.followup.send("💎 **تم ضخ الثروات اللانهائية!** حصلت على عملات وألماس بلا حدود.", ephemeral=True)

    @discord.ui.button(label="أقصى عتاد", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def max_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "aim": 9999999999, "evasion": 9999999999,
                    "attack": 9999999999, "accuracy": 9999999999,
                    "defense": 9999999999, "critical": 9999999999,
                    "magic": 9999999999, "intelligence": 9999999999
                }
            },
            upsert=True
        )
        await interaction.followup.send("⚡ **تمت ترقية كافة المعدلات والعتاد للأقصى المطلق!**", ephemeral=True)

    @discord.ui.button(label="إهداء عتاد", style=discord.ButtonStyle.secondary, emoji="🎁", row=1)
    async def gift_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎁 اختر العضو لإهداء العتاد له بالمنشن:", view=DevGiftUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة رصيد", style=discord.ButtonStyle.secondary, emoji="🪙", row=1)
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🪙 اختر العضو لإضافة الرصيد له بالمنشن:", view=DevBalanceUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة مطور", style=discord.ButtonStyle.secondary, emoji="🛠️", row=1)
    async def add_dev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ اختر العضو لترقيته لمطور بالمنشن:", view=DevAddUserSelectView(), ephemeral=True)


# ================== أوامر البوت الأساسية الشاملة ==================

@bot.tree.command(name="المتجر", description="فتح بوابة المتاجر (العادي والمظلم)")
async def shop_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏛️ متجر الإمبراطورية المركزي",
        description="أهلاً بك أيها المقاتل. اختر القسم وتصفح العتاد عبر القوائم المنسدلة بالأسفل.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=NormalShopDropdownView(), ephemeral=True)

@bot.tree.command(name="البنك", description="فتح لوحة البنك المركزي لإدارة أموالك (إيداع وسحب)")
async def bank_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    
    embed = discord.Embed(
        title="🏦 البنك الإمبراطوري المركزي",
        description="حافظ على أموالك من قطاع الطرق في الخزنة الآمنة للبنك.",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 أموال المحفظة", value=f"{balance:,} 🪙", inline=True)
    embed.add_field(name="💳 رصيد البنك", value=f"{bank:,} 🪙", inline=True)
    embed.set_footer(text="استخدم الأزرار أدناه للإيداع أو السحب.")
    await interaction.response.send_message(embed=embed, view=BankView(), ephemeral=True)

@bot.tree.command(name="الطوابق", description="صعود طوابق البرج القتالي وتحدي الأعداء")
async def floors_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
    
    current_floor = user_data.get("max_floor", 0) + 1
    embed = discord.Embed(
        title=f"🏢 بوابة الطوابق الإمبراطورية - الطابق التالي: #{current_floor}",
        description="اضغط على زر **الطابق التالي** للبدء بالمعركة وصعود البرج، أو استخدم الأزرار الأخرى للإدارة.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=FloorsView(), ephemeral=False)

@bot.tree.command(name="تطوير_معدلاتي", description="فتح لوحة تطوير المعدلات القتالية بلا حدود قصوى")
async def upgrade_stats_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يرجى التسجيل أولاً باستخدام `/تسجيل`.", ephemeral=True)
    
    embed = discord.Embed(
        title="📊 لوحة تطوير المعدلات القيصرية",
        description=f"اختر المعدل الذي تريد ترقيته بلا حدود قصوى.\nكل ترقية تكلف `{STATS_COST:,}` ذهبة وتمنحك نقاطاً إضافية فورية!",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=StatsUpgradeView(), ephemeral=True)

@bot.tree.command(name="تحويل", description="تحويل أموال من رصيدك لعضو آخر بالمنشن")
@app_commands.describe(member="العضو المراد التحويل له", amount="المبلغ المراد تحويله")
async def transfer_command(interaction: discord.Interaction, member: discord.Member, amount: int):
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ لا يمكنك التحويل لنفسك!", ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
    
    sender_id = str(interaction.user.id)
    receiver_id = str(member.id)
    
    sender_data = users_col.find_one({"user_id": sender_id})
    if not sender_data or sender_data.get("balance", 0) < amount:
        return await interaction.response.send_message("❌ رصيد محفظتك لا يكفي لإتمام هذا التحويل!", ephemeral=True)
    
    users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount}})
    users_col.update_one({"user_id": receiver_id}, {"$inc": {"balance": amount}}, upsert=True)
    
    await interaction.response.send_message(f"✅ **تم التحويل بنجاح!** أرسلت `{amount:,}` 🪙 إلى العضو {member.mention}.", ephemeral=False)

@bot.tree.command(name="المطور", description="لوحة السيطرة والتحكم العليا للمطورين")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة السيطرة والتحكم العليا للمطورين",
        description="أهلاً بك أيها الحاكم المطلق. استخدم الأزرار أدناه لتنفيذ الأوامر الخارقة:",
        color=discord.Color.dark_embed()
    )
    await interaction.response.send_message(embed=embed, view=DevControlView(), ephemeral=True)

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
    embed.add_field(name="💎 الألماس والعملات", value=f"{diamonds:,} 💎", inline=True)

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
        "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
        "defense": 10, "critical": 10, "magic": 10, "intelligence": 10
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

bot.run(DISCORD_TOKEN)
