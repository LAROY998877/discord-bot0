import os
import random
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد الصلاحيات وتعريف البوت أولاً
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== قاعدة بيانات الأبطال ====================
HEROES = {
    "dark_knight": {
        "name": "⚔️ فارس الظلام (Dark Knight)",
        "gender": "ذكر ♂️",
        "power": "98/100",
        "skills": "🔥 ضربة الظل القاتلة | 🛡️ درع الأرواح | ⚡ اندفاع الجحيم",
        "desc": "مقاتل أسطوري يستمد قوته من ظلال المعارك ويهشم دروع الأعداء.",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000&auto=format&fit=crop"
    },
    "golden_samurai": {
        "name": "⚡ الساموراي الذهبي (Golden Samurai)",
        "gender": "ذكر ♂️",
        "power": "92/100",
        "skills": "🗡️ قطع البرق | 🌀 إعصار الشفرات | 👁️ التركيز المطلق",
        "desc": "صاحب السرعة الخاطفة ودقة الضربات القاتلة بالسيف الذهبي.",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
    },
    "soul_reaper": {
        "name": "🔮 صائد الأرواح (Soul Reaper)",
        "gender": "ذكر ♂️",
        "power": "96/100",
        "skills": "☠️ ملمس الموت | 🌌 ثقب الفراغ | 🩸 امتصاص الحياة",
        "desc": "سيّاد الأرواح من الأبعاد المظلمة، يقتات على طاقة الخصوم.",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000&auto=format&fit=crop"
    },
    "dragon_empress": {
        "name": "🐉 سيدة التنانين (Dragon Empress)",
        "gender": "أنثى ♀️",
        "power": "95/100",
        "skills": "🔥 زئير التنين | 🛡️ درع الحرشوف | ☄️ نيزك الجمر",
        "desc": "تتحكم بالنيران الأسطورية وتستدعي التنانين لحماية حلفائها.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=1000&auto=format&fit=crop"
    },
    "frost_queen": {
        "name": "❄️ أميرة الجليد (Frost Queen)",
        "gender": "أنثى ♀️",
        "power": "94/100",
        "skills": "🧊 التجميد المطلق | 🌪️ العاصفة الثلجية | 💎 رمح الصقيع",
        "desc": "تحكم الساحات بجمود الجليد وتجمد الأعداء قبل اقترابهم.",
        "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=1000&auto=format&fit=crop"
    },
    "shadow_witch": {
        "name": "🔮 ساحرة الظلال (Shadow Witch)",
        "gender": "أنثى ♀️",
        "power": "97/100",
        "skills": "🌑 اللعنة السوداء | 👁️ الرؤية المظلمة | 👻 استدعاء الأطياف",
        "desc": "تنسج السحر الأسود من أعماق الظلام وتضعف قدرات الخصوم.",
        "image": "https://images.unsplash.com/photo-1509281373149-e957c6296406?q=80&w=1000&auto=format&fit=crop"
    },
    "blood_blade": {
        "name": "🗡️ قاطعة الدماء (Blood Blade)",
        "gender": "أنثى ♀️",
        "power": "93/100",
        "skills": "🩸 رقصة الدماء | ⚡ القفزة السريعة | 🗡️ الطعنة المزدوجة",
        "desc": "محاربة سريعة جداً تعتمد على سفك الدماء لزيادة سرعتها وقوتها.",
        "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=1000&auto=format&fit=crop"
    }
}

# ==================== الأحداث (Events) ====================
@bot.event
async def on_ready():
    print(f"🟢 البوت يعمل الآن باسم: {bot.user}")

# ==================== الأوامر النصية (Prefix Commands) ====================
@bot.command(name="sync")
async def sync_commands(ctx):
    try:
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ تم تنظيف السيرفر وإعادة مزامنة `{len(synced)}` أمر بدقة بدون تكرار!")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء المزامنة: {e}")

# ==================== الأوامر الشرطية (Slash Commands) ====================

@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! سرعة الاتصال: `{latency}ms`", ephemeral=True)

@bot.tree.command(name="الملف", description="عرض بطاقتك الشخصية بتصميم فخم")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    target = العضو or interaction.user
    bg_url = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=1000&auto=format&fit=crop"
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي | {target.display_name}",
        description="✨ **البطاقة التعريفية الرسمية داخل السيرفر**",
        color=0xD4AF37
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🆔 الآيدي:", value=f"`{target.id}`", inline=True)
    embed.add_field(name="📅 انضمامك للسيرفر:", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🚀 إنشاء الحساب:", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 أعلى رتبة:", value=target.top_role.mention, inline=False)
    embed.set_image(url=bg_url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="الابطال", description="استعراض الأبطال الأسطوريين وصورهم ومهاراتهم")
@app_commands.choices(البطل=[
    app_commands.Choice(name="⚔️ فارس الظلام (ذكر)", value="dark_knight"),
    app_commands.Choice(name="⚡ الساموراي الذهبي (ذكر)", value="golden_samurai"),
    app_commands.Choice(name="🔮 صائد الأرواح (ذكر)", value="soul_reaper"),
    app_commands.Choice(name="🐉 سيدة التنانين (أنثى)", value="dragon_empress"),
    app_commands.Choice(name="❄️ أميرة الجليد (أنثى)", value="frost_queen"),
    app_commands.Choice(name="🔮 ساحرة الظلال (أنثى)", value="shadow_witch"),
    app_commands.Choice(name="🗡️ قاطعة الدماء (أنثى)", value="blood_blade")
])
async def heroes(interaction: discord.Interaction, البطل: app_commands.Choice[str]):
    selected = HEROES[البطل.value]
    
    embed = discord.Embed(
        title=selected["name"],
        description=f"👤 **الجنس:** {selected['gender']}\n⚡ **مستوى القوة:** `{selected['power']}`\n\n📜 **الوصف:** {selected['desc']}\n\n🔥 **المهارات الخاصة:**\n`{selected['skills']}`",
        color=0x9B59B6
    )
    embed.set_image(url=selected["image"])
    embed.set_footer(text="قائمة أبطال النخبة الأسطورية ⚔️")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر_عادي", description="استعراض المعدات والأسلحة العادية بأسعار مناسبة")
async def normal_shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 المتجر العادي للمعدات",
        description="معدات وأسلحة موثوقة لتعزيز قدراتك في المعارك بأسعار معقولة:\n",
        color=0x3498DB
    )
    
    items = [
        ("🗡️ سيف الفولاذ الخفيف", "⚙️ الرتبة: `عادي` | 🪙 السعر: 150 ذهبة", "يزيد الهجوم +20"),
        ("🛡️ درع الحديد المقوى", "⚙️ الرتبة: `عادي` | 🪙 السعر: 200 ذهبة", "يزيد الدفاع +25"),
        ("🏹 قوس الصياد السريع", "✨ الرتبة: `نادر` | 🪙 السعر: 450 ذهبة", "يزيد سرعة الهجوم +15%"),
        ("💍 خاتم القوة السحرية", "✨ الرتبة: `نادر` | 🪙 السعر: 600 ذهبة", "يزيد طاقة السحر +40"),
        ("🪖 خوذة الفارس الملكي", "🌟 الرتبة: `أسطوري` | 🪙 السعر: 1,200 ذهبة", "تمنح حماية ضد الضربات الحرجة"),
        ("👟 حذاء الريح الخاطف", "🌟 الرتبة: `أسطوري` | 🪙 السعر: 1,500 ذهبة", "يزيد سرعة المراوغة +30%")
    ]
    
    for name, details, eff in items:
        embed.add_field(name=name, value=f"{details}\n✨ **التأثير:** {eff}\n---", inline=False)
        
    embed.set_footer(text="استخدم أموالك بحكمة لتطوير بطلتك أو بطلك!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر_الظلام", description="دخول متجر الظلام للمعدات الملعونة والأدوات المحرمة")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💀 متجر الظلام الملعون",
        description="⚠️ **تحذير:** هذه المعدات تحتوي على طاقات ملعونة وقوة تدميرية هائلة!\n",
        color=0x992D22
    )
    
    dark_items = [
        ("🗡️ خنجر الأرواح الملعون", "🟣 الرتبة: `مقدس` | 🪙 السعر: 4,000 ذهبة", "يمتص 20% من صحة الخصم عند كل ضربة"),
        ("🛡️ درع الجماجم السوداء", "🟣 الرتبة: `مقدس` | 🪙 السعر: 6,500 ذهبة", "يعكس 15% من الضرر الوارد إلى المهاجم"),
        ("🔮 صولجان الهلاك الأبدي", "🔥 الرتبة: `الجحيم` | 🪙 السعر: 12,000 ذهبة", "يطلق حرقاً جهنمياً يستمر طوال المعركة"),
        ("🩸 عباءة دماء الشياطين", "🔥 الرتبة: `الجحيم` | 🪙 السعر: 18,000 ذهبة", "تخفي صاحبها وتزيد الضرر الحرج بنسبة 100%"),
        ("👑 تاج العرش المظلم", "⚡ الرتبة: `الشيطان الأكبر` | 🪙 السعر: 35,000 ذهبة", "يضاعف جميع مهارات البطل ويستدعي طيفاً مساعداً"),
        ("💍 خاتم الفناء المطلق", "⚡ الرتبة: `الشيطان الأكبر` | 🪙 السعر: 50,000 ذهبة", "يمنح فرصة 10% للقضاء على الخصم بضربة واحدة")
    ]
    
    for name, details, eff in dark_items:
        embed.add_field(name=name, value=f"{details}\n🩸 **اللعنة/التأثير:** {eff}\n---", inline=False)
        
    embed.set_thumbnail(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000&auto=format&fit=crop")
    embed.set_footer(text="أعلى رتبة للمعدات الملعونة: الجحيم ➔ الشيطان الأكبر ☠️")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="حظ", description="تجربة حظك اليومي لربح الذهب")
async def luck(interaction: discord.Interaction):
    outcomes = [
        ("🏆 فوز أسطوري!", "حصلت على 500 قطعة ذهبية 🪙", discord.Color.gold()),
        ("🎉 فوز ممتاز!", "حصلت على 150 قطعة ذهبية 🪙", discord.Color.green()),
        ("💀 خسارة قاسية!", "خسرت 50 قطعة ذهبية!", discord.Color.red()),
        ("⚡ تعادل!", "لم تكسب ولم تخسر أي شيء.", discord.Color.blue())
    ]
    title, desc, color = random.choice(outcomes)
    embed = discord.Embed(title=title, description=desc, color=color)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="تخمين", description="لعبة تخمين رقم الحظ من 1 إلى 10")
async def guess(interaction: discord.Interaction, الرقم: int):
    if الرقم < 1 or الرقم > 10:
        await interaction.response.send_message("❌ اختر رقماً بين 1 و 10 فقط!", ephemeral=True)
        return
        
    secret_num = random.randint(1, 10)
    if الرقم == secret_num:
        embed = discord.Embed(title="🎯 إجابة صحيحة!", description=f"الرقم السري كان `{secret_num}`.", color=discord.Color.green())
    else:
        embed = discord.Embed(title="❌ إجابة خاطئة!", description=f"تخمينك كان `{الرقم}` والرقم السري هو `{secret_num}`.", color=discord.Color.red())
        
    await interaction.response.send_message(embed=embed)

# تشغيل البوت
bot.run(os.getenv('TOKEN'))
