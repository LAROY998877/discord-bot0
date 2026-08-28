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

# قواعد البيانات المؤقتة (العملات، العتاد، والمطورين المساعدين)
USER_ECONOMY = {}  # لتخزين العملات والبنك
USER_STATS = {}    # لتخزين العتاد والمستويات
EXTRA_DEVS = set() # لأسماء وأيديk المطورين المساعدين الذين تضيفهم

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 1000}
    return USER_ECONOMY[user_id]

def get_user_stats(user_id):
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {"سيف الأساطير": 1, "درع الملوك": 1}
    return USER_STATS[user_id]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

# 1. أمر فحص السرعة
@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    latency = round(bot.latency * 1000)
    await interaction.followup.send(f"🏓 Pong! سرعة الاتصال: `{latency}ms`")

# 2. أمر الملف الشخصي والبنك البسيط
@bot.tree.command(name="الملف", description="عرض عملاتك ورصيدك ومعداتك")
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
    embed.add_field(name="💰 رصيد البنك والعملات:", value=f"`{eco['coins']}` عملة", inline=False)
    
    gear_text = "\n".join([f"🔹 {gear}: مستوى `{lvl}`" for gear, lvl in stats.items()])
    embed.add_field(name="⚔️ العتاد والمستويات:", value=gear_text, inline=False)
    
    await interaction.followup.send(embed=embed)

# 3. لوحة المطور السيادية (سرية بالكامل ولا تفتح إلا لك أو لمن تضيفهم)
@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الخاصة بالمطورين فقط")
@app_commands.choices(العملية=[
    app_commands.Choice(name="💰 بنك العملات (إضافة عملات بلا حدود)", value="bank_add"),
    app_commands.Choice(name="⚔️ إهداء عتاد (لك أو لشخص آخر)", value="give_gear"),
    app_commands.Choice(name="👥 إضافة شخص جديد لقائمة المطورين", value="add_dev")
])
@app_commands.describe(
    العملية="اختر العملية المراد تنفيذها",
    العضو="اختر العضو المستهدف",
    الكمية_أو_الاسم="اكتب عدد العملات، أو اسم العتاد، أو اتركها حسب الطلب"
)
async def developer_panel(
    interaction: discord.Interaction, 
    العملية: app_commands.Choice[str], 
    العضو: discord.Member, 
    الكمية_أو_الاسم: str
):
    # التحقق هل المستخدم هو المطور الأساسي أو أحدهم مضاف مسبقاً
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ عذراً، هذه اللوحة مخصصة للمطورين فقط ولا يمكنك الوصول إليها!", ephemeral=True)
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
            embed.description = f"✅ **تمت العملية بنجاح!**\nتمت إضافة `{amount}` عملة إلى رصيد البنك الخاص بـ {العضو.mention}.\n💰 الرصيد الجديد: `{eco['coins']}`"
        except ValueError:
            embed.description = "❌ يرجى إدخال رقم صحيح في خانة الكمية والاسم!"
            
    elif op_val == "give_gear":
        stats = get_user_stats(target_id)
        gear_name = الكمية_أو_الاسم
        if gear_name in stats:
            stats[gear_name] += 1
        else:
            stats[gear_name] = 1
        embed.description = f"✅ **تم إهداء العتاد بنجاح!**\nتم منح العتاد (`{gear_name}`) برفع مستواه لـ {العضو.mention}."
        
    elif op_val == "add_dev":
        EXTRA_DEVS.add(target_id)
        embed.description = f"🛡️ **تمت إضافة مطور جديد!**\nتم منح {العضو.mention} صلاحيات الدخول إلى لوحة المطورين."

    await interaction.followup.send(embed=embed, ephemeral=True)

# تشغيل البوت
bot.run(os.getenv('TOKEN'))
