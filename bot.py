import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# بيانات الأبطال والصور
HEROES = {
    "dark_knight": {
        "name": "⚔️ فارس الظلام (Dark Knight)",
        "desc": "مقاتل أسطوري يمتلك قوة هجومية ساحقة في المعارك الليلية.",
        "power": "98/100",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000&auto=format&fit=crop"
    },
    "dragon_empress": {
        "name": "🐉 سيدة التنانين (Dragon Empress)",
        "desc": "تتحكم بالنيران الأسطورية وتملك درعاً متيناً لا يُقهر.",
        "power": "95/100",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=1000&auto=format&fit=crop"
    },
    "golden_samurai": {
        "name": "⚡ الساموراي الذهبي (Golden Samurai)",
        "desc": "صاحب السرعة الخاطفة ودقة الضربات القاتلة بالسيف.",
        "power": "92/100",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
    }
}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم الاتصال باسم {bot.user} ومزامنة {len(synced)} أمر سلاش بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")

# 1. أمر الملف الشخصي
@bot.tree.command(name="الملف", description="عرض بطاقتك الشخصية بتصميم فخم")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    target = العضو or interaction.user
    bg_url = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=1000&auto=format&fit=crop"
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي | {target.display_name}",
        description="✨ **البطاقة التعريفية الرسمية**",
        color=0xD4AF37
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🆔 الآيدي:", value=f"`{target.id}`", inline=True)
    embed.add_field(name="📅 انضمامك للسيرفر:", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🚀 إنشاء الحساب:", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 أعلى رتبة:", value=target.top_role.mention, inline=False)
    embed.set_image(url=bg_url)
    
    await interaction.response.send_message(embed=embed)

# 2. أمر الأبطال
@bot.tree.command(name="الابطال", description="استعراض الأبطال الأسطوريين وصورهم الفخمة")
@app_commands.choices(البطل=[
    app_commands.Choice(name="⚔️ فارس الظلام", value="dark_knight"),
    app_commands.Choice(name="🐉 سيدة التنانين", value="dragon_empress"),
    app_commands.Choice(name="⚡ الساموراي الذهبي", value="golden_samurai")
])
async def heroes(interaction: discord.Interaction, البطل: app_commands.Choice[str]):
    selected_hero = HEROES[البطل.value]
    
    embed = discord.Embed(
        title=selected_hero["name"],
        description=f"📜 **الوصف:** {selected_hero['desc']}\n⚡ **مستوى القوة:** `{selected_hero['power']}`",
        color=discord.Color.purple()
    )
    embed.set_image(url=selected_hero["image"])
    
    await interaction.response.send_message(embed=embed)

# 3. لعبة الحظ
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

# 4. لعبة التخمين
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

bot.run(os.getenv('TOKEN'))
