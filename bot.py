import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

class FakhamaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        synced = await self.tree.sync()
        print(f"✅ تمت مزامنة {len(synced)} أمر بنجاح!")

bot = FakhamaBot()

# طباعة أي خطأ يحدث داخل الكونسول لتسهيل معرفته
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print(f"❌ خطأ أثناء تنفيذ الأمر: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message("❌ حدث خطأ أثناء تنفيذ الأمر، يرجى المحاولة لاحقاً.", ephemeral=True)

# ==================== 1. أمر الملف الشخصي ====================
@bot.tree.command(name="الملف", description="عرض بطاقتك الشخصية بتصميم فخم وخلفية سينمائية")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    await interaction.response.defer()
    target = العضو or interaction.user
    background_url = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?q=80&w=1000&auto=format&fit=crop"
    
    embed = discord.Embed(
        title=f"👑 الملف الشخصي | {target.display_name}",
        description="✨ **البطاقة التعريفية الرسمية داخل السيرفر**",
        color=discord.Color.from_rgb(212, 175, 55)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🆔 الآيدي:", value=f"`{target.id}`", inline=True)
    embed.add_field(name="📅 انضمامك للسيرفر:", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🚀 إنشاء الحساب:", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 أعلى رتبة:", value=target.top_role.mention, inline=False)
    embed.set_image(url=background_url)
    
    await interaction.followup.send(embed=embed)

# ==================== 2. أمر الأبطال ====================
HEROES = {
    "فارس_الظلام": {
        "name": "⚔️ فارس الظلام (Dark Knight)",
        "desc": "مقاتل أسطوري يمتلك قوة هجومية ساحقة في المعارك الليلية.",
        "power": "98/100",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000&auto=format&fit=crop"
    },
    "سيدة_التنانين": {
        "name": "🐉 سيدة التنانين (Dragon Empress)",
        "desc": "تتحكم بالنيران الأسطورية وتملك درعاً متيناً لا يُقهر.",
        "power": "95/100",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=1000&auto=format&fit=crop"
    },
    "الساموراي_الذهبي": {
        "name": "⚡ الساموراي الذهبي (Golden Samurai)",
        "desc": "صاحب السرعة الخاطفة ودقة الضربات القاتلة بالسيف.",
        "power": "92/100",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
    }
}

@bot.tree.command(name="الابطال", description="استعراض الأبطال الأسطوريين وقدراتهم وصورهم الفخمة")
@app_commands.choices(البطل=[
    app_commands.Choice(name="⚔️ فارس الظلام", value="فارس_الظلام"),
    app_commands.Choice(name="🐉 سيدة التنانين", value="سيدة_التنانين"),
    app_commands.Choice(name="⚡ الساموراي الذهبي", value="الساموراي_الذهبي")
])
async def heroes(interaction: discord.Interaction, البطل: app_commands.Choice[str]):
    await interaction.response.defer()
    selected_hero = HEROES[البطل.value]
    
    embed = discord.Embed(
        title=selected_hero["name"],
        description=f"📜 **الوصف:** {selected_hero['desc']}\n⚡ **مستوى القوة:** `{selected_hero['power']}`",
        color=discord.Color.purple()
    )
    embed.set_image(url=selected_hero["image"])
    
    await interaction.followup.send(embed=embed)

# ==================== 3. لعبة الحظ ====================
@bot.tree.command(name="حظ", description="تجربة حظك اليومي لربح الذهب")
async def luck(interaction: discord.Interaction):
    await interaction.response.defer()
    outcomes = [
        ("🏆 فوز أسطوري!", "حصلت على 500 قطعة ذهبية 🪙", discord.Color.gold()),
        ("🎉 فوز ممتاز!", "حصلت على 150 قطعة ذهبية 🪙", discord.Color.green()),
        ("💀 خسارة قاسية!", "خسرت 50 قطعة ذهبية!", discord.Color.red()),
        ("⚡ تعادل!", "لم تكسب ولم تخسر أي شيء.", discord.Color.blue())
    ]
    title, desc, color = random.choice(outcomes)
    embed = discord.Embed(title=title, description=desc, color=color)
    
    await interaction.followup.send(embed=embed)

# ==================== 4. لعبة التخمين ====================
@bot.tree.command(name="تخمين", description="لعبة تخمين رقم الحظ من 1 إلى 10")
async def guess(interaction: discord.Interaction, الرقم: int):
    if الرقم < 1 or الرقم > 10:
        await interaction.response.send_message("❌ يرجى اختيار رقم بين 1 و 10 فقط!", ephemeral=True)
        return
        
    secret_num = random.randint(1, 10)
    if الرقم == secret_num:
        embed = discord.Embed(title="🎯 إجابة صحيحة!", description=f"ماشاء الله! الرقم السري كان بالفعل `{secret_num}`.", color=discord.Color.green())
    else:
        embed = discord.Embed(title="❌ إجابة خاطئة!", description=f"تخمينك كان `{الرقم}` والرقم السري الصحيح هو `{secret_num}`.", color=discord.Color.red())
        
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv('TOKEN'))
