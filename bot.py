import os
import re
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات والبيئة ---
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
        print("✅ تم مزامنة جميع الأوامر والأنظمة بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل الآن باسم: {bot.user}")

# ================== بيانات المتاجر ==================
NORMAL_SHOP_ITEMS = {
    "أسلحة": [
        {"id": "n_sword", "name": "سيف حديدي", "tier": "شائع", "power": 50, "price": 1000},
        {"id": "n_bow", "name": "قوس خشبي", "tier": "شائع", "power": 40, "price": 800}
    ],
    "دروع": [
        {"id": "n_shield", "name": "درع خشبي", "tier": "شائع", "defense": 30, "price": 500}
    ]
}

DARK_SHOP_ITEMS = {
    "أسلحة مظلمة": [
        {"id": "d_blade", "name": "شفرة الظلام", "tier": "أسطوري", "power": 250, "price": 50},
    ],
    "دروع مظلمة": [
        {"id": "d_plate", "name": "درع التنين الأسود", "tier": "أسطوري", "defense": 200, "price": 40}
    ]
}

# ================== نظام المتاجر (بالقوائم المنسدلة) ==================
class ShopSpecificSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category):
        self.items_pool = items_pool
        self.shop_type = shop_type
        options = [
            discord.SelectOption(
                label=item["name"], 
                value=item["id"], 
                description=f"السعر: {item['price']} | القوة/الدرع: {item.get('power', item.get('defense', 0))}"
            ) for item in items_pool
        ]
        super().__init__(placeholder=f"اختر قطعة لشرائها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        item_id = self.values[0]
        item = next((it for it in self.items_pool if it["id"] == item_id), None)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if self.shop_type == "normal":
            if user_data.get("balance", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك العادي غير كافٍ! تحتاج `{item['price']}`.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}}, upsert=True)
        else:
            if user_data.get("diamonds", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك من الألماس غير كافٍ! تحتاج `💎 {item['price']}`.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}}, upsert=True)

        await interaction.followup.send(f"🎉 **مبروك!** تم شراء **{item['name']}** وإضافته لحقيبتك.", ephemeral=True)

class ShopCategorySelect(discord.ui.Select):
    def __init__(self, shop_type):
        self.shop_type = shop_type
        options = [
            discord.SelectOption(label="قسم الأسلحة", value="أسلحة" if shop_type == "normal" else "أسلحة مظلمة", emoji="⚔️"),
            discord.SelectOption(label="قسم الدروع", value="دروع" if shop_type == "normal" else "دروع مظلمة", emoji="🛡️")
        ]
        super().__init__(placeholder="اختر القسم الذي تريد تصفحه...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        items_pool = NORMAL_SHOP_ITEMS.get(category, []) if self.shop_type == "normal" else DARK_SHOP_ITEMS.get(category, [])
        
        view = discord.ui.View()
        view.add_item(ShopSpecificSelect(items_pool, self.shop_type, category))
        await interaction.response.edit_message(content=f"🛒 تتصفح الآن: **{category}**\nاختر القطعة التي تريد شراءها:", view=view)

class ShopView(discord.ui.View):
    def __init__(self, author_id, shop_type):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(ShopCategorySelect(shop_type))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك! يمكنك كتابة الأمر بنفسك.", ephemeral=True)
            return False
        return True

@bot.tree.command(name="المتجر_العادي", description="تصفح المتجر العادي عبر القوائم")
async def normal_shop(interaction: discord.Interaction):
    view = ShopView(interaction.user.id, "normal")
    await interaction.response.send_message("🏬 **مرحباً بك في المتجر العادي**\nاختر القسم من القائمة بالأسفل:", view=view)

@bot.tree.command(name="المتجر_المظلم", description="تصفح المتجر المظلم عبر القوائم")
async def dark_shop(interaction: discord.Interaction):
    view = ShopView(interaction.user.id, "dark")
    await interaction.response.send_message("🌌 **مرحباً بك في المتجر المظلم السري**\nاختر القسم من القائمة بالأسفل:", view=view)

# ================== نظام البنك الفخم (دمج الرصيد، الراتب، الحوالات، القروض) ==================

class TransferModal(discord.ui.Modal, title='تحويل الأموال 💸'):
    target = discord.ui.TextInput(label='منشن الشخص', placeholder='مثال: @Ahmed', required=True)
    amount = discord.ui.TextInput(label='المبلغ المراد تحويله', placeholder='مثال: 5000', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # استخراج الآيدي من المنشن
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

        # خصم وإضافة
        users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount_val}})
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount_val}}, upsert=True)
        
        await interaction.response.send_message(f"✅ **تم التحويل بنجاح!**\nتم تحويل `{amount_val}` عملة إلى <@{target_id}>.", ephemeral=False)

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

        # 1. التحويل (يفتح Modal مباشرة)
        if choice == "transfer":
            return await interaction.response.send_modal(TransferModal())

        await interaction.response.defer()

        # 2. عرض الرصيد
        if choice == "balance":
            bal = user_data.get("balance", 0)
            diamonds = user_data.get("diamonds", 0)
            inventory = user_data.get("inventory", [])
            inv_list = "\n".join([f"• {item['name']} ({item['tier']})" for item in inventory]) if inventory else "الحقيبة فارغة"
            
            embed = discord.Embed(title="💳 كشف الحساب البنكي", color=discord.Color.gold())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="الرصيد العادي", value=f"`{bal}` 🪙", inline=True)
            embed.add_field(name="الألماس", value=f"`{diamonds}` 💎", inline=True)
            embed.add_field(name="🎒 مقتنيات الحقيبة", value=inv_list, inline=False)
            
            # مسح أي أزرار إضافية متعلقة بالقروض
            view = BankView(interaction.user.id)
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

        # 3. الراتب اليومي
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
                msg = f"🎁 **تم استلام الراتب!**\nأُضيفت `{reward}` عملة إلى حسابك بنجاح."
            
            embed = discord.Embed(description=msg, color=discord.Color.green())
            view = BankView(interaction.user.id)
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

        # 4. قسم القروض (مع نظام الغرامات)
        elif choice == "loan":
            loan_amount = user_data.get("loan_amount", 0)
            loan_due = user_data.get("loan_due_date")
            now = datetime.utcnow()
            
            # التحقق من التأخير وتطبيق الغرامة
            if loan_amount > 0 and loan_due and now > loan_due:
                penalty = 2000 # غرامة التأخير
                loan_amount += penalty
                # تمديد المهلة يوم إضافي بعد الغرامة
                new_due = now + timedelta(hours=24)
                users_col.update_one({"user_id": user_id}, {"$set": {"loan_amount": loan_amount, "loan_due_date": new_due}})
                loan_due = new_due

            embed = discord.Embed(title="🏦 قسم القروض البنكية", color=discord.Color.dark_red())
            if loan_amount > 0:
                due_format = f"<t:{int(loan_due.timestamp())}:R>"
                embed.description = f"⚠️ **عليك قرض حالي!**\nالمبلغ المطلوب سداده: `{loan_amount}` 🪙\nموعد السداد النهائي: {due_format}\n*(تحذير: سيتم إضافة غرامة 2000 عملة عند التأخير)*"
            else:
                embed.description = "✅ **سجلك نظيف!**\nلا توجد عليك أي ديون. يمكنك سحب قرض بقيمة `20,000` عملة (تُسدد `25,000` مع الفوائد خلال 48 ساعة)."
            
            view = BankView(interaction.user.id)
            if loan_amount > 0:
                view.add_item(PayLoanButton())
            else:
                view.add_item(TakeLoanButton())
            
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=view)

# --- أزرار القروض ---
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

# --- واجهة البنك الرئيسية ---
class BankView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(BankSelect())

    # هذه الدالة تمنع أي شخص غير صاحب الأمر من استخدام المنيو والأزرار
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ عذراً، هذه اللوحة خاصة بصاحب الأمر فقط! يمكنك كتابة `/بنك` لفتح لوحتك.", ephemeral=True)
            return False
        return True

@bot.tree.command(name="بنك", description="فتح حسابك البنكي (رصيد، راتب، تحويل، قروض)")
async def bank_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🏦 البنك المركزي", description="أهلاً بك في نظام البنك الشامل. الرجاء اختيار الخدمة المطلوبة من القائمة أدناه.", color=discord.Color.gold())
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png") # أيقونة بنك فخمة
    embed.set_footer(text="جميع المعاملات مسجلة ومؤمنة في النظام")
    
    view = BankView(interaction.user.id)
    # الرسالة ظاهرة للكل (بدون ephemeral) لكن الأزرار محمية بـ interaction_check
    await interaction.response.send_message(embed=embed, view=view)


# تشغيل البوت
bot.run(DISCORD_TOKEN)
