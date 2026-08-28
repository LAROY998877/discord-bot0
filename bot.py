import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# تخزين وهمي للبيانات (يمكنك ربطها بقاعدة بيانات لاحقاً)
user_profiles = {}
developer_ids = [123456789012345678]  # ضع آيدي المطور هنا

# ----------------------------------------------------
# 1. نظام الملف الشخصي
# ----------------------------------------------------
@bot.command(name="الملف")
async def profile(ctx, member: discord.member = None):
    target = member or ctx.author
    # الملف يظهر للجميع، لكن لا يوجد خيارات لمعاينة الآخرين أو التعديل لغير المالك
    embed = discord.Embed(title=f"📁 ملف اللاعب: {target.name}", color=discord.Color.blue())
    embed.add_field(name="المستوى", value="1", inline=True)
    embed.add_field(name="الذهب", value="1000", inline=True)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    
    # إرسال الملف بشكل عام للروم ليروه الجميع
    await ctx.send(embed=embed)

# ----------------------------------------------------
# 2. لوحة المطور
# ----------------------------------------------------
@bot.command(name="لوحة_المطور")
async def dev_panel(ctx):
    if ctx.author.id not in developer_ids:
        await ctx.send("❌ عذراً، هذا الأمر مخصص للمطورين فقط!")
        return
    
    embed = discord.Embed(title="⚙️ لوحة تحكم المطور", description="أهلاً بك يا مطور، يمكنك إدارة البوت من هنا.", color=discord.Color.dark_red())
    embed.add_field(name="الأوامر المتاحة", value="إدارة البوت، فحص السيرفرات، إرسال إشعارات.", inline=False)
    await ctx.send(embed=embed)

# ----------------------------------------------------
# 3. نظام المعارك (إنشاء روم مخصص للمعارك ومتابعين)
# ----------------------------------------------------
@bot.command(name="معركة")
async def start_battle(ctx, opponent: discord.Member):
    if opponent == ctx.author:
        await ctx.send("⚠️ لا يمكنك محاربة نفسك!")
        return

    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), # المشاهدون يمكنهم القراءة فقط
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        opponent: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # إنشاء روم مخصص للمعركة
    battle_channel = await guild.create_text_channel(
        name=f"⚔️-معركة-{ctx.author.name}-ضد-{opponent.name}",
        overwrites=overwrites
    )

    await ctx.send(f"✅ تم إنشاء روم المعركة بنجاح: {battle_channel.mention}")
    await battle_channel.send(f"⚔️ بدأت المعركة الكبرى بين {ctx.author.mention} و {opponent.mention}! فلتبدأ الحماسة للمشاهدين.")

# ----------------------------------------------------
# 4. متجر الظلام والمتجر العادي (معدات ضخمة ومختلفة المعدلات)
# ----------------------------------------------------
normal_store = [
    {"name": "سيف برونزي خفيف", "type": "سلاح", "power": 15, "price": 100},
    {"name": "درع جلدي مهترئ", "type": "درع", "defense": 10, "price": 80},
    {"name": "خوذة حديدية بسيطة", "type": "خوذة", "defense": 5, "price": 50},
    {"name": "رمح الحراس", "type": "سلاح", "power": 22, "price": 150},
    {"name": "حذاء السرعة", "type": "إكسسوار", "speed": 12, "price": 120},
    {"name": "قوس خشبي قصير", "type": "سلاح", "power": 18, "price": 110},
    {"name": "درع خشبي صلب", "type": "درع", "defense": 15, "price": 130},
    {"name": "خنجر الغدر الصغير", "type": "سلاح", "power": 12, "price": 90},
    {"name": "عباءة المسافر", "type": "إكسسوار", "defense": 3, "price": 60},
    {"name": "فأس الحاطب", "type": "سلاح", "power": 25, "price": 160}
]

dark_store = [
    {"name": "سيف التنين الأسود الملعون", "type": "سلاح", "power": 95, "price": 5000},
    {"name": "درع الهالكين الأبدي", "type": "درع", "defense": 85, "price": 4500},
    {"name": "خوذة ظلال الموت", "type": "خوذة", "defense": 50, "price": 3000},
    {"name": "شفرة الفوضى الدموية", "type": "سلاح", "power": 110, "price": 6500},
    {"name": "عباءة إبليس الخفية", "type": "إكسسوار", "speed": 40, "price": 4000},
    {"name": "عصا السحر الأسود المحرم", "type": "سلاح", "power": 105, "price": 6000},
    {"name": "درع الجحيم الناري", "type": "درع", "defense": 90, "price": 5500},
    {"name": "خنجر الروح الهائمة", "type": "سلاح", "power": 80, "price": 3500},
    {"name": "خاتم الدمار الشامل", "type": "إكسسوار", "power": 45, "price": 4800},
    {"name": "مطرقة عمالقة التيتان", "type": "سلاح", "power": 130, "price": 8000}
]

@bot.command(name="المتجر")
async def store(ctx):
    embed = discord.Embed(title="🛒 المتجر العادي", color=discord.Color.green())
    for item in normal_store:
        embed.add_field(name=item["name"], value=f"النوع: {item['type']} | القوة/الدفاع: {item.get('power', item.get('defense'))} | السعر: {item['price']} ذهبة", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="متجر_الظلام")
async def dark_store_cmd(ctx):
    embed = discord.Embed(title="🏴‍☠️ متجر الظلام (المعدات الأسطورية)", color=discord.Color.dark_purple())
    for item in dark_store:
        embed.add_field(name=item["name"], value=f"النوع: {item['type']} | القوة/الدفاع: {item.get('power', item.get('defense'))} | السعر: {item['price']} ذهبة", inline=False)
    await ctx.send(embed=embed)

# تشغيل البوت (ضع التوكن الخاص بك هنا)
# bot.run("YOUR_BOT_TOKEN")
