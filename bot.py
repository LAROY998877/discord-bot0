import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DEVELOPER_ID = 1103985971638325269

# قواعد البيانات
USER_ECONOMY = {}
USER_STATS = {}    # حقيبة اللاعبين (العتاد والكمية)
USER_EQUIPPED = {} # العتاد المركب حالياً لكل لاعب
EXTRA_DEVS = set()

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 5000}
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

# ==================== بيانات المعدات والصور الدقيقة ====================
ITEMS_DATA = {
    # المتجر العادي
    "سيف حديدي بسيط": {"price": 100, "type": "عادي", "image": "https://images.unsplash.com/photo-1595590424283-b8f17842773f?q=80&w=800", "desc": "سيف تقليدي حاد ومناسب للمبتدئين."},
    "درع خشبي متين": {"price": 150, "type": "عادي", "image": "https://images.unsplash.com/photo-1548234479-111002377cf6?q=80&w=800", "desc": "درع من الخشب المقوى لحماية أساسية."},
    "خنجر الصياد السريع": {"price": 200, "type": "عادي", "image": "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?q=80&w=800", "desc": "خنجر خفيف للطعنات السريعة."},
    "قوس الخشب القديم": {"price": 250, "type": "عادي", "image": "https://images.unsplash.com/photo-1513151233558-d860c5398176?q=80&w=800", "desc": "قوس بدائي للهجوم عن بعد."},
    "رمح الحراس": {"price": 300, "type": "عادي", "image": "https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?q=80&w=800", "desc": "رمح طويل يحافظ على مسافة آمنة."},

    # المتجر المظلم (رتب الشيطان والجحيم)
    "نصل الجحيم المحرق": {"price": 1200, "type": "🔥 رتبة الجحيم", "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800", "desc": "سيف أسطوري مشتعل بنيران الحمم البركانية الحارقة."},
    "مطرقة الجحيم العملاقة": {"price": 2000, "type": "🔥 رتبة الجحيم", "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?q=80&w=800", "desc": "مطرقة جحيمية ثقيلة تحطم أي درع بضربة واحدة."},
    "خنجر الشيطان الدموي": {"price": 1600, "type": "🖤 رتبة الشيطان", "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=800", "desc": "خنجر شيطاني مسكون بلعنة الظلام وسرعة مرعبة."},
    "سيف الشيطان الأبدي": {"price": 2800, "type": "🖤 رتبة الشيطان", "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800", "desc": "سيف مرعب وفخم للغاية ينبض بطاقة الشيطان."},
    "صولجان الخراب المظلم": {"price": 3500, "type": "🖤 رتبة الشيطان", "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800", "desc": "سلاح الدمار الشامل لسيطرة مطلقة على العوالم."},
}

# ==================== واجهات المتجر العادي والمظلم ====================

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🛒 اختر السلاح العادي لعرض صورته وشرائه...",
        options=[discord.SelectOption(label=name, description=f"السعر: {data['price']} عملة | النوع: {data['type']}", value=name) for name, data in list(ITEMS_DATA.items())[:5]]
    )
    async def select_item(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_name = select.values[0]
        item = ITEMS_DATA[item_name]
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item["price"]:
            await interaction.response.send_message(f"❌ رصيدك غير كافي! تحتاج إلى `{item['price']}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item["price"]
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        
        embed = discord.Embed(title=f"✅ تم شراء ({item_name}) بنجاح!", description=item["desc"], color=0x3498DB)
        embed.set_image(url=item["image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🌑 اختر معدات الجحيم والشيطان لعرض صورتها المرعبة...",
        options=[discord.SelectOption(label=name, description=f"السعر: {data['price']} | {data['type']}", value=name) for name, data in list(ITEMS_DATA.items())[5:]]
    )
    async def select_dark_item(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_name = select.values[0]
        item = ITEMS_DATA[item_name]
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item["price"]:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي لشراء عتاد ({item['type']})! تحتاج إلى `{item['price']}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item["price"]
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        
        embed = discord.Embed(title=f"🔥 تم اقتناء ({item_name}) بنجاح!", description=f"**الرتبة:** {item['type']}\n{item['desc']}", color=0x8E44AD)
        embed.set_image(url=item["image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== ميزة الحقيبة وتجهيز المعدات ====================

class InventoryEquipView(discord.ui.View):
    def __init__(self, user_stats_dict):
        super().__init__(timeout=60)
        self.user_stats_dict = user_stats_dict
        
        options = []
        for gear_name in user_stats_dict.keys():
            if gear_name in ITEMS_DATA:
                item = ITEMS_DATA[gear_name]
                options.append(discord.SelectOption(label=gear_name, description=f"الرتبة: {item['type']} | العدد: {user_stats_dict[gear_name]}", value=gear_name))
        
        if not options:
            options.append(discord.SelectOption(label="حقيبتك فارغة تماماً", description="توجه للمتاجر للتسوق أولاً", value="empty"))
            
        self.select_menu.options = options

    @discord.ui.select(placeholder="🎒 اختر سلاحاً من حقيبتك لتركيبه وتجهيزه...")
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        gear_name = select.values[0]
        if gear_name == "empty":
            await interaction.response.send_message("❌ حقيبتك فارغة! لا توجد معدات لتركيبها.", ephemeral=True)
            return
            
        USER_EQUIPPED[interaction.user.id] = gear_name
        item = ITEMS_DATA[gear_name]
        
        embed = discord.Embed(title="⚔️ تم تركيب وتجهيز العتاد بنجاح!", description=f"لقد قمت بارتداء وتجهيز **{gear_name}** ({item['type']}). أنت جاهز الآن للقتال!", color=0x2ECC71)
        embed.set_image(url=item["image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== الأوامر الأساسية (مخصصة للمستخدم فقط وبدون خيار العضو) ====================

@bot.tree.command(name="المتجر_العادي", description="استعرض المتجر العادي وتصفح صور الأسلحة بضغطة زر")
async def normal_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمعدات", description="اختر من القائمة أدناه لتظهر لك صورة السلاح وتفاصيله الحقيقية:", color=0x3498DB)
    embed.set_image(url="https://images.unsplash.com/photo-1595590424283-b8f17842773f?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="متجر أسلحة الجحيم والشيطان السرّية الخارقة")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🌑 المتجر المظلم الأسطوري", description="أسلحة رتبتي **الجحيم** و **الشيطان** بانتظارك. اختر بحذر:", color=0x8E44AD)
    embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)

@bot.tree.command(name="الحقيبة", description="عرض حقيبتك الشخصية وتركيب المعدات والسلح النشط")
async def inventory(interaction: discord.Interaction):
    target = interaction.user
    stats = get_user_stats(target.id)
    equipped = USER_EQUIPPED.get(target.id, "لا يوجد سلاح مركب حالياً")
    
    embed = discord.Embed(title=f"🎒 حقيبة المغامر | {target.display_name}", color=0xD4AF37)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="⚔️ العتاد النشط (المُركب):", value=f"`{equipped}`", inline=False)
    
    if stats:
        gear_text = "\n".join([f"🔹 **{gear}** (العدد: {count})" for gear, count in stats.items()])
    else:
        gear_text = "حقيبتك فارغة تماماً!"
        
    embed.add_field(name="📦 جميع المعدات المملوكة:", value=gear_text, inline=False)
    
    if stats:
        await interaction.response.send_message(embed=embed, view=InventoryEquipView(stats), ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وشخصيتك مع العتاد المُركب")
async def profile(interaction: discord.Interaction):
    target = interaction.user
    eco = get_user_economy(target.id)
    equipped = USER_EQUIPPED.get(target.id, None)
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {target.display_name}", color=0xE67E22)
    
    # إذا كان المستخدم مركب سلاح، نعرض صورة السلاح كصورة رئيسية للشخصية، وإذا لم يكن مركباً نعرض صورته الشخصية
    if equipped and equipped in ITEMS_DATA:
        item = ITEMS_DATA[equipped]
        embed.set_image(url=item["image"])  # صورة السلاح/الشخصية الأسطورية
        equipped_text = f"⚔️ **{equipped}** ({item['type']})"
    else:
        equipped_text = "لا يوجد سلاح مركب حالياً"
        embed.set_thumbnail(url=target.display_avatar.url)
        
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="🛡️ العتاد المرتدى (الشخصية):", value=equipped_text, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# لوحة المطور لإهداء العتاد
class DevGearSelect(discord.ui.View):
    def __init__(self, target_member):
        super().__init__(timeout=60)
        self.target_member = target_member

    @discord.ui.select(
        placeholder="⚔️ اختر القطعة المراد إهداؤها...",
        options=[discord.SelectOption(label=name, description=f"النوع: {data['type']} | السعر: {data['price']}", value=name) for name, data in ITEMS_DATA.items()]
    )
    async def select_dev_gear(self, interaction: discord.Interaction, select: discord.ui.Select):
        gear_name = select.values[0]
        stats = get_user_stats(self.target_member.id)
        stats[gear_name] = stats.get(gear_name, 0) + 1
        
        item = ITEMS_DATA[gear_name]
        embed = discord.Embed(title="🛠️ تم إهداء العتاد بواسطة المطور", description=f"تم منح **{gear_name}** إلى العضو {self.target_member.mention} بنجاح!", color=0x2b2d31)
        embed.set_image(url=item["image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطورين الحصرية")
@app_commands.choices(العملية=[
    app_commands.Choice(name="💰 بنك العملات (إضافة رصيد)", value="bank_add"),
    app_commands.Choice(name="⚔️ إهداء عتاد (من القائمة)", value="give_gear"),
    app_commands.Choice(name="👥 إضافة مطور جديد", value="add_dev")
])
@app_commands.describe(العملية="اختر العملية", العضو="العضو المستهدف", كمية_العملات="اكتب عدد العملات (للбанк فقط)")
async def developer_panel(interaction: discord.Interaction, العملية: app_commands.Choice[str], العضو: discord.Member, كمية_العملات: int = 0):
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ عذراً، هذه اللوحة مخصصة للمطورين فقط!", ephemeral=True)
        return
    
    op_val = العملية.value
    if op_val == "bank_add":
        eco = get_user_economy(العضو.id)
        eco["coins"] += كمية_العملات
        await interaction.response.send_message(f"✅ تمت إضافة `{كمية_العملات}` عملة لـ {العضو.mention}.\n💰 رصيده الجديد: `{eco['coins']}`", ephemeral=True)
    elif op_val == "give_gear":
        await interaction.response.send_message(f"🛠️ اختر العتاد لإهدائه إلى {العضو.mention}:", view=DevGearSelect(العضو), ephemeral=True)
    elif op_val == "add_dev":
        EXTRA_DEVS.add(العضو.id)
        await interaction.response.send_message(f"🛡️ تم منح {العضو.mention} صلاحيات المطور بنجاح.", ephemeral=True)

bot.run(os.getenv('TOKEN'))
