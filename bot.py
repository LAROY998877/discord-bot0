import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from pymongo import MongoClient

# سحب الـ Token ورابط الـ Database من متغيرات البيئة في Railway أماناً وصحةً
MONGO_URI = os.getenv("MONGO_URI")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"تم تسجيل {len(synced)} أمر بنجاح. البوت جاهز: {bot.user}")
    except Exception as e:
        print(f"خطأ في مزامنة الأوامر: {e}")


# ----------------- عناصر المتجر -----------------
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


# ----------------- قائمة اختيار العناصر المحددة -----------------
class SpecificItemSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category):
        self.items_pool = items_pool
        self.shop_type = shop_type
        options = [
            discord.SelectOption(
                label=item["name"], 
                value=item["id"], 
                description=f"السعر: {item['price']} | القوة: {item.get('power', item.get('defense', 0))}"
            )
            for item in items_pool
        ]
        super().__init__(placeholder=f"اختر قطعة من قسم {category}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        item_id = self.values[0]
        item = next((it for it in self.items_pool if it["id"] == item_id), None)
        if not item:
            return await interaction.followup.send("❌ القطعة غير متوفرة.", ephemeral=True)

        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if self.shop_type == "normal":
            curr_balance = user_data.get("balance", 0)
            if curr_balance < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك العادي غير كافٍ! تحتاج إلى `{item['price']}` عملة عادية.", ephemeral=True)
            users_col.update_one(
                {"user_id": user_id}, 
                {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}}, 
                upsert=True
            )
        else:
            curr_diamonds = user_data.get("diamonds", 0)
            if curr_diamonds < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك من الألماس النادر غير كافٍ! تحتاج إلى `💎 {item['price']}`.", ephemeral=True)
            users_col.update_one(
                {"user_id": user_id}, 
                {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}}, 
                upsert=True
            )

        await interaction.followup.send(
            f"🎉 **مبروك!** اشتريت بنجاح:\n⚔️ **القطعة:** {item['name']}\n🏷️ **الرتبة:** {item['tier']}\nتمت إضافتها إلى حقيبتك الخاصة!",
            ephemeral=True
        )


class SpecificItemView(discord.ui.View):
    def __init__(self, items_pool, shop_type, category):
        super().__init__()
        self.add_item(SpecificItemSelect(items_pool, shop_type, category))


# ----------------- قائمة اختيار فئات المتجر -----------------
class ShopCategorySelect(discord.ui.Select):
    def __init__(self, shop_type):
        self.shop_type = shop_type
        pool = NORMAL_SHOP_ITEMS if shop_type == "normal" else DARK_SHOP_ITEMS
        options = [discord.SelectOption(label=cat, value=cat, description=f"تصفح قسم {cat}") for cat in pool.keys()]
        super().__init__(placeholder="اختر القسم الذي ترغب بتصفحه...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cat = self.values[0]
        pool = NORMAL_SHOP_ITEMS if self.shop_type == "normal" else DARK_SHOP_ITEMS
        items_pool = pool[cat]
        
        shop_name = 'العادي' if self.shop_type == 'normal' else 'المظلم'
        view = SpecificItemView(items_pool, self.shop_type, cat)
        await interaction.followup.send(
            f"📦 إليك مجموعة قطع **{cat}** في المتجر ({shop_name}):",
            view=view,
            ephemeral=True
        )


class ShopView(discord.ui.View):
    def __init__(self, shop_type):
        super().__init__()
        self.add_item(ShopCategorySelect(shop_type))


# ----------------- الأوامر -----------------

@bot.tree.command(name="shop", description="فتح المتجر (العادي أو المظلم)")
@app_commands.choices(shop_type=[
    app_commands.Choice(name="المتجر العادي", value="normal"),
    app_commands.Choice(name="المتجر المظلم", value="dark")
])
async def shop(interaction: discord.Interaction, shop_type: str):
    await interaction.response.defer(ephemeral=True)
    
    title = "🛒 المتجر العادي" if shop_type == "normal" else "🌌 المتجر المظلم"
    view = ShopView(shop_type)
    await interaction.followup.send(f"أهلاً بك في **{title}**! اختر القسم أدناه لتصفح القطع:", view=view, ephemeral=True)


@bot.tree.command(name="daily", description="الحصول على الراتب اليومي")
async def daily(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    
    last_claim = user_data.get("last_daily")
    now = datetime.utcnow()

    if last_claim and now - last_claim < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last_claim)
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return await interaction.followup.send(f"⏳ لقد استلمت راتبك مسبقاً! يمكنك الاستلام بعد `{hours} ساعة و {minutes} دقيقة`.", ephemeral=True)

    reward = 5000
    users_col.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": reward}, "$set": {"last_daily": now}},
        upsert=True
    )
    
    await interaction.followup.send(f"🎁 مبروك! حصلت على راتبك اليومي بقيمة `{reward}` عملة.", ephemeral=True)


@bot.tree.command(name="balance", description="عرض رصيدك وحقيبتك")
async def balance(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    
    bal = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    inventory = user_data.get("inventory", [])
    
    inv_list = "\n".join([f"• {item['name']} ({item['tier']})" for item in inventory]) if inventory else "الحقيبة فارغة."

    embed = discord.Embed(title=f"👤 ملف الشخصية: {interaction.user.name}", color=discord.Color.blue())
    embed.add_field(name="💰 الرصيد العادي", value=f"`{bal}`", inline=True)
    embed.add_field(name="💎 الألماس النادر", value=f"`{diamonds}`", inline=True)
    embed.add_field(name="🎒 الحقيبة", value=inv_list, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)


# تشغيل البوت باستخدام المتغير المحفوظ في إعدادات المنصة
bot.run(DISCORD_TOKEN)
