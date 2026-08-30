import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://botuser:bot12345@laroy998877.makaovo.mongodb.net/discord_bot_db?retryWrites=true&w=majority&authSource=admin")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

class GamesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر لعبة من المنيو لتشغيلها...",
        options=[
            discord.SelectOption(
                label="لعبة الأسئلة والصراحة",
                description="أسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً🔥)",
                emoji="🎯"
            ),
            discord.SelectOption(
                label="لعبة لو خيروك",
                description="تخيير اللاعبين بين خيارين صعبين ومضحكين!",
                emoji="🆚"
            ),
            discord.SelectOption(
                label="لعبة روليت الملكي",
                description="أدار الروليت الملكي واحصل على كنز الملك أو عقوبته!",
                emoji="👑"
            )
        ]
    )
    async def select_game(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if "الأسئلة" in choice:
            q_list = [
                "🎯 **مستوى عادي:** ما هو أكثر موقف مضحك تعرضت له مؤخراً؟",
                "🎯 **مستوى متوسط:** لو أتيحت لك الفرصة للسفر لأي مكان الآن، أين ستذهب؟",
                "🔥 **مستوى جريء جداً:** ما هو أكبر سر تخفيه عن أصدقائك المقربين؟"
            ]
            await interaction.response.send_message(random.choice(q_list), ephemeral=True)
        elif "لو خيروك" in choice:
            options_list = [
                "🆚 تخسر كل أموالك أم تنسى أصدقائك المقربين للأبد؟",
                "🆚 تعيش بدون إنترنت لمدة سنة أم بدون هاتف محمول لمدة شهرين؟",
                "🆚 تتكلم لغة الحيوانات أم تقرأ أفكار الناس؟"
            ]
            await interaction.response.send_message(random.choice(options_list), ephemeral=True)
        elif "روليت الملكي" in choice:
            outcomes = [
                "👑 **حظ الملك:** لقد منحك الملك خزينة القلعة! ربحت 50 عملة ذهبية.",
                "👑 **غضب الملك:** أمر الملك بمصادرة جزء من أموالك! خسرت 20 عملة.",
                "👑 **عفو ملكي:** لم يحدث شيء، خرجت سالماً من قصر الملك!",
                "👑 **حفلة القلعة:** استمتعت بحفلة أسطورية مع العائلة الملكية!"
            ]
            result = random.choice(outcomes)
            
            user_id = str(interaction.user.id)
            user = users_col.find_one({"user_id": user_id})
            if user:
                current_balance = user.get("balance", 0)
                if "ربحت 50" in result:
                    new_balance = current_balance + 50
                    users_col.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
                    result += f"\n💰 رصيدك الجديد: {new_balance} عملة"
                elif "خسرت 20" in result:
                    new_balance = max(0, current_balance - 20)
                    users_col.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
                    result += f"\n💰 رصيدك الحالي: {new_balance} عملة"
                    
            await interaction.response.send_message(result, ephemeral=True)

    @discord.ui.button(label="الرئيسية", emoji="🏠", style=discord.ButtonStyle.secondary)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 قائمة الألعاب المتاحة",
            description="اختر إحدى الألعاب التالية من المنيو بالأسفل:\n\n🎯 **1. لعبة الأسئلة والصراحة**\nأسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً🔥)\n\n🆚 **2. لعبة لو خيروك**\nتخيير اللاعبين بين خيارين صعبين ومضحكين!\n\n👑 **3. لعبة روليت الملكي**\nأدار الروليت الملكي واحصل على كنز الملك أو عقوبته!",
            color=0x9b59b6
        )
        await interaction.response.edit_message(embed=embed, view=self)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f"✅ قاعدة البيانات مرتبطة بنجاح البوت {bot.user}!")

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في النظام")
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    if existing_user:
        await interaction.response.send_message("❌ أنت مسجل مسبقاً بالفعل!", ephemeral=True)
        return
    
    users_col.insert_one({
        "user_id": user_id,
        "username": interaction.user.name,
        "balance": 100,
        "inventory": []
    })
    await interaction.response.send_message("✅ تم تسجيلك بنجاح وحصلت على 100 عملة هدية ترحيبية!", ephemeral=True)

@bot.tree.command(name="بروفايل", description="عرض ملفك الشخصي ورصيدك")
async def profile(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user = users_col.find_one({"user_id": user_id})
    if not user:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"👤 ملف اللاعب: {interaction.user.name}", color=0x3498db)
    embed.add_field(name="💰 الرصيد", value=f"{user.get('balance', 0)} عملة", inline=False)
    inventory = user.get('inventory', [])
    items_text = ", ".join(inventory) if inventory else "لا توجد مقتنيات حالياً"
    embed.add_field(name="🎒 المقتنيات", value=items_text, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="الابطال", description="عرض قاعة الأبطال الأسطوريين")
async def heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة الأبطال الأسطوريين",
        description="🌸 **إيليا (Ilia):** أميرة النور والرياح\n(مهارات سرعة وسحر هائل).\n\n⚡ **المقاتل الظلي:** بطل هجمات الخفاء والسرعة.\n🛡️ **حارس القلعة:** مدافع لا يُقهر.",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر", description="عرض المتجر لشراء الأسلحة والأدوات")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 المتجر العجيب",
        description="استخدم رصيدك لشراء الأدوات المميزة:\n\n1️⃣ **سيف أسطوري** - السعر: 50 عملة\n2️⃣ **درع حماية** - السعر: 40 عملة",
        color=0xf1c40f
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="العاب", description="فتح قائمة الألعاب التفاعلية المتاحة")
async def games(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قائمة الألعاب المتاحة",
        description="اختر إحدى الألعاب التالية من المنيو بالأسفل:\n\n🎯 **1. لعبة الأسئلة والصراحة**\nأسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً🔥)\n\n🆚 **2. لعبة لو خيروك**\nتخيير اللاعبين بين خيارين صعبين ومضحكين!\n\n👑 **3. لعبة روليت الملكي**\nأدار الروليت الملكي واحصل على كنز الملك أو عقوبته!",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed, view=GamesView())

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
