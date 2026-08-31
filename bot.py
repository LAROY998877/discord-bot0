import os
import discord
from discord.ext import commands
import pymongo
import random

# إعدادات الاتصال بقاعدة البيانات وقناة البوت
MONGO_URI = os.getenv("MONGO_URI", "رابط_الاتصال_الخاص_بـ_MongoDB")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col = db["users"]
guilds_col = db["guilds"]  # مجموعة النقابات

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# معرفات المطورين (قم بتغييرها بما يناسب الآيدي الخاص بك)
DEVELOPER_IDS = [123456789012345678] 

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f"البوت يعمل الآن باسم: {bot.user}")


# ================== 1. نظام التسجيل ==================
@bot.tree.command(name="تسجيل", description="التسجيل في نظام اللعبة والحصول على لقب المبتدئ")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if users_col.find_one({"user_id": user_id}):
        return await interaction.response.send_message("❌ أنت مسجل بالفعل في قاعدة البيانات!", ephemeral=True)
    
    new_user = {
        "user_id": user_id,
        "balance": 1000,
        "bank": 0,
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "selected_hero": "لم يتم اختيار بطل بعد",
        "guild": None,
        "inventory": [],
        "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
        "defense": 10, "critical": 10, "magic": 10, "intelligence": 10
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح في الإمبراطورية!** حصلت على مكافأة البداية `1,000` 🪙 و `10` 💎 ألماس.", ephemeral=True)


# ================== 2. الملف الشخصي (مرتب بشكل رهيب) ==================
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
    guild = user_data.get("guild", "بلا نقابة")
    
    aim = user_data.get("aim", 10)
    evasion = user_data.get("evasion", 10)
    attack = user_data.get("attack", 10)
    accuracy = user_data.get("accuracy", 10)
    defense = user_data.get("defense", 10)
    critical = user_data.get("critical", 10)
    magic = user_data.get("magic", 10)
    intelligence = user_data.get("intelligence", 10)
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=discord.Color.from_rgb(40, 40, 40)
    )
    
    general_info = (
        f"👑 **اللقب الحالي:** `{custom_title}`\n"
        f"🦸‍♂️ **البطل المختار:** `{selected_hero}`\n"
        f"🏰 **النقابة:** `{guild}`\n"
        f"⚡ **طاقة القتال:** `{power:,}`"
    )
    embed.add_field(name="📌 **المعلومات العامة**", value=general_info, inline=False)
    
    combat_stats = (
        f"🎯 **التصويب:** `{aim:,}` | 💨 **المراوغة:** `{evasion:,}`\n"
        f"🗡️ **الهجوم:** `{attack:,}` | 👁️ **الدقة:** `{accuracy:,}`\n"
        f"🛡️ **الدفاع:** `{defense:,}` | 💥 **الحرجة:** `{critical:,}`\n"
        f"🔮 **السحر:** `{magic:,}` | 🧠 **الذكاء:** `{intelligence:,}`"
    )
    embed.add_field(name="📊 **ترسانة المعدلات القتالية**", value=combat_stats, inline=False)
    
    wealth_stats = (
        f"🏢 **أعلى طابق:** `{max_floor}` | 💀 **الخصوم المقضي عليهم:** `{kills:,}`\n"
        f"🪙 **المحفظة:** `{balance:,}` | 💳 **البنك:** `{bank:,}`\n"
        f"💎 **الألماس:** `{diamonds:,}`"
    )
    embed.add_field(name="💰 **الثروة والإنجازات**", value=wealth_stats, inline=False)

    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"معرف المقاتل: {user_id} | نظام الإمبراطورية الأسطوري", icon_url=interaction.guild.icon.url if interaction.guild else None)
    await interaction.followup.send(embed=embed, ephemeral=False)


# ================== 3. أوامر البنك وخياراته ==================
@bot.tree.command(name="بنك_إيداع", description="إيداع العملات في البنك للحفاظ عليها")
async def bank_deposit(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get("balance", 0) < amount or amount <= 0:
        return await interaction.response.send_message("❌ رصيدك في المحفظة لا يكفي أو القيمة غير مدعومة!", ephemeral=True)
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -amount, "bank": amount}})
    await interaction.response.send_message(f"✅ تم إيداع `{amount:,}` 🪙 في البنك بنجاح.", ephemeral=False)

@bot.tree.command(name="بنك_سحب", description="سحب العملات من البنك إلى المحفظة")
async def bank_withdraw(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get("bank", 0) < amount or amount <= 0:
        return await interaction.response.send_message("❌ رصيدك في البنك لا يكفي أو القيمة غير مدعومة!", ephemeral=True)
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount, "bank": -amount}})
    await interaction.response.send_message(f"✅ تم سحب `{amount:,}` 🪙 من البنك إلى محفظتك بنجاح.", ephemeral=False)

@bot.tree.command(name="رصيد", description="عرض رصيدك الحالي في المحفظة والبنك والألماس")
async def balance_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ لم تقم بالتسجيل بعد!", ephemeral=True)
    
    embed = discord.Embed(title=f"💰 خزنة المقاتل: {interaction.user.display_name}", color=discord.Color.green())
    embed.add_field(name="🪙 المحفظة", value=f"`{user_data.get('balance', 0):,}`", inline=True)
    embed.add_field(name="💳 البنك", value=f"`{user_data.get('bank', 0):,}`", inline=True)
    embed.add_field(name="💎 الألماس", value=f"`{user_data.get('diamonds', 0):,}`", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ================== 4. أوامر الأبطال وخياراته ==================
@bot.tree.command(name="الأبطال_عرض", description="عرض قائمة الأبطال المتاحين وقدراتهم")
async def heroes_list(interaction: discord.Interaction):
    embed = discord.Embed(title="🦸‍♂️ قائمة أبطال الإمبراطورية", color=discord.Color.blue())
    embed.add_field(name="⚔️ فارس الظلام", value="متخصص في الهجوم والدفاع المباشر.", inline=False)
    embed.add_field(name="🗡️ السفاح المحترف", value="متخصص في السرعة والضربات الحرجة.", inline=False)
    embed.add_field(name="🔮 حارس السحر", value="متخصص في السحر والذكاء التدميري.", inline=False)
    embed.add_field(name="🛡️ مقاتل الطوارئ", value="بطل متوازن مناسب لكافة المهام.", inline=False)
    embed.set_footer(text="استخدم أمر /اختيار_البطل لاختيار بطلك.")
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="اختيار_البطل", description="اختر بطلك المفضل لرحلة القتال")
async def select_hero(interaction: discord.Interaction, bosta: str):
    user_id = str(interaction.user.id)
    heroes = ["فارس الظلام", "السفاح المحترف", "حارس السحر", "مقاتل الطوارئ"]
    if bosta not in heroes:
        return await interaction.response.send_message(f"❌ البطل غير موجود! الأبطال المتاحون: {', '.join(heroes)}", ephemeral=True)
    
    users_col.update_one({"user_id": user_id}, {"$set": {"selected_hero": bosta}})
    await interaction.response.send_message(f"⚔️ لقد اخترت البطل **{bosta}** بنجاح!", ephemeral=False)


# ================== 5. أوامر تطوير المعداتي وخياراته ==================
@bot.tree.command(name="تطوير_المعدات", description="تطوير معداتك القتالية لرفع خصائص الهجوم والدفاع والدقة")
async def upgrade_gear(interaction: discord.Interaction, stat_type: str):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يجب التسجيل أولاً!", ephemeral=True)
    
    valid_stats = ["attack", "defense", "aim", "evasion", "accuracy", "critical", "magic", "intelligence"]
    if stat_type not in valid_stats:
        return await interaction.response.send_message(f"❌ نوع المعدات غير صحيح! الخيارات المتاحة: `{', '.join(valid_stats)}`", ephemeral=True)
    
    cost = 300  # تكلفة التطوير
    if user_data.get("balance", 0) < cost:
        return await interaction.response.send_message(f"❌ رصيدك لا يكفي لتطوير المعدات (تحتاج إلى `{cost}` 🪙)!", ephemeral=True)
    
    # خصم التكلفة وزيادة الخاصية المطلوبة مع زيادة الطاقة القتالية العامة
    users_col.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": -cost,
                stat_type: 5,
                "power": 15
            }
        }
    )
    await interaction.response.send_message(f"🛠️ **تم تطوير معداتك بنجاح!** زادت خاصية `{stat_type}` بمقدار `5` نقاط، وزادت طاقتك الإجمالية بـ `15` نقطة.", ephemeral=False)


# ================== 6. أوامر المتاجر وخياراته ==================
@bot.tree.command(name="متجر_عرض", description="عرض المنتجات المتاحة للشراء في المتجر")
async def store_view(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 متجر الإمبراطورية العظيم", color=discord.Color.gold())
    embed.add_field(name="1️⃣ جرعة طاقة (+50 طاقة)", value="السعر: 500 🪙 (`/شراء_جرعة`)", inline=False)
    embed.add_field(name="2️⃣ حجر ترقية الألماس (5 ألماس)", value="السعر: 1000 🪙 (`/شراء_ألماس`)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="شراء_جرعة", description="شراء جرعة لزيادة طاقتك القتالية مقابل العملات")
async def buy_potion(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get("balance", 0) < 500:
        return await interaction.response.send_message("❌ لا تملك عملات كافية لشراء الجرعة (تحتاج 500 🪙)!", ephemeral=True)
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -500, "power": 50}})
    await interaction.response.send_message("🧪 لقد اشتريت جرعة الطاقة بنجاح وزادت طاقتك القتالية بـ `50` نقطة!", ephemeral=False)


# ================== 7. أوامر الطوابق وخياراته ==================
@bot.tree.command(name="طابق_صعود", description="صعود الطوابق وقتال وحوش البرج لاجتياز الاختبارات")
async def floor_climb(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.response.send_message("❌ يجب التسجيل أولاً!", ephemeral=True)
    
    next_floor = user_data.get("max_floor", 0) + 1
    power = user_data.get("power", 100)
    
    if power >= (next_floor * 40) or random.choice([True, False]):
        users_col.update_one({"user_id": user_id}, {"$inc": {"max_floor": 1, "kills": 1, "balance": 400}})
        await interaction.response.send_message(f"🏆 **انتصار مبهر!** اجتزت وحوش الطابق `{next_floor}` وحصلت على `400` 🪙!", ephemeral=False)
    else:
        await interaction.response.send_message(f"💀 **هزيمة قاسية!** وحش الطابق `{next_floor}` كان أقوى منك، ارفع طاقتك وحاول مجدداً.", ephemeral=False)


# ================== 8. أوامر الحقيبة وخياراته ==================
@bot.tree.command(name="حقيبة_عرض", description="عرض محتويات حقيبتك الشخصية")
async def inventory_view(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    inventory = user_data.get("inventory", [])
    
    if not inventory:
        return await interaction.response.send_message("🎒 حقيبتك فارغة حالياً.", ephemeral=False)
    
    items_text = "\n".join([f"• {item}" for item in inventory])
    embed = discord.Embed(title=f"🎒 حقيبة المقاتل: {interaction.user.display_name}", description=items_text, color=discord.Color.dark_orange())
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ================== 9. أوامر إنشاء نقابة ونقابتي ==================
@bot.tree.command(name="انشاء_نقابة", description="إنشاء نقابة جديدة خاصة بك (التكلفة: 5000 عملة)")
async def create_guild(interaction: discord.Interaction, guild_name: str):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get("balance", 0) < 5000:
        return await interaction.response.send_message("❌ تحتاج إلى `5000` 🪙 لإنشاء نقابة!", ephemeral=True)
    
    if guilds_col.find_one({"name": guild_name}):
        return await interaction.response.send_message("❌ اسم النقابة مستخدم بالفعل!", ephemeral=True)
    
    guilds_col.insert_one({"name": guild_name, "leader": user_id, "members": [user_id], "level": 1})
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -5000}, "$set": {"guild": guild_name}})
    await interaction.response.send_message(f"🏰 **تم إنشاء النقابة '{guild_name}' بنجاح وأنت قائدها العام!**", ephemeral=False)

@bot.tree.command(name="نقابتي", description="عرض معلومات نقابتك الحالية والأعضاء")
async def my_guild(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    guild_name = user_data.get("guild")
    
    if not guild_name or guild_name == "بلا نقابة":
        return await interaction.response.send_message("❌ أنت لست منضمًا إلى أي نقابة حالياً!", ephemeral=True)
    
    guild_data = guilds_col.find_one({"name": guild_name})
    embed = discord.Embed(title=f"🏰 تفاصيل نقابة: {guild_name}", color=discord.Color.purple())
    embed.add_field(name="👑 القائد", value=f"<@{guild_data['leader']}>", inline=True)
    embed.add_field(name="👥 عدد الأعضاء", value=str(len(guild_data["members"])), inline=True)
    embed.add_field(name="⭐ مستوى النقابة", value=str(guild_data["level"]), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ================== 10. أوامر الألعاب وخياراته ==================
@bot.tree.command(name="لعبة_حظ", description="لعبة حظ سريعة لمضاعفة عملاتك أو خسارتها")
async def gamble_game(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get("balance", 0) < amount or amount <= 0:
        return await interaction.response.send_message("❌ ليس لديك رصيد كافٍ في المحفظة لهذه المغامرة!", ephemeral=True)
    
    if random.choice([True, False]):
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
        await interaction.response.send_message(f"🎉 **مبروك!** ربحت رهانتك وحصلت على مضاعفة بقيمة `{amount:,}` 🪙!", ephemeral=False)
    else:
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
        await interaction.response.send_message(f"😢 **للأسف!** خسرت رهانتك وقدرها `{amount:,}` 🪙.", ephemeral=False)


# ================== 11. لوحة المطور وكامل خياراتها ==================
@bot.tree.command(name="مطور_اعطاء_فلوس", description="[للمطور فقط] منح عملات لمستخدم معين")
async def dev_give_money(interaction: discord.Interaction, member: discord.Member, amount: int):
    if interaction.user.id not in DEVELOPER_IDS:
        return await interaction.response.send_message("❌ هذا الأمر مخصص لمطوري البوت فقط!", ephemeral=True)
    
    users_col.update_one({"user_id": str(member.id)}, {"$inc": {"balance": amount}}, upsert=True)
    await interaction.response.send_message(f"✅ تم إضافة `{amount:,}` 🪙 للمستخدم {member.mention} بنجاح.", ephemeral=True)

@bot.tree.command(name="مطور_خصم_فلوس", description="[للمطور فقط] خصم عملات من مستخدم معين")
async def dev_take_money(interaction: discord.Interaction, member: discord.Member, amount: int):
    if interaction.user.id not in DEVELOPER_IDS:
        return await interaction.response.send_message("❌ هذا الأمر مخصص لمطوري البوت فقط!", ephemeral=True)
    
    users_col.update_one({"user_id": str(member.id)}, {"$inc": {"balance": -amount}}, upsert=True)
    await interaction.response.send_message(f"✅ تم خصم `{amount:,}` 🪙 من المستخدم {member.mention} بنجاح.", ephemeral=True)

@bot.tree.command(name="مطور_إحصائيات", description="[للمطور فقط] عرض إحصائيات قاعدة البيانات الشاملة")
async def dev_stats(interaction: discord.Interaction):
    if interaction.user.id not in DEVELOPER_IDS:
        return await interaction.response.send_message("❌ هذا الأمر مخصص لمطوري البوت فقط!", ephemeral=True)
    
    total_users = users_col.count_documents({})
    total_guilds = guilds_col.count_documents({})
    
    embed = discord.Embed(title="📊 لوحة تحكم وإحصائيات المطور", color=discord.Color.red())
    embed.add_field(name="👥 إجمالي المستخدمين المسجلين", value=str(total_users), inline=True)
    embed.add_field(name="🏰 إجمالي النقابات النشطة", value=str(total_guilds), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
