import os
import re
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة البنك والمتاجر الأسطورية بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل الآن باسم: {bot.user}")

# ================== عتاد المتجر العادي (عملات عادية) ==================
NORMAL_SHOP_ITEMS = {
    "خوذة": [
        {"id": "n_helm_1", "name": "خوذة الجندي البسيطة", "tier": "شائع", "stats": "الدرع: +15 | الصحة: +20", "price": 300, "stock": 1000},
        {"id": "n_helm_2", "name": "خوذة الفارس الفولاذية", "tier": "نادر", "stats": "الدرع: +40 | الصحة: +50", "price": 800, "stock": 1000}
    ],
    "درع": [
        {"id": "n_chest_1", "name": "درع قماشي مقوى", "tier": "غير مألوف", "stats": "الدرع: +25 | خفة الحركة: +5", "price": 400, "stock": 1000},
        {"id": "n_chest_2", "name": "درع الحرس الملكي", "tier": "نادر", "stats": "الدرع: +60 | الصحة: +100", "price": 1200, "stock": 1000}
    ],
    "بنطال": [
        {"id": "n_pant_1", "name": "بنطال جلدي خفيف", "tier": "شائع", "stats": "الدرع: +10 | السرعة: +5", "price": 250, "stock": 1000},
        {"id": "n_pant_2", "name": "واقي الساقين الحديدي", "tier": "نادر", "stats": "الدرع: +35", "price": 750, "stock": 1000}
    ],
    "حذاء": [
        {"id": "n_boot_1", "name": "حذاء المستكشف", "tier": "غير مألوف", "stats": "السرعة: +20 | الدرع: +5", "price": 300, "stock": 1000},
        {"id": "n_boot_2", "name": "حذاء المعارك الثقيل", "tier": "نادر", "stats": "الدرع: +20 | السرعة: -5", "price": 600, "stock": 1000}
    ],
    "سيف": [
        {"id": "n_swd_1", "name": "سيف التدريب الخشبي", "tier": "شائع", "stats": "الهجوم: +15", "price": 200, "stock": 1000},
        {"id": "n_swd_2", "name": "سيف الفولاذ المصقول", "tier": "نادر", "stats": "الهجوم: +55 | نسبة الكريتيكال: 5%", "price": 1500, "stock": 1000}
    ],
    "مطرقة": [
        {"id": "n_ham_1", "name": "مطرقة الحداد", "tier": "شائع", "stats": "الهجوم: +25 | السرعة: -10", "price": 400, "stock": 1000},
        {"id": "n_ham_2", "name": "مطرقة تحطيم الدروع", "tier": "نادر", "stats": "الهجوم: +70 | كسر الدرع: 15%", "price": 1800, "stock": 1000}
    ],
    "خنجر": [
        {"id": "n_dag_1", "name": "خنجر اللص", "tier": "غير مألوف", "stats": "الهجوم: +20 | السرعة: +15", "price": 350, "stock": 1000},
        {"id": "n_dag_2", "name": "خنجر الاغتيال المسموم", "tier": "نادر", "stats": "الهجوم: +40 | ضرر السم: +10", "price": 1100, "stock": 1000}
    ],
    "عصا سحرية": [
        {"id": "n_wand_1", "name": "غصن شجرة البلوط", "tier": "شائع", "stats": "قوة السحر: +20", "price": 300, "stock": 1000},
        {"id": "n_wand_2", "name": "عصا بلورة المانا", "tier": "نادر", "stats": "قوة السحر: +65 | المانا: +50", "price": 1600, "stock": 1000}
    ]
}

# ================== عتاد المتجر المظلم (ألماس نادر) ==================
DARK_SHOP_ITEMS = {
    "خوذة": [
        {"id": "d_helm_1", "name": "خوذة عذاب الأرواح", "tier": "ملعون", "stats": "الدرع: +150 | امتصاص الصحة: 5%", "price": 30, "stock": 1000},
        {"id": "d_helm_2", "name": "تاج أمير الشياطين", "tier": "الشيطان", "stats": "الدرع: +350 | هيبة مرعبة تقلل هجوم العدو 20%", "price": 150, "stock": 1000}
    ],
    "درع": [
        {"id": "d_chest_1", "name": "درع صرخات الموتى", "tier": "الجحيم", "stats": "الدرع: +400 | مناعة ضد النار 50%", "price": 120, "stock": 1000},
        {"id": "d_chest_2", "name": "عباءة الظل المطلق", "tier": "السفاح", "stats": "الدرع: +250 | التخفي التلقائي بالظلام 30%", "price": 100, "stock": 1000}
    ],
    "بنطال": [
        {"id": "d_pant_1", "name": "دروع الساقين الدموية", "tier": "الجحيم", "stats": "الدرع: +280 | عكس الضرر: 10%", "price": 90, "stock": 1000},
        {"id": "d_pant_2", "name": "بنطال ملك الهاوية", "tier": "الشيطان", "stats": "الدرع: +320 | الصحة القصوى: +500", "price": 130, "stock": 1000}
    ],
    "حذاء": [
        {"id": "d_boot_1", "name": "خطوات السفاح الصامتة", "tier": "السفاح", "stats": "السرعة: +300 | الدرع: +90 | لا يُصدر صوتاً", "price": 85, "stock": 1000},
        {"id": "d_boot_2", "name": "حذاء نيزك الجحيم", "tier": "الجحيم", "stats": "السرعة: +150 | يترك أثراً نارياً يحرق الأعداء", "price": 110, "stock": 1000}
    ],
    "سيف": [
        {"id": "d_swd_1", "name": "نصل دمار العوالم", "tier": "الشيطان", "stats": "الهجوم: +750 | تدمير شامل للدروع", "price": 250, "stock": 1000},
        {"id": "d_swd_2", "name": "سيف قاطع الأرواح", "tier": "السفاح", "stats": "الهجوم: +500 | ضربة قاتلة 25% (كريتيكال 3x)", "price": 180, "stock": 1000}
    ],
    "مطرقة": [
        {"id": "d_ham_1", "name": "كسارة عظام الجحيم", "tier": "الجحيم", "stats": "الهجوم: +650 | إحداث زلزال عند الضرب", "price": 190, "stock": 1000},
        {"id": "d_ham_2", "name": "مطرقة اللعنة الأبدية", "tier": "ملعون", "stats": "الهجوم: +450 | تصيب العدو بالعمى", "price": 80, "stock": 1000}
    ],
    "خنجر": [
        {"id": "d_dag_1", "name": "ناب مصاص الدماء الأكبر", "tier": "السفاح", "stats": "الهجوم: +480 | يسرق 30% من صحة العدو لك", "price": 200, "stock": 1000},
        {"id": "d_dag_2", "name": "خنجر طقوس الشياطين", "tier": "الشيطان", "stats": "الهجوم: +600 | يخترق كل الدروع السحرية", "price": 220, "stock": 1000}
    ],
    "عصا سحرية": [
        {"id": "d_wand_1", "name": "صولجان بوابة الجحيم", "tier": "الجحيم", "stats": "السحر: +800 | استدعاء نيازك مصغرة", "price": 240, "stock": 1000},
        {"id": "d_wand_2", "name": "عصا سيد الشياطين", "tier": "الشيطان", "stats": "السحر: +999 | تحكم كامل بعقول الأعداء الضعفاء", "price": 300, "stock": 1000}
    ]
}

# ================== القوائم المنسدلة للمتاجر ==================
class ShopSpecificSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category):
        self.items_pool = items_pool
        self.shop_type = shop_type
        
        options = [
            discord.SelectOption(
                label=f"{item['name']} [{item['tier']}]", 
                value=item["id"], 
                description=f"السعر: {item['price']} | {item['stats']} | المخزون: {item['stock']}"
            ) for item in items_pool
        ]
        super().__init__(placeholder=f"اختر قطعة من قسم {category}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        item_id = self.values[0]
        item = next((it for it in self.items_pool if it["id"] == item_id), None)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if self.shop_type == "normal":
            if user_data.get("balance", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك العادي غير كافٍ! تحتاج `{item['price']}` 🪙.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}}, upsert=True)
        else:
            if user_data.get("diamonds", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك من الألماس غير كافٍ! تحتاج `💎 {item['price']}`.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}}, upsert=True)

        await interaction.followup.send(
            f"🎉 **عملية شراء ناجحة!**\n⚔️ القطعة: **{item['name']}**\n🔰 الرتبة: **{item['tier']}**\n📊 المميزات: `{item['stats']}`\n*تمت إضافتها لحقيبتك!*", 
            ephemeral=True
        )

class ShopCategorySelect(discord.ui.Select):
    def __init__(self, shop_type):
        self.shop_type = shop_type
        # تم إضافة الأقسام الـ 8 التي طلبتها
        options = [
            discord.SelectOption(label="خوذة", value="خوذة", emoji="🪖"),
            discord.SelectOption(label="درع", value="درع", emoji="🛡️"),
            discord.SelectOption(label="بنطال", value="بنطال", emoji="👖"),
            discord.SelectOption(label="حذاء", value="حذاء", emoji="🥾"),
            discord.SelectOption(label="سيف", value="سيف", emoji="⚔️"),
            discord.SelectOption(label="مطرقة", value="مطرقة", emoji="🔨"),
            discord.SelectOption(label="خنجر", value="خنجر", emoji="🗡️"),
            discord.SelectOption(label="عصا سحرية", value="عصا سحرية", emoji="🪄")
        ]
        super().__init__(placeholder="اختر فئة العتاد التي تريد تصفحها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        items_pool = NORMAL_SHOP_ITEMS.get(category, []) if self.shop_type == "normal" else DARK_SHOP_ITEMS.get(category, [])
        
        view = discord.ui.View()
        view.add_item(ShopSpecificSelect(items_pool, self.shop_type, category))
        await interaction.response.edit_message(content=f"🛒 تتصفح الآن قسم: **{category}**\nاختر القطعة التي تناسبك:", view=view)

class ShopView(discord.ui.View):
    def __init__(self, author_id, shop_type):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(ShopCategorySelect(shop_type))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="المتجر_العادي", description="تصفح وشراء العتاد العادي المتوفر (بالعملة العادية)")
async def normal_shop(interaction: discord.Interaction):
    view = ShopView(interaction.user.id, "normal")
    await interaction.response.send_message("🏬 **متجر العتاد العادي**\nيحتوي على 1000 قطعة من كل فئة. اختر القسم من القائمة بالأسفل:", view=view)

@bot.tree.command(name="المتجر_المظلم", description="تصفح العتاد الأسطوري والملعون (بالألماس)")
async def dark_shop(interaction: discord.Interaction):
    view = ShopView(interaction.user.id, "dark")
    await interaction.response.send_message("🌌 **المتجر المظلم (سوق الأساطير)**\nمكان العتاد المحرم ورتب (الشيطان، الجحيم، السفاح). اختر القسم بحذر:", view=view)

# ================== نظام البنك المركزي ==================
class TransferModal(discord.ui.Modal, title='تحويل الأموال 💸'):
    target = discord.ui.TextInput(label='منشن الشخص', placeholder='مثال: @Ahmed', required=True)
    amount = discord.ui.TextInput(label='المبلغ المراد تحويله', placeholder='مثال: 5000', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        target_id = re.sub(r'\D', '', self.target.value)
        if not target_id or not self.amount.value.isdigit():
            return await interaction.response.send_message("❌ تأكد من المنشن وكتابة المبلغ بالأرقام فقط!", ephemeral=True)
        
        amount_val = int(self.amount.value)
        if amount_val <= 0:
            return await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من الصفر!", ephemeral=True)

        sender_id = str(interaction.user.id)
        if sender_id == target_id:
            return await interaction.response.send_message("❌ لا يمكنك التحويل لنفسك!", ephemeral=True)

        sender_data = users_col.find_one({"user_id": sender_id}) or {}
        if sender_data.get("balance", 0) < amount_val:
            return await interaction.response.send_message("❌ رصيدك غير كافٍ لإتمام التحويل!", ephemeral=True)

        users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount_val}})
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount_val}}, upsert=True)
        await interaction.response.send_message(f"✅ **تم التحويل بنجاح!**\nتم تحويل `{amount_val}` 🪙 إلى <@{target_id}>.", ephemeral=False)

class BankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="حسابي والرصيد", value="balance", description="عرض أموالك وحقيبتك", emoji="💳"),
            discord.SelectOption(label="الراتب اليومي", value="daily", description="استلام راتبك", emoji="💰"),
            discord.SelectOption(label="قسم القروض", value="loan", description="طلب وسداد القروض", emoji="🏦"),
            discord.SelectOption(label="تحويل عملات", value="transfer", description="إرسال أموال لشخص آخر", emoji="💸")
        ]
        super().__init__(placeholder="اختر الخدمة البنكية...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if choice == "transfer":
            return await interaction.response.send_modal(TransferModal())

        await interaction.response.defer()

        if choice == "balance":
            bal = user_data.get("balance", 0)
            diamonds = user_data.get("diamonds", 0)
            inventory = user_data.get("inventory", [])
            inv_list = "\n".join([f"• {item['name']} `[{item['tier']}]`" for item in inventory]) if inventory else "الحقيبة فارغة"
            
            embed = discord.Embed(title="💳 كشف الحساب البنكي", color=discord.Color.gold())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="الرصيد العادي", value=f"`{bal}` 🪙", inline=True)
            embed.add_field(name="الألماس النادر", value=f"`{diamonds}` 💎", inline=True)
            embed.add_field(name="🎒 مقتنيات الحقيبة", value=inv_list, inline=False)
            
            view = BankView(interaction.user.id)
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

        elif choice == "daily":
            last_claim = user_data.get("last_daily")
            now = datetime.utcnow()
            if last_claim and now - last_claim < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_claim)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                mins, _ = divmod(remainder, 60)
                msg = f"⏳ **عذراً!** لقد استلمت راتبك مسبقاً. عد بعد `{hours} ساعة و {mins} دقيقة`."
            else:
                reward = 5000
                users_col.update_one({"user_id": user_id}, {"$inc": {"balance": reward}, "$set": {"last_daily": now}}, upsert=True)
                msg = f"🎁 **تم استلام الراتب!**\nأُضيفت `{reward}` 🪙 عملة إلى حسابك بنجاح."
            
            embed = discord.Embed(description=msg, color=discord.Color.green())
            view = BankView(interaction.user.id)
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

        elif choice == "loan":
            loan_amount = user_data.get("loan_amount", 0)
            loan_due = user_data.get("loan_due_date")
            now = datetime.utcnow()
            
            if loan_amount > 0 and loan_due and now > loan_due:
                penalty = 2000 
                loan_amount += penalty
                new_due = now + timedelta(hours=24)
                users_col.update_one({"user_id": user_id}, {"$set": {"loan_amount": loan_amount, "loan_due_date": new_due}})
                loan_due = new_due

            embed = discord.Embed(title="🏦 قسم القروض البنكية", color=discord.Color.dark_red())
            if loan_amount > 0:
                due_format = f"<t:{int(loan_due.timestamp())}:R>"
                embed.description = f"⚠️ **عليك قرض حالي!**\nالمبلغ المطلوب سداده: `{loan_amount}` 🪙\nموعد السداد النهائي: {due_format}\n*(تحذير: سيتم إضافة غرامة 2000 عملة عند التأخير)*"
            else:
                embed.description = "✅ **سجلك نظيف!**\nلا توجد عليك أي ديون. يمكنك سحب قرض بقيمة `20,000` 🪙 (تُسدد `25,000` مع الفوائد خلال 48 ساعة)."
            
            view = BankView(interaction.user.id)
            if loan_amount > 0:
                view.add_item(PayLoanButton())
            else:
                view.add_item(TakeLoanButton())
            
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

class TakeLoanButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="استلام قرض (20,000)", emoji="💵")
    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        due_date = datetime.utcnow() + timedelta(hours=48)
        users_col.update_one(
            {"user_id": user_id}, 
            {"$inc": {"balance": 20000}, "$set": {"loan_amount": 25000, "loan_due_date": due_date}}, 
            upsert=True
        )
        await interaction.response.send_message("✅ **تم إيداع القرض!** استلمت `20,000` وعليك سداد `25,000` خلال يومين.", ephemeral=True)

class PayLoanButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="سداد القرض بالكامل", emoji="💸")
    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}
        debt = user_data.get("loan_amount", 0)
        
        if user_data.get("balance", 0) < debt:
            return await interaction.response.send_message("❌ رصيدك الحالي لا يكفي لسداد القرض!", ephemeral=True)
            
        users_col.update_one(
            {"user_id": user_id}, 
            {"$inc": {"balance": -debt}, "$set": {"loan_amount": 0, "loan_due_date": None}}
        )
        await interaction.response.send_message("✅ **ممتاز!** تم سداد قرضك بالكامل وتصفية ديونك.", ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(BankSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ عذراً، هذه اللوحة خاصة بصاحب الأمر فقط!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="بنك", description="فتح حسابك البنكي (رصيد، راتب، تحويل، قروض)")
async def bank_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🏦 البنك المركزي للعبة", description="أهلاً بك في نظام البنك الشامل. الرجاء اختيار الخدمة المطلوبة من القائمة أدناه.", color=discord.Color.gold())
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png")
    embed.set_footer(text="جميع المعاملات مسجلة ومؤمنة في قاعدة البيانات")
    
    view = BankView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
