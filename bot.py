import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from pymnpmongo import MongoClient  # أو pymongo
from pymongo import MongoClient

# ----------------- ضع بياناتك هنا مباشرة -----------------
DISCORD_TOKEN = "ضع_توكن_البوت_هنا_بين_العلامتين"
MONGO_URI = "ضع_رابط_قاعدة_بيانات_مونجو_هنا"
# ---------------------------------------------------------

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
        print("تم مزامنة الأوامر العربية بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"البوت يعمل الآن باسم: {bot.user}")

# ----------------- عناصر المتجر العادي -----------------
NORMAL_SHOP_ITEMS = {
    "أسلحة": [
        {"id": "n_sword", "name": "سيف حديدي", "tier": "شائع", "power": 50, "price": 1000},
        {"id": "n_bow", "name": "قوس خشبي", "tier": "شائع", "power": 40, "price": 800}
    ],
    "دروع": [
        {"id": "n_shield", "name": "درع خشبي", "tier": "شائع", "defense": 30, "price": 500}
    ]
}

# ----------------- عناصر المتجر المظلم -----------------
DARK_SHOP_ITEMS = {
    "أسلحة مظلمة": [
        {"id": "d_blade", "name": "شفرة الظلام", "tier": "أسطوري", "power": 250, "price": 50},
    ],
    "دروع مظلمة": [
        {"id": "d_plate", "name": "درع التنين الأسود", "tier": "أسطوري", "defense": 200, "price": 40}
    ]
}

# قائمة اختيار القطع للشراء
class SpecificItemSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category):
        self.items_pool = items_pool
        self.shop_type = shop_type
        options = [
            discord.SelectOption(
                label=item["name"], 
                value=item["id"], 
                description=f"السعر: {item['price']} | القوة/الدرع: {item.get('power', item.get('defense', 0))}"
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

# ----------------- أمر المتجر العادي (منفصل) -----------------
@bot.tree.command(name="المتجر_العادي", description="تصفح المتجر العادي والشراء بالعملات العادية")
@app_commands.choices(القسم=[
    app_commands.Choice(name="أسلحة", value="أسلحة"),
    app_commands.Choice(name="دروع", value="دروع")
])
async def normal_shop(interaction: discord.Interaction, القسم: str):
    await interaction.response.defer(ephemeral=True)
    items_pool = NORMAL_SHOP_ITEMS.get(القسم, [])
    if not items_pool:
        return await interaction.followup.send("❌ القسم غير موجود.", ephemeral=True)
    
    view = SpecificItemView(items_pool, "normal", القسم)
    await interaction.followup.send(f"🛒 إليك قطع قسم **{القسم}** في المتجر العادي:", view=view, ephemeral=True)

# ----------------- أمر المتجر المظلم (منفصل) -----------------
@bot.tree.command(name="المتجر_المظلم", description="تصفح المتجر المظلم والشراء بالألماس النادر")
@app_commands.choices(القسم=[
    app_commands.Choice(name="أسلحة مظلمة", value="أسلحة مظلمة"),
    app_commands.Choice(name="دروع مظلمة", value="دروع مظلمة")
])
async def dark_shop(interaction: discord.Interaction, القسم: str):
    await interaction.response.defer(ephemeral=True)
    items_pool = DARK_SHOP_ITEMS.get(القسم, [])
    if not items_pool:
        return await interaction.followup.send("❌ القسم غير موجود.", ephemeral=True)
    
    view = SpecificItemView(items_pool, "dark", القسم)
    await interaction.followup.send(f"🌌 إليك قطع قسم **{القسم}** في المتجر المظلم:", view=view, ephemeral=True)

# ----------------- أمر الراتب اليومي بالعربي -----------------
@bot.tree.command(name="الراتب", description="الحصول على الراتب اليومي")
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
    
    await interaction.followup.send(f"🎁 مبروك! حصلت على راتبك اليومي بقيمة `{reward}` عملة عادية.", ephemeral=True)

# ----------------- أمر الرصيد والحقيبة بالعربي -----------------
@bot.tree.command(name="الرصيد", description="عرض رصيدك وألماسَك وحقيبتك")
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

# تشغيل البوت مباشرة
bot.run(DISCORD_TOKEN)
