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
USER_STATS = {}
EXTRA_DEVS = set()

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 2000}  # رصيد يبدأ بـ 2000 للتجربة
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

# ==================== بيانات المعدات الكاملة ====================
ITEMS_DATA = {
    # المتجر العادي
    "سيف حديدي بسيط": {"price": 100, "type": "عادي", "image": "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?q=80&w=600", "desc": "قوة هجومية أساسية للمبتدئين."},
    "درع خشبي متين": {"price": 150, "type": "عادي", "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=600", "desc": "يوفر حماية بسيطة ضد الضربات الضعيفة."},
    "خنجر الصياد السريع": {"price": 200, "type": "عادي", "image": "https://images.unsplash.com/photo-1595590424283-b8f17842773f?q=80&w=600", "desc": "خفيف الوزن وسريع في الاشتباكات القريبة."},
    "قوس الخشب القديم": {"price": 250, "type": "عادي", "image": "https://images.unsplash.com/photo-1513151233558-d860c5398176?q=80&w=600", "desc": "مناسب للهجوم من مسافات متوسطة."},
    "رمح الحراس": {"price": 300, "type": "عادي", "image": "https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?q=80&w=600", "desc": "يمنحك مدى أطول أثناء الدفاع والهجوم."},

    # المتجر المظلم (رتب الشيطان والجحيم وأساطير الظلام)
    "نصل الجحيم المحرق": {"price": 1200, "type": "🔥 رتبة الجحيم", "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=600", "desc": "نصل متوهج بنار الحمم البركانية المدمرة."},
    "مخلب الشيطان المرعب": {"price": 1800, "type": "🖤 رتبة الشيطان", "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=600", "desc": "قوة شيطانية خالقة للرعب في قلوب الأعداء."},
    "عباءة الظلال الملعونة": {"price": 900, "type": "🟣 أسطوري مظلم", "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600", "desc": "تخفي صاحبها وتمنحه مراوغة خارقة."},
    "صولجان الموت الأبدي": {"price": 2500, "type": "🔥 رتبة الجحيم", "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?q=80&w=600", "desc": "يدمر دروع الخصم بضربة واحدة مرعبة."},
    "تاج الخراب الشيطاني": {"price": 3000, "type": "🖤 رتبة الشيطان", "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=600", "desc": "يعطي سيطرة كاملة على طاقات الظلام المحيطة."}
}

# ==================== واجهات المتاجر (تفاعلية بالقوائم) ====================

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🛒 اختر من عتاد المتجر العادي...",
        options=[
            discord.SelectOption(label="سيف حديدي بسيط", description="السعر: 100 عملة", value="سيف حديدي بسيط"),
            discord.SelectOption(label="درع خشبي متين", description="السعر: 150 عملة", value="درع خشبي متين"),
            discord.SelectOption(label="خنجر الصياد السريع", description="السعر: 200 عملة", value="خنجر الصياد السريع"),
            discord.SelectOption(label="قوس الخشب القديم", description="السعر: 250 عملة", value="قوس الخشب القديم"),
            discord.SelectOption(label="رمح الحراس", description="السعر: 300 عملة", value="رمح الحراس"),
        ]
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
        
        embed = discord.Embed(title=f"✅ تم شراء {item_name} بنجاح!", description=item["desc"], color=0x3498DB)
        embed.set_thumbnail(url=item["image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🌑 اختر من معدات الجحيم والشيطان الخارقة...",
        options=[
            discord.SelectOption(label="نصل الجحيم المحرق", description="السعر: 1200 | رتبة الجحيم 🔥", value="نصل الجحيم المحرق"),
            discord.SelectOption(label="مخلب الشيطان المرعب", description="السعر: 1800 | رتبة الشيطان 🖤", value="مخلب الشيطان المرعب"),
            discord.SelectOption(label="عباءة الظلال الملعونة", description="السعر: 900 | أسطوري مظلم 🟣", value="عباءة الظلال الملعونة"),
            discord.SelectOption(label="صولجان الموت الأبدي", description="السعر: 2500 | رتبة الجحيم 🔥", value="صولجان الموت الأبدي"),
            discord.SelectOption(label="تاج الخراب الشيطاني", description="السعر: 3000 | رتبة الشيطان 🖤", value="تاج الخراب الشيطاني"),
        ]
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
        
        embed = discord.Embed(title=f"🔥 تم اقتناء {item_name} بنجاح!", description=f"**الرتبة:** {item['type']}\n{item['desc']}", color=0x8E44AD)
        embed.set_thumbnail(url=item["image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== لوحة المطور التفاعلية (بدون كتابة يدوية) ====================

class DevGearSelect(discord.ui.View):
    def __init__(self, target_member):
        super().__init__(timeout=60)
        self.target_member = target_member

    @discord.ui.select(
        placeholder="⚔️ اختر القطعة المراد إهداؤها...",
        options=[discord.SelectOption(label=name, description=f"النوع: {data['type']} | السعر: {data['price']}", value=name) for name, data in list(ITEMS_DATA.items())[:10]]
    )
    async def select_dev_gear(self, interaction: discord.Interaction, select: discord.ui.Select):
        gear_name = select.values[0]
        stats = get_user_stats(self.target_member.id)
        stats[gear_name] = stats.get(gear_name, 0) + 1
        
        item = ITEMS_DATA[gear_name]
        embed = discord.Embed(title="🛠️ تم إهداء العتاد بواسطة المطور", description=f"تم منح **{gear_name}** إلى العضو {self.target_member.mention} بنجاح!", color=0x2b2d31)
        embed.set_thumbnail(url=item["image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== الأوامر الأساسية ====================

@bot.tree.command(name="المتجر_العادي", description="استعرض المتاجر العادية واختر عتادك بضغطة زر")
async def normal_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمعدات", description="اختر من القائمة أدناه لتشاهد الصورة وتشتري سلاحك المفضل:", color=0x3498DB)
    embed.set_image(url="https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="متجر أسلحة الجحيم والشيطان السرّية الخارقة")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🌑 المتجر المظلم الأسطوري", description="أسلحة رتبتي **الجحيم** و **الشيطان** بانتظارك. اختر بحذر:", color=0x8E44AD)
    embed.set_image(url="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)

@bot.tree.command(name="الملف", description="عرض رصيدك وعقاراتك وحقيبة معداتك")
async def profile(interaction: discord.Interaction, العضو: discord.Member = None):
    await interaction.response.defer()
    target = العضو or interaction.user
    eco = get_user_economy(target.id)
    stats = get_user_stats(target.id)
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {target.display_name}", color=0xD4AF37)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    
    if stats:
        gear_text = "\n".join([f"⚔️ {gear} (العدد: {count})" for gear, count in stats.items()])
    else:
        gear_text = "حقيبتك فارغة، توجه للمتاجر وتسوق الآن!"
        
    embed.add_field(name="🎒 حقيبة المعدات:", value=gear_text, inline=False)
    await interaction.followup.send(embed=embed)


# لوحة المطور المحدثة (بدون كتابة مزعجة)
@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطورين الحصرية")
@app_commands.choices(العملية=[
    app_commands.Choice(name="💰 بنك العملات (إضافة رصيد بلا حدود)", value="bank_add"),
    app_commands.Choice(name="⚔️ إهداء عتاد (عبر قائمة جاهزة)", value="give_gear"),
    app_commands.Choice(name="👥 إضافة مطور جديد للسيرفر", value="add_dev")
])
@app_commands.describe(العملية="اختر العملية", العضو="العضو المستهدف", كمية_العملات="اكتب عدد العملات فقط (في حال اخترت البنك)")
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
        # تفتح له قائمة منسدلة باختيار العتاد مباشرة بدون كتابة أسامي!
        await interaction.response.send_message(f"🛠️ اختر العتاد الذي تريد إهداءه إلى {العضو.mention} من القائمة أدناه:", view=DevGearSelect(العضو), ephemeral=True)
        
    elif op_val == "add_dev":
        EXTRA_DEVS.add(العضو.id)
        await interaction.response.send_message(f"🛡️ تم منح {العضو.mention} صلاحيات لوحة المطورين بنجاح.", ephemeral=True)

bot.run(os.getenv('TOKEN'))
