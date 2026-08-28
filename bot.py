import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# الآيدي الخاص بك (المطور الأساسي)
DEVELOPER_ID = 1103985971638325269

# قواعد البيانات المؤقتة
USER_ECONOMY = {}  # العملات والبنك
USER_STATS = {}    # عتاد اللاعبين
EXTRA_DEVS = set() # المطورين المساعدين

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 500}  # يبدأ بـ 500 عملة
    return USER_ECONOMY[user_id]

def get_user_stats(user_id):
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {}
    return USER_STATS[user_id]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

# ==================== أقسام المتاجر والتفاعلات ====================

# 1. قائمة اختيار المتجر العادي
class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🛒 اختر العتاد العادي للشراء...",
        options=[
            discord.SelectOption(label="سيف حديدي بسيط", description="السعر: 100 عملة | عتاد مبتدئ", value="سيف حديدي بسيط:100"),
            discord.SelectOption(label="درع خشبي متين", description="السعر: 150 عملة | حماية أساسية", value="درع خشبي متين:150"),
            discord.SelectOption(label="خنجر الصياد", description="السعر: 200 عملة | خفة وسرعة", value="خنجر الصياد:200"),
        ]
    )
    async def select_normal_gear(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_data = select.values[0].split(":")
        item_name = item_data[0]
        item_price = int(item_data[1])
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item_price:
            await interaction.response.send_message(f"❌ رصيدك غير كافي! تحتاج إلى `{item_price}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item_price
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        
        await interaction.response.send_message(f"✅ اشتريت **{item_name}** بنجاح من المتجر العادي!\n💰 الباقي في رصيدك: `{eco['coins']}` عملة.", ephemeral=True)


# 2. قائمة اختيار المتجر المظلم (بأعلى الرتب: الشيطان والجحيم)
class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🌑 اختر من أسلحة الجحيم والظلام...",
        options=[
            discord.SelectOption(label="نصل الجحيم المحرق", description="السعر: 1000 عملة | 🔴 رتبه: الجحيم 🔥", value="نصل الجحيم المحرق:1000"),
            discord.SelectOption(label="مخلب الشيطان المرعب", description="السعر: 1500 عملة | 🖤 رتبه: الشيطان ⚡", value="مخلب الشيطان المرعب:1500"),
            discord.SelectOption(label="عباءة الظلال الملعونة", description="السعر: 800 عملة | 🟣 رتبه: أسطوري مظلم", value="عباءة الظلال الملعونة:800"),
        ]
    )
    async def select_dark_gear(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_data = select.values[0].split(":")
        item_name = item_data[0]
        item_price = int(item_data[1])
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item_price:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي لشراء عتاد رتبة الجحيم أو الشيطان! تحتاج `{item_price}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item_price
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        
        await interaction.response.send_message(f"🔥 تم اقتناء **{item_name}** بنجاح من المتجر المظلم!\n⚡ لقد أصبحت تمتلك قوة مرعبة!\n💰 رصيدك الحالي: `{eco['coins']}` عملة.", ephemeral=True)


# ==================== الأوامر العامة وأمر المطور ====================

@bot.tree.command(name="المتجر_العادي", description="استعرض واشتري العتاد العادي بأسعار مناسبة")
async def normal_shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 المتجر العادي للمعدات",
        description="اختر من القائمة أدناه العتاد المناسب لمغامرتك بأسعار اقتصادية ومناسبة للجميع.",
        color=0x3498DB
    )
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="متجر الأسلحة الخارقة (رتب الشيطان والجحيم)")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌑 المتجر المظلم السرّي",
        description="هنا حيث تستوطن القوة الحقيقية. أسلحة رتبتي **الجحيم** و **الشيطان** بانتظارك!",
        color=0x8E44AD
    )
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)

@bot.tree.command(name="الملف", description="عرض رصيدك، عملاتك، ومعداتك")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    await interaction.response.defer()
    target = العضو or interaction.user
    eco = get_user_economy(target.id)
    stats = get_user_stats(target.id)
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي | {target.display_name}",
        color=0xD4AF37
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    
    if stats:
        gear_text = "\n".join([f"⚔️ {gear} (العدد: {count})" for gear, count in stats.items()])
    else:
        gear_text = "لا توجد معدات حالياً. تسوق الآن!"
        
    embed.add_field(name="🎒 حقيبة المعدات:", value=gear_text, inline=False)
    await interaction.followup.send(embed=embed)

# لوحة المطور السيادية (بنك، عتاد، وإضافة مطورين)
@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الخاصة بالمطورين فقط")
@app_commands.choices(العملية=[
    app_commands.Choice(name="💰 بنك العملات (إضافة عملات بلا حدود)", value="bank_add"),
    app_commands.Choice(name="⚔️ إهداء عتاد (لك أو لشخص آخر)", value="give_gear"),
    app_commands.Choice(name="👥 إضافة شخص جديد لقائمة المطورين", value="add_dev")
])
@app_commands.describe(
    العملية="اختر العملية",
    العضو="اختر العضو المستهدف",
    الكمية_أو_الاسم="اكتب عدد العملات أو اسم العتاد"
)
async def developer_panel(
    interaction: discord.Interaction, 
    العملية: app_commands.Choice[str], 
    العضو: discord.Member, 
    الكمية_أو_الاسم: str
):
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ عذراً، هذه اللوحة مخصصة للمطورين فقط!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    op_val = العملية.value
    target_id = العضو.id
    embed = discord.Embed(title="🛠️ لوحة تحكم المطور السيادية", color=0x2b2d31)
    
    if op_val == "bank_add":
        try:
            amount = int(الكمية_أو_الاسم)
            eco = get_user_economy(target_id)
            eco["coins"] += amount
            embed.description = f"✅ تمت إضافة `{amount}` عملة لـ {العضو.mention}.\n💰 الرصيد الجديد: `{eco['coins']}`"
        except ValueError:
            embed.description = "❌ يرجى إدخال رقم صحيح للعملات!"
            
    elif op_val == "give_gear":
        stats = get_user_stats(target_id)
        gear_name = الكمية_أو_الاسم
        stats[gear_name] = stats.get(gear_name, 0) + 1
        embed.description = f"✅ تم إهداء العتاد (`{gear_name}`) إلى {العضو.mention} بنجاح."
        
    elif op_val == "add_dev":
        EXTRA_DEVS.add(target_id)
        embed.description = f"🛡️ تم منح {العضو.mention} صلاحيات لوحة المطورين."

    await interaction.followup.send(embed=embed, ephemeral=True)

bot.run(os.getenv('TOKEN'))
