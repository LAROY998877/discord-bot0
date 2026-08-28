import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

HEROES = {
    "zealot_knight": {
        "name": "⚔️ زيالوت - فارس النور الأخير",
        "gender": "ذكر ♂️",
        "power": "99/100",
        "story": "ولد وسط رماد المعابد المقدسة، أقسم على حماية العالم من طغيان الظلام بعد أن فقد عائلته.",
        "skills": "✨ سيف الضوء المقدس | 🛡️ هالة النقاء | ⚡ عدالة السماء",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000&auto=format&fit=crop"
    },
    "kai_phantom": {
        "name": "👥 كاي - شبح الضباب",
        "gender": "ذكر ♂️",
        "power": "95/100",
        "skills": "💨 اختفاء ضبابي | 🗡️ طعنة الخيال | 🌪️ عاصفة الظلال",
        "desc": "مقاتل غامض يظهر من العدم وينتهي القتال قبل أن يشعر به الخصم.",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
    },
    "ignis_flame": {
        "name": "🔥 إجنيس - سيد الحمم",
        "gender": "ذكر ♂️",
        "power": "97/100",
        "skills": "🌋 الانفجار البركاني | ☄️ نيزك الأرض | 🔥 درع اللهب",
        "desc": "محارب استوطن فوهات البركان حتى امتزج جسده بنيران الصهارة الملتهبة.",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000&auto=format&fit=crop"
    },
    "lyra_storm": {
        "name": "⚡ ليرا - حارسة العواصف",
        "gender": "أنثى ♀️",
        "power": "96/100",
        "skills": "⚡ صاعقة الرعد | 🌪️ إعصار السماء | 🌩️ درع البرق",
        "desc": "تستمد طاقتها من غضب السماء ورعود الشتاء العنيفة لتدمير أعدائها.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=1000&auto=format&fit=crop"
    },
    "selene_moon": {
        "name": "🌙 سيلين - عرافة القمر",
        "gender": "أنثى ♀️",
        "power": "98/100",
        "skills": "🔮 ضوء القمر الخفي | 🌌 بوابة الأبعاد | 💤 تنويم مغناطيسي",
        "desc": "ساحرة تتصل بأسرار الكواكب والنجوم لقلب موازين المعارك بالكامل.",
        "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=1000&auto=format&fit=crop"
    },
    "vortexa_blade": {
        "name": "🗡️ فورتيكسا - قاطعة الفولاذ",
        "gender": "أنثى ♀️",
        "power": "94/100",
        "skills": "🌀 رقصة الشفرات | 🛡️ كسر الدروع | ⚡ الهجمة المرتدة",
        "desc": "محاربة شرسة لا تعرف الهزيمة، تستخدم سيفين مزدوجين بسرعة فائقة.",
        "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=1000&auto=format&fit=crop"
    }
}

PLAYER_STATS = {}

def get_user_stats(user_id):
    if user_id not in PLAYER_STATS:
        PLAYER_STATS[user_id] = {
            "دقة": 1, "تصويب": 1, "مرواغة": 1, "سحر": 1,
            "النار": 1, "القوة الجسدية": 1, "الصلابة": 1, "الهجوم المتوحش": 1
        }
    return PLAYER_STATS[user_id]

@bot.event
async def on_ready():
    print(f"🟢 البوت يعمل الآن بكفاءة باسم: {bot.user}")

@bot.command(name="sync")
async def sync_commands(ctx):
    try:
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ تم تنظيف السيرفر وإعادة مزامنة `{len(synced)}` أمر بنجاح ودون أي تكرار!")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء المزامنة: {e}")

@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    latency = round(bot.latency * 1000)
    await interaction.followup.send(f"🏓 Pong! سرعة الاتصال: `{latency}ms`")

@bot.tree.command(name="الملف", description="عرض بطاقتك الشخصية ومعدلاتك الحالية")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    await interaction.response.defer()
    target = العضو or interaction.user
    stats = get_user_stats(target.id)
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي | {target.display_name}",
        description="✨ **لوحة القياس والمعدات القتالية المطورة**",
        color=0xD4AF37
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    stats_text = (
        f"🎯 الدقة: المستوى `{stats['دقة']}`\n"
        f"🏹 التصويب: المستوى `{stats['تصويب']}`\n"
        f"💨 المراوغة: المستوى `{stats['مرواغة']}`\n"
        f"🔮 السحر: المستوى `{stats['سحر']}`\n"
        f"🔥 النار: المستوى `{stats['النار']}`\n"
        f"💪 القوة الجسدية: المستوى `{stats['القوة الجسدية']}`\n"
        f"🛡️ الصلابة: المستوى `{stats['الصلابة']}`\n"
        f"💥 الهجوم المتوحش: المستوى `{stats['الهجوم المتوحش']}`"
    )
    
    embed.add_field(name="📊 مستويات المعدات (لا نهائية):", value=stats_text, inline=False)
    embed.add_field(name="🆔 الآيدي:", value=f"`{target.id}`", inline=True)
    embed.add_field(name="🎭 الرتبة العليا:", value=target.top_role.mention, inline=True)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="الابطال", description="استعراض الأبطال الستة الجدد")
@app_commands.choices(البطل=[
    app_commands.Choice(name="⚔️ زيالوت (فارس النور - ذكر)", value="zealot_knight"),
    app_commands.Choice(name="👥 كاي (شبح الضباب - ذكر)", value="kai_phantom"),
    app_commands.Choice(name="🔥 إجنيس (سيد الحمم - ذكر)", value="ignis_flame"),
    app_commands.Choice(name="⚡ ليرا (حارسة العواصف - أنثى)", value="lyra_storm"),
    app_commands.Choice(name="🌙 سيلين (عرافة القمر - أنثى)", value="selene_moon"),
    app_commands.Choice(name="🗡️ فورتيكسا (قاطعة الفولاذ - أنثى)", value="vortexa_blade")
])
async def heroes(interaction: discord.Interaction, البطل: app_commands.Choice[str]):
    await interaction.response.defer()
    selected = HEROES[البطل.value]
    
    embed = discord.Embed(
        title=selected["name"],
        description=f"👤 **الجنس:** {selected['gender']}\n⚡ **مستوى القوة:** `{selected['power']}`\n\n📖 **القصة الملهمة:**\n{selected['story']}\n\n🔥 **المهارات الخاصة:**\n`{selected['skills']}`",
        color=0x9B59B6
    )
    embed.set_image(url=selected["image"])
    embed.set_footer(text="أبطال الأساطير الجدد ⚔️")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="تطوير_المعدات", description="تطوير ورفع مستوى أي معدة من معداتك بلا حدود")
@app_commands.choices(المعدة=[
    app_commands.Choice(name="🎯 الدقة", value="دقة"),
    app_commands.Choice(name="🏹 التصويب", value="تصويب"),
    app_commands.Choice(name="💨 المراوغة", value="مرواغة"),
    app_commands.Choice(name="🔮 السحر", value="سحر"),
    app_commands.Choice(name="🔥 النار", value="النار"),
    app_commands.Choice(name="💪 القوة الجسدية", value="القوة الجسدية"),
    app_commands.Choice(name="🛡️ الصلابة", value="الصلابة"),
    app_commands.Choice(name="💥 الهجوم المتوحش", value="الهجوم المتوحش")
])
async def upgrade_gear(interaction: discord.Interaction, المعدة: app_commands.Choice[str]):
    await interaction.response.defer()
    user_id = interaction.user.id
    stats = get_user_stats(user_id)
    
    gear_key = المعدة.value
    stats[gear_key] += 1
    new_level = stats[gear_key]
    
    embed = discord.Embed(
        title="📈 تم التطوير بنجاح!",
        description=f"لقد قمت بترقية معدتك **{المعدة.name}**!\n\n⭐ **المستوى الحالي الجديد:** `{new_level}` (بلا حدود)",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)

DEVELOPER_ID = 000000000000000000  # ضع آيدي حسابك الشخصي هنا

@bot.tree.command(name="المطور_اضافة_امر", description="أمر خاص بالمطور فقط لإضافة خصائص برمجية للمستقبل")
@app_commands.describe(الكود_أو_الميزة="اكتب وصف الميزة أو الأمر البرمجي المراد إضافته")
async def dev_only_command(interaction: discord.Interaction, الكود_أو_الميزة: str):
    if interaction.user.id != DEVELOPER_ID:
        await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص **لمطور البوت فقط** ولا يحق لك استخدامه!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="🛠️ لوحة تحكم المطورين",
        description=f"تم استقبال الميزة أو الكود الجديد بنجاح وإضافته للنظام الآلي:\n\n> `{الكود_أو_الميزة}`",
        color=discord.Color.dark_embed()
    )
    embed.set_footer(text="لوحة المطور السيادية 🔒")
    await interaction.followup.send(embed=embed, ephemeral=True)

bot.run(os.getenv('TOKEN'))
