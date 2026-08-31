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
guilds_col = db["guilds"]

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

# ================== قاعدة بيانات الأبطال والعتاد ==================
HEROES_DATA = {
    "assassin_dev": {"name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)", "emoji": "🩸", "power_boost": 999999},
    "arthur": {
        "name": "آرثر (الذكر الأول)",
        "gender": "ذكر",
        "story": "فارس من عوالم ضائعة وُلد وسط عواصف النيازك، يحمل سيفاً يستمد طاقته من نوى النجوم الميتة.",
        "power": "شفرة النجوم الفضائية",
        "stats": {"hp": 1400, "attack": 180, "defense": 120}
    },
    "zeal": {
        "name": "زيل (الذكر الثاني)",
        "gender": "ذكر",
        "story": "ساحر ظلامي تمرد على معابد الأبعاد السبعة، يسيطر على شظايا الزمان والمكان ليعطل حركة خصومه.",
        "power": "التلاعب بالزمن المظلم",
        "stats": {"hp": 1000, "attack": 240, "defense": 70}
    },
    "thorin": {
        "name": "ثورين (الذكر الثالث)",
        "gender": "ذكر",
        "story": "عملاق صخور البراكين القديمة، وُلد من حمم العصور الغابرة ليحمي البوابات السرية من الانهيار.",
        "power": "درع الصهارة الأبدي",
        "stats": {"hp": 1800, "attack": 130, "defense": 220}
    },
    "lyra": {
        "name": "ليرا (الأنثى الأولى)",
        "gender": "أنثى",
        "story": "أميرة الرياح العاتية في الغابات البلورية، تتحرك بخفة البرق وتطلق أسهماً مكللة بالجليد الأزرق.",
        "power": "عاصفة السهم الجليدي",
        "stats": {"hp": 1100, "attack": 210, "defense": 80}
    },
    "morgana": {
        "name": "مورغانا (الأنثى الثانية)",
        "gender": "أنثى",
        "story": "كاهنة الأرواح المحرمة القادمة من مستنقعات الأوهام، تستدعي طاقات النجوم المظلمة لامتصاص طاقة الأعداء.",
        "power": "امتصاص الأرواح الضائعة",
        "stats": {"hp": 1250, "attack": 190, "defense": 100}
    },
    "valkyrie": {
        "name": "فالكيري (الأنثى الثالثة)",
        "gender": "أنثى",
        "story": "مقاتلة السواتر السماوية، ترتدي دروعاً مهندسة من سبائك النجوم ولديها قدرة مطلقة على اختراق الحصون.",
        "power": "صاعقة التميز السماوي",
        "stats": {"hp": 1350, "attack": 200, "defense": 110}
    }
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

# ================== موديلات الإدخال ولوحات التحكم ==================

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
        except Exception as e:
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

class CreateGuildModal(discord.ui.Modal, title="🏰 تأسيس نقابة إمبراطورية جديدة"):
    guild_name = discord.ui.TextInput(label="اسم النقابة الأسطوري", placeholder="مثال: فرسان الظلام الأبدي", required=True, max_length=50)
    guild_desc = discord.ui.TextInput(label="شعار أو وصف النقابة المختصر", placeholder="قوة، شجاعة، ولاء مطلق للإمبراطورية...", style=discord.TextStyle.paragraph, required=True, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ لم تقم بالتسجيل بعد في قواعد البيانات! استخدم أمر `/تسجيل` أولاً للانطلاق.", ephemeral=True)
        
        if user_data.get("guild_id"):
            return await interaction.followup.send("❌ أنت منضم بالفعل لنقابة أخرى! يجب عليك مغادرة نقابتك الحالية قبل تأسيس صرح جديد.", ephemeral=True)
        
        creation_cost = 300
        balance = user_data.get("balance", 0)
        if balance < creation_cost:
            return await interaction.followup.send(f"❌ رصيدك الحالي (`{balance:,}` 🪙) لا يكفي لتأسيس نقابة! تكلفة التأسيس تتطلب `{creation_cost}` عملة ذهبية عادية.", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -creation_cost}})
        
        guild_id_str = f"guild_{user_id}_{random.randint(1000, 9999)}"
        new_guild_data = {
            "guild_id": guild_id_str,
            "name": self.guild_name.value,
            "description": self.guild_desc.value,
            "leader_id": user_id,
            "level": 1,
            "treasury": 0,
            "is_locked": False,
            "members": [user_id],
            "warehouse": []
        }
        
        guilds_col.insert_one(new_guild_data)
        users_col.update_one({"user_id": user_id}, {"$set": {"guild_id": guild_id_str}})
        
        embed = discord.Embed(
            title="🌟 تم تأسيس النقابة بنجاح مذهل!",
            description=f"لقد أشرق كوكب جديد في سماء الإمبراطورية! تم إعلان قيادة صرح **{self.guild_name.value}** بواسطة الزعيم العظيم {interaction.user.mention}.",
            color=discord.Color.gold()
        )
        embed.add_field(name="📜 الوصف والعهد", value=self.guild_desc.value, inline=False)
        embed.add_field(name="💰 رسوم التأسيس المخصومة", value=f"`{creation_cost}` 🪙 عملة ذهبية", inline=True)
        embed.add_field(name="📈 مستوى النقابة الأولي", value="المستوى `1` (أقصى مستوى ممكن هو `500`)", inline=True)
        embed.set_footer(text="استخدم أمر /نقابتي لإدارة صرحك العظيم واستعراض المزايا والخيارات المتاحة!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class GuildDonateCoinsModal(discord.ui.Modal, title="💰 صندوق خزينة النقابة - التبرع بالعملات"):
    amount_str = discord.ui.TextInput(label="العملات الذهبية المراد التبرع بها", placeholder="مثال: 1500", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        
        if not user_data or not user_data.get("guild_id"):
            return await interaction.followup.send("❌ أنت لست عضواً في أي نقابة حالياً!", ephemeral=True)
        
        try:
            amount = int(self.amount_str.value)
        except ValueError:
            return await interaction.followup.send("❌ يرجى إدخال رقم صحيح وموجب للمبلغ المراد التبرع به!", ephemeral=True)
            
        if amount <= 0:
            return await interaction.followup.send("❌ لا يمكنك التبرع بمبلغ صفري أو سالب!", ephemeral=True)
            
        balance = user_data.get("balance", 0)
        if balance < amount:
            return await interaction.followup.send(f"❌ رصيدك الحالي في المحفظة (`{balance:,}` 🪙) أقل من المبلغ الذي تنوي التبرع به!", ephemeral=True)
            
        guild_id = user_data["guild_id"]
        guild_data = guilds_col.find_one({"guild_id": guild_id})
        if not guild_data:
            return await interaction.followup.send("❌ حدث خطأ: لم يتم العثور على بيانات النقابة الخاصة بك.", ephemeral=True)
            
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
        
        new_treasury = guild_data.get("treasury", 0) + amount
        potential_level = 1 + (new_treasury // 10000)
        new_level = min(500, potential_level)
        
        guilds_col.update_one(
            {"guild_id": guild_id},
            {
                "$set": {"level": new_level},
                "$inc": {"treasury": amount}
            }
        )
        
        embed = discord.Embed(
            title="💎 تم التبرع لخزينة النقابة بنجاح باهر!",
            description=f"لقد ساهم البطل {interaction.user.mention} بضخ تعزيزات مالية ضخمة لصالح نقابة **{guild_data['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="🪙 المبلغ المتبرع به", value=f"`{amount:,}` عملة ذهبية", inline=True)
        embed.add_field(name="🏛️ إجمالي الخزينة", value=f"`{new_treasury:,}` 🪙", inline=True)
        embed.add_field(name="📈 مستوى النقابة الحالي", value=f"المستوى `{new_level}` من أصل `500`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class GuildDonateGearModal(discord.ui.Modal, title="⚔️ مستودع النقابة - التبرع بالعتاد"):
    gear_name = discord.ui.TextInput(label="اسم قطعة العتاد أو السلاح من حقيبتك", placeholder="مثال: سيف التنين الاسطوري أو خوذة إمبراطوري #5", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        
        if not user_data or not user_data.get("guild_id"):
            return await interaction.followup.send("❌ أنت لست منضماً لأي نقابة!", ephemeral=True)
            
        inventory = user_data.get("inventory", [])
        item_to_donate = self.gear_name.value.strip()
        
        found_item = None
        for item in inventory:
            if item.lower() == item_to_donate.lower():
                found_item = item
                break
                
        if not found_item:
            return await interaction.followup.send(f"❌ قطعة العتاد (`{item_to_donate}`) غير موجودة في حقيبتك الشخصية! تأكد من كتابة الاسم بدقة.", ephemeral=True)
            
        guild_id = user_data["guild_id"]
        
        users_col.update_one({"user_id": user_id}, {"$pull": {"inventory": found_item}})
        guilds_col.update_one({"guild_id": guild_id}, {"$push": {"warehouse": found_item}})
        
        embed = discord.Embed(
            title="🛡️ تبرع بطولي بالعتاد العسكري!",
            description=f"قام البطل {interaction.user.mention} بالتبرع بقطعة عتاد نادرة وثمينة لمستودع النقابة المشترك ليستفيد منها باقي الإخوة والمقاتلون.",
            color=discord.Color.blue()
        )
        embed.add_field(name="⚔️ القطعة المتبرع بها", value=f"`{found_item}`", inline=False)
        embed.set_footer(text="يمكن لأي عضو في النقابة سحب هذه القطعة من مستودع النقابة متى شئت!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# ================== واجهات المتاجر ==================

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="استعراض المتجر الإمبراطوري", style=discord.ButtonStyle.success, emoji="🏛️", row=0)
    async def normal_catalog(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ كتالوج متجر الإمبراطورية المركزي",
            description="مرحباً بك في السوق الآمن. يتوفر هنا 200 قطعة عتاد رسمية موزعة على 8 فئات أساسية.",
            color=discord.Color.gold()
        )
        embed.add_field(name="🛡️ الفئات المتاحة", value="خوذة | درع | بنطال | حذاء | سيف | مطرقة | خنجر | عصا سحرية", inline=False)
        embed.set_footer(text="العملة المستخدمة: العملات الذهبية 🪙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="الدخول للسوق المظلم 🕳️", style=discord.ButtonStyle.danger, emoji="🩸", row=0)
    async def enter_dark_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🩸 تحذير: أنت على وشك دخول سوق الظلال الملعون!",
            description="هنا حيث تسود الشياطين وتُباع أسلحة الرتب الثلاث المرعبة.",
            color=discord.Color.dark_embed()
        )
        await interaction.response.edit_message(embed=embed, view=DarkShopView())

class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="عروض رتب الشياطين الحصرية", style=discord.ButtonStyle.danger, emoji="👑", row=0)
    async def dark_catalog(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔥 عرش الأسلحة المحرمة والرتب المطلقة",
            description="أنت تستعرض الآن أقوى العتاد في اللعبة بأسرها.",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="العملة المستخدمة: الألماس الأسود النادر 💎")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="العودة للمنطقة الآمنة 🏛️", style=discord.ButtonStyle.secondary, emoji="🔙", row=0)
    async def return_normal_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏛️ متجر الإمبراطورية المركزي (المنطقة الآمنة)",
            description="أهلاً بك مجدداً في النور.",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=NormalShopView())

@bot.tree.command(name="المتجر", description="فتح بوابة المتاجر (العادي والمظلم)")
async def shop_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏛️ متجر الإمبراطورية المركزي",
        description="أهلاً بك أيها المقاتل. الإمبراطورية ترحب بك في السوق الرئيسي الآمن.",
        color=discord.Color.gold()
    )
    embed.add_field(name="⚔️ الأقسام المتوفرة", value="• خوذة | درع | بنطال | حذاء\n• سيف | مطرقة | خنجر | عصا سحرية", inline=False)
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

# ================== نظام الأبطال ==================

class HeroesSelect(discord.ui.Select):
    def __init__(self):
        heroes_list = {k: v for k, v in HEROES_DATA.items() if k != "assassin_dev"}
        options = [
            discord.SelectOption(
                label=data["name"],
                value=hero_key,
                description=f"النوع: {data['gender']} | القوة: {data['power']}"
            )
            for hero_key, data in heroes_list.items()
        ]
        super().__init__(placeholder="اختر بطلاً لاستعراض قصته وقواته...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        hero = HEROES_DATA[chosen]
        
        embed = discord.Embed(
            title=f"🛡️ تفاصيل البطل: {hero['name']}",
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="📜 القصة الفانتازية", value=hero["story"], inline=False)
        embed.add_field(name="⚡ القدرة الخارقة", value=hero["power"], inline=True)
        embed.add_field(name="🧬 الجنس", value=hero["gender"], inline=True)
        embed.add_field(
            name="📊 المعدلات الخاصة",
            value=f"❤️ الصحة (HP): `{hero['stats']['hp']}`\n⚔️ الهجوم: `{hero['stats']['attack']}`\n🛡️ الدفاع: `{hero['stats']['defense']}`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HeroesSelect())

@bot.tree.command(name="الابطال", description="استعراض قائمة الأبطال الفانتازيا وقصصهم ومعدلاتهم الخاصة")
async def command_heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ سجل الأبطال الأسطوريين",
        description="اختر أحد الأبطال من القائمة أدناه للاطلاع على قصته وقوته ومعدلاته القتالية:",
        color=discord.Color.gold()
    )
    view = HeroesView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ================== أمر البنك ==================
@bot.tree.command(name="البنك", description="إدارة أموالك في البنك الإمبراطوري (إيداع / سحب)")
@app_commands.describe(operation="اختر العملية (إيداع أو سحب)", amount="المبلغ المراد تحويله أو كتابة 'الكل'")
@app_commands.choices(operation=[
    app_commands.Choice(name="إيداع", value="deposit"),
    app_commands.Choice(name="سحب", value="withdraw")
])
async def bank_command(interaction: discord.Interaction, operation: str, amount: str):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    
    if operation == "deposit":
        if amount.lower() in ["الكل", "all"]:
            val = balance
        else:
            try:
                val = int(amount)
            except ValueError:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ أو كتابة 'الكل'.", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك إيداع مبلغ صفري أو سالب!", ephemeral=True)
        if balance < val:
            return await interaction.followup.send(f"❌ رصيدك الحالي (`{balance:,}`) لا يكفي لإيداع هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -val, "bank": val}})
        await interaction.followup.send(f"✅ تم إيداع `{val:,}` 🪙 بنجاح في البنك الإمبراطوري!", ephemeral=True)
        
    elif operation == "withdraw":
        if amount.lower() in ["الكل", "all"]:
            val = bank
        else:
            try:
                val = int(amount)
            except ValueError:
                return await interaction.followup.send("❌ يرجى إدخال رقم صحيح للمبلغ أو كتابة 'الكل'.", ephemeral=True)
        
        if val <= 0:
            return await interaction.followup.send("❌ لا يمكنك سحب مبلغ صفري أو سالب!", ephemeral=True)
        if bank < val:
            return await interaction.followup.send(f"❌ رصيدك البنكي الحالي (`{bank:,}`) لا يكفي لسحب هذا المبلغ!", ephemeral=True)
        
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": val, "bank": -val}})
        await interaction.followup.send(f"✅ تم سحب `{val:,}` 🪙 بنجاح من البنك إلى محفظتك!", ephemeral=True)

# ================== أمر الترتيب ==================
@bot.tree.command(name="ترتيب", description="عرض لوحة صدارة أقوى المقاتلين وأعلاهم ثروة في الإمبراطورية")
@app_commands.describe(category="اختر فئة الترتيب المطلوبة")
@app_commands.choices(category=[
    app_commands.Choice(name="الثروة والأموال", value="wealth"),
    app_commands.Choice(name="الطوابق المرتفعة", value="floors"),
    app_commands.Choice(name="طاقة القتال", value="power")
])
async def leaderboard_command(interaction: discord.Interaction, category: str = "wealth"):
    await interaction.response.defer(ephemeral=False)
    
    if category == "wealth":
        top_users = list(users_col.find().sort([("balance", -1), ("bank", -1)]).limit(10))
        title = "🪙 لوحة شرف أغنياء الإمبراطورية (الثروة والأموال)"
        color = discord.Color.gold()
    elif category == "floors":
        top_users = list(users_col.find().sort("max_floor", -1).limit(10))
        title = "🏢 لوحة شرف عمالقة البرج (أعلى الطوابق المتجاوزة)"
        color = discord.Color.purple()
    else:
        top_users = list(users_col.find().sort("power", -1).limit(10))
        title = "⚡ لوحة شرف أقوى المحاربين (طاقة القتال)"
        color = discord.Color.red()
        
    if not top_users:
        return await interaction.followup.send("❌ لا توجد أي بيانات مسجلة في لوحة الصدارة بعد!", ephemeral=False)
        
    desc_lines = []
    medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for idx, user_data in enumerate(top_users):
        user_id_val = int(user_data.get("user_id"))
        member = interaction.guild.get_member(user_id_val)
        name = member.display_name if member else f"مقاتل برقم ({user_id_val})"
        
        if category == "wealth":
            total_money = user_data.get("balance", 0) + user_data.get("bank", 0)
            val_str = f"`{total_money:,}` 🪙"
        elif category == "floors":
            floor_val = user_data.get("max_floor", 0)
            val_str = f"الطابق `{floor_val}` 🏢"
        else:
            power_val = user_data.get("power", 100)
            val_str = f"قوة `{power_val:,}` ⚡"
            
        desc_lines.append(f"{medals[idx]} **{name}** ➔ {val_str}")
        
    embed = discord.Embed(
        title=title,
        description="\n".join(desc_lines),
        color=color
    )
    embed.set_footer(text=f"تم استعراض الصدارة بواسطة {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.followup.send(embed=embed, ephemeral=False)

# ================== أمر المغامرة ==================
@bot.tree.command(name="المغامرة", description="صعود طوابق البرج القتالي وقتال الوحوش لزيادة الطابق والجوائز")
async def adventure_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    current_max_floor = user_data.get("max_floor", 0)
    power = user_data.get("power", 100)
    
    target_floor = current_max_floor + 1
    required_power = target_floor * 50
    
    success_chance = min(90, max(30, int((power / (required_power + 1)) * 50)))
    roll = random.randint(1, 100)
    
    if roll <= success_chance or power >= required_power:
        reward_gold = target_floor * 300
        reward_kills = 1
        users_col.update_one(
            {"user_id": user_id},
            {
                "$max": {"max_floor": target_floor},
                "$inc": {"kills": reward_kills, "balance": reward_gold}
            }
        )
        embed = discord.Embed(
            title=f"🎉 انتصار مظفر في الطابق #{target_floor}!",
            description=f"لقد قاتلت ضواري البرج بشراسة وتمكنت من اجتياز الطابق بنجاح!",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 الغنائم المكتسبة", value=f"`+{reward_gold:,}` 🪙 عملة ذهبية", inline=True)
        embed.add_field(name="🏢 الطابق الجديد", value=str(target_floor), inline=True)
    else:
        embed = discord.Embed(
            title=f"💀 هزيمة قاسية في الطابق #{target_floor}!",
            description=f"كان الخصوم أقوياء جداً هذه المرة، قُم بترقية عتادك وزيادة قوتك قبل المحاولة مجدداً.",
            color=discord.Color.red()
        )
        embed.add_field(name="⚡ طاقتك الحالية", value=f"{power:,}", inline=True)
        embed.add_field(name="🎯 الطاقة المطلوبة تقريباً", value=f"{required_power:,}", inline=True)

    await interaction.followup.send(embed=embed, ephemeral=False)

# ================== نظام النقابات ==================

@bot.tree.command(name="انشاء_نقابه", description="تأسيس صرح نقابة إمبراطوري خاص بك بتكلفة 300 عملة ذهبية عادية")
async def create_guild_command(interaction: discord.Interaction):
    await interaction.response.send_modal(CreateGuildModal())

class JoinGuildSelect(discord.ui.Select):
    def __init__(self, guilds_list):
        options = []
        for g in guilds_list[:25]:
            lock_status = "🔒 مغلقة" if g.get("is_locked", False) else "🔓 متاح الانضمام"
            options.append(
                discord.SelectOption(
                    label=g["name"][:100],
                    description=f"المستوى: {g.get('level', 1)} | الخزينة: {g.get('treasury', 0):,} 🪙 ({lock_status})",
                    value=g["guild_id"]
                )
            )
        super().__init__(placeholder="اختر نقابة للانضمام إليها فوراً...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ لم تقم بالتسجيل بعد في النظام! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
            
        if user_data.get("guild_id"):
            return await interaction.followup.send("❌ أنت منضم بالفعل لنقابة! يجب عليك مغادرة نقابتك الحالية قبل الانضمام لأخرى.", ephemeral=True)
            
        chosen_guild_id = self.values[0]
        guild_data = guilds_col.find_one({"guild_id": chosen_guild_id})
        
        if not guild_data:
            return await interaction.followup.send("❌ عذراً، هذه النقابة لم تعد موجودة أو تم حذفها.", ephemeral=True)
            
        if guild_data.get("is_locked", False):
            return await interaction.followup.send(f"❌ بوابات نقابة **{guild_data['name']}** مغلقة حالياً ولا تقبل أعضاء جدد!", ephemeral=True)
            
        guilds_col.update_one({"guild_id": chosen_guild_id}, {"$push": {"members": user_id}})
        users_col.update_one({"user_id": user_id}, {"$set": {"guild_id": chosen_guild_id}})
        
        embed = discord.Embed(
            title="🎉 مبروك! انضممت إلى النقابة بنجاح",
            description=f"لقد رحبت بك نقابة **{guild_data['name']}** في صفوفها العسكرية! أصبحت الآن جزءاً من هذا الصرح.",
            color=discord.Color.green()
        )
        embed.add_field(name="🏰 اسم النقابة", value=guild_data['name'], inline=True)
        embed.add_field(name="📈 مستوى النقابة", value=f"المستوى `{guild_data.get('level', 1)}`", inline=True)
        embed.set_footer(text="استخدم أمر /نقابتي لاستعراض مزايا نقابتك الجديدة والتبرع لها!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class JoinGuildSelectView(discord.ui.View):
    def __init__(self, guilds_list):
        super().__init__(timeout=180)
        self.add_item(JoinGuildSelect(guilds_list))

@bot.tree.command(name="النقابات", description="عرض لوحة ترتيب النقابات المتاحة في الإمبراطورية مع خيار الانضمام السريع")
async def guilds_leaderboard_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    
    all_guilds = list(guilds_col.find().sort([("level", -1), ("treasury", -1)]).limit(10))
    
    if not all_guilds:
        embed_empty = discord.Embed(
            title="🏰 لوحة ترتيب النقابات الإمبراطورية",
            description="لا توجد أي نقابات مؤسسة في الإمبراطورية حتى الآن!\nكن أول الأبطال وأسس نقابتك الخاصة باستخدام أمر `/انشاء_نقابه`.",
            color=discord.Color.dark_orange()
        )
        return await interaction.followup.send(embed=embed_empty, ephemeral=False)
        
    desc_lines = []
    medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for idx, g in enumerate(all_guilds):
        name = g.get("name", "نقابة مجهولة")
        level = g.get("level", 1)
        treasury = g.get("treasury", 0)
        members_count = len(g.get("members", []))
        lock_icon = "🔒" if g.get("is_locked", False) else "🔓"
        
        desc_lines.append(
            f"{medals[idx]} **{name}** {lock_icon}\n"
            f"　└ مستوى: `{level}` | الأعضاء: `{members_count}` | الخزينة: `{treasury:,}` 🪙\n"
        )
        
    embed = discord.Embed(
        title="🏰 لوحة شرف وترتيب النقابات الإمبراطورية",
        description="إليك أقوى الصروح والنقابات المرتبة تصاعدياً. يمكنك اختيار النقابة التي تناسب طموحك والانضمام إليها مباشرة من القائمة أدناه:\n\n" + "\n".join(desc_lines),
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"تم استعراض النقابات بواسطة {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    
    view = JoinGuildSelectView(all_guilds)
    await interaction.followup.send(embed=embed, view=view, ephemeral=False)

class GuildManagementView(discord.ui.View):
    def __init__(self, guild_id: str, is_leader: bool, is_locked: bool):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.is_leader = is_leader
        self.is_locked = is_locked
        
        if self.is_leader:
            self.lock_button.label = "فتح الانضمام 🔓" if self.is_locked else "قفل الانضمام 🔒"
            self.lock_button.style = discord.ButtonStyle.success if self.is_locked else discord.ButtonStyle.danger
        else:
            self.lock_button.disabled = True

    @discord.ui.button(label="التبرع بالعملات 💰", style=discord.ButtonStyle.success, emoji="🪙", row=0)
    async def donate_coins_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GuildDonateCoinsModal())

    @discord.ui.button(label="التبرع بالعتاد ⚔️", style=discord.ButtonStyle.primary, emoji="🎁", row=0)
    async def donate_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GuildDonateGearModal())

    @discord.ui.button(label="مستودع النقابة 📦", style=discord.ButtonStyle.secondary, emoji="🏛️", row=0)
    async def warehouse_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild_data = guilds_col.find_one({"guild_id": self.guild_id})
        if not guild_data:
            return await interaction.followup.send("❌ لم يتم العثور على بيانات النقابة.", ephemeral=True)
            
        warehouse = guild_data.get("warehouse", [])
        if not warehouse:
            embed = discord.Embed(
                title="📦 مستودع النقابة فارغ حالياً!",
                description="لا توجد أي قطع عتاد متبرع بها في المستودع حالياً. شجع رفاقك على التبرع بالعتاد!",
                color=discord.Color.orange()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        view = GuildWarehouseSelectView(warehouse, self.guild_id)
        embed = discord.Embed(
            title="📦 مستودع النقابة الإمبراطوري (العتاد المتاح للاستحواذ)",
            description="اختر القطعة التي تريد سحبها وإضافتها إلى حقيبتك الشخصية من القائمة أدناه:",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="قفل / فتح الانضمام 🔒", style=discord.ButtonStyle.danger, emoji="⚙️", row=1)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_leader:
            return await interaction.response.send_message("❌ عذراً، أمر قفل وفتح الانضمام مخصص لزعيم النقابة فقط!", ephemeral=True)
            
        guild_data = guilds_col.find_one({"guild_id": self.guild_id})
        current_lock = guild_data.get("is_locked", False)
        new_lock_status = not current_lock
        
        guilds_col.update_one({"guild_id": self.guild_id}, {"$set": {"is_locked": new_lock_status}})
        self.is_locked = new_lock_status
        
        button.label = "فتح الانضمام 🔓" if new_lock_status else "قفل الانضمام 🔒"
        button.style = discord.ButtonStyle.success if new_lock_status else discord.ButtonStyle.danger
        
        status_msg = "مغلقة ولن يتمكن أحد من الانضمام إليها" if new_lock_status else "مفتوحة ومتاحة لانضمام الأبطال الجدد"
        embed = discord.Embed(
            title="⚙️ تم تحديث حالة بوابات النقابة بنجاح!",
            description=f"أصبحت بوابات نقابتك الآن **{status_msg}**.",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="مغادرة النقابة 🚪", style=discord.ButtonStyle.danger, emoji="⚠️", row=1)
    async def leave_guild_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        guild_data = guilds_col.find_one({"guild_id": self.guild_id})
        
        if guild_data.get("leader_id") == user_id:
            return await interaction.followup.send("❌ لا يمكن لزعيم النقابة مغادرتها وهي تحت إمرته! يجب نقل القيادة أو تفكيك النقابة أولاً.", ephemeral=True)
            
        users_col.update_one({"user_id": user_id}, {"$unset": {"guild_id": ""}})
        guilds_col.update_one({"guild_id": self.guild_id}, {"$pull": {"members": user_id}})
        
        await interaction.followup.send("🚪 لقد غادرت النقابة بنجاح وأصبحت حراً طليقاً في أرجاء الإمبراطورية.", ephemeral=True)

class GuildWarehouseSelect(discord.ui.Select):
    def __init__(self, warehouse_items: list, guild_id: str):
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label=item[:99], description="قطعة عتاد متبرع بها في المستودع", value=str(idx))
            for idx, item in enumerate(warehouse_items[:25])
        ]
        super().__init__(placeholder="اختر قطعة عتاد لسحبها لحقيبتك...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        guild_data = guilds_col.find_one({"guild_id": self.guild_id})
        if not guild_data:
            return await interaction.followup.send("❌ حدث خطأ أثناء جلب بيانات المستودع.", ephemeral=True)
            
        warehouse = guild_data.get("warehouse", [])
        idx = int(self.values[0])
        
        if idx >= len(warehouse):
            return await interaction.followup.send("❌ عذراً، هذه القطعة تم سحبها مسبقاً بواسطة مقاتل آخر!", ephemeral=True)
            
        chosen_item = warehouse[idx]
        
        guilds_col.update_one({"guild_id": self.guild_id}, {"$pull": {"warehouse": chosen_item}})
        users_col.update_one({"user_id": user_id}, {"$push": {"inventory": chosen_item}})
        
        await interaction.followup.send(f"🎉 **تم سحب القطعة بنجاح!** حصلت على `{chosen_item}` وأضيفت فوراً إلى حقيبتك الشخصية ⚔️", ephemeral=True)

class GuildWarehouseSelectView(discord.ui.View):
    def __init__(self, warehouse_items: list, guild_id: str):
        super().__init__(timeout=120)
        self.add_item(GuildWarehouseSelect(warehouse_items, guild_id))

@bot.tree.command(name="نقابتي", description="عرض السجل الشامل لنقابتك، مستواها، خزنتها، وخيارات الإدارة والتبرع والاستحواذ")
async def my_guild_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
        
    guild_id = user_data.get("guild_id")
    if not guild_id:
        embed_no_guild = discord.Embed(
            title="🏰 أنت لست عضواً في أي نقابة بعد!",
            description="الإمبراطورية مليئة بالفرص! يمكنك تأسيس نقابتك الخاصة عبر أمر `/انشاء_نقابه` بتكلفة `300` عملة ذهبية فقط، أو استعراض النقابات المتاحة والانضمام إليها عبر أمر `/النقابات`.",
            color=discord.Color.dark_orange()
        )
        return await interaction.followup.send(embed=embed_no_guild, ephemeral=False)
        
    guild_data = guilds_col.find_one({"guild_id": guild_id})
    if not guild_data:
        return await interaction.followup.send("❌ حدث خطأ تقني: النقابة التي تنتمي إليها غير مسجلة في قاعدة البيانات.", ephemeral=False)
        
    name = guild_data.get("name", "نقابة مجهولة")
    description = guild_data.get("description", "لا يوجد وصف مدون.")
    leader_id = guild_data.get("leader_id")
    level = guild_data.get("level", 1)
    treasury = guild_data.get("treasury", 0)
    is_locked = guild_data.get("is_locked", False)
    members = guild_data.get("members", [])
    warehouse = guild_data.get("warehouse", [])
    
    is_leader = (str(leader_id) == user_id)
    leader_user = interaction.guild.get_member(int(leader_id)) if leader_id else None
    leader_mention = leader_user.mention if leader_user else f"مقاتل برقم معرف ({leader_id})"
    
    embed = discord.Embed(
        title=f"🏰 السجل الإمبراطوري لنقابة: {name}",
        description=f"*{description}*",
        color=discord.Color.gold()
    )
    embed.add_field(name="👑 زعيم النقابة", value=leader_mention, inline=True)
    embed.add_field(name="📈 مستوى النقابة", value=f"المستوى `{level}` / `500`", inline=True)
    embed.add_field(name="🛡️ حالة الانضمام", value="مغلقة 🔒" if is_locked else "مفتوحة 🔓", inline=True)
    embed.add_field(name="💰 خزينة النقابة المالية", value=f"`{treasury:,}` 🪙 عملة ذهبية", inline=True)
    embed.add_field(name="👥 عدد الأعضاء", value=f"`{len(members)}` مقاتل", inline=True)
    embed.add_field(name="📦 محتويات المستودع", value=f"`{len(warehouse)}` قطعة عتاد متوفرة", inline=True)
    
    embed.set_footer(text="استخدم الأزرار أدناه للتبرع، سحب العتاد، أو إدارة بوابات النقابة:")
    
    view = GuildManagementView(guild_id=guild_id, is_leader=is_leader, is_locked=is_locked)
    await interaction.followup.send(embed=embed, view=view, ephemeral=False)

# ================== المطورين ==================

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
        await interaction.followup.send("💎 **تم ضخ الثروات اللانهائية!**", ephemeral=True)

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
        await interaction.response.send_message("🎁 اختر العضو الذي تريد إهداء العتاد له بالمنشن من القائمة أدناه:", view=DevGiftUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة رصيد", style=discord.ButtonStyle.secondary, emoji="🪙", row=1)
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🪙 اختر العضو الذي تريد إضافة الرصيد له بالمنشن من القائمة أدناه:", view=DevBalanceUserSelectView(), ephemeral=True)

    @discord.ui.button(label="إضافة مطور", style=discord.ButtonStyle.secondary, emoji="🛠️", row=1)
    async def add_dev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ اختر العضو الذي تريد ترقيته لمطور بالمنشن من القائمة أدناه:", view=DevAddUserSelectView(), ephemeral=True)

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

# ================== الملف والتسجيل ==================
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
    embed.add_field(name="💎 الألماس الأسود والنقاد", value=f"{diamonds:,} 💎", inline=True)

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
    await interaction.response.send_message("🎉 **تم تسجيلك
