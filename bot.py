import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DEVELOPER_ID = 1103985971638325269
EXTRA_DEVS = set()

# بيانات وهمية للتخزين المؤقت
USER_ECONOMY = {}
USER_STATS = {}
USER_EQUIPPED = {}
REGISTERED_USERS = {}
GUILDS_DATA = {}

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

# ==================== المتاجر (معدات ضخمة ومختلفة المعدلات) ====================
NORMAL_SHOP = {
    "سيف التدريب الخشبي": {"price": 50, "attack": 10, "desc": "سيف خفيف للتدريب الأساسي."},
    "خنجر الصیاد السريع": {"price": 120, "attack": 25, "desc": "خنجر رشق سريع الطعنات."},
    "سيف الفارس الفولاذي": {"price": 300, "attack": 55, "desc": "سيف حديدي متين وقوي."},
    "رمح الحراس": {"price": 450, "attack": 75, "desc": "رمح طويل لإبعاد الأعداء."},
    "درع الجلد الطبيعي": {"price": 100, "defense": 20, "desc": "درع يحمي من الضربات الخفيفة."},
    "درع الفولاذ المقاوم": {"price": 350, "defense": 60, "desc": "درع صلب يمتص الصدمات القوية."},
    "خوذة الحراسة الملكية": {"price": 200, "defense": 35, "desc": "خوذة تحمي الرأس من الإصابات الحرجة."},
    "قوس الرماة الخشبي": {"price": 250, "attack": 40, "desc": "قوس تقليدي بدقة متوسطة."},
    "فأس الحطاب الثقيلة": {"price": 500, "attack": 90, "desc": "فأس ضخمة تحدث أضراراً بالغة."},
    "درع النحاس المرصع": {"price": 280, "defense": 45, "desc": "درع نحاسي جيد ضد الضربات الحادة."},
    "سيف الحرس الملكي": {"price": 600, "attack": 110, "desc": "سيف رسمي مصقول بعناية فائقة."},
    "خنجر السم الخفي": {"price": 400, "attack": 85, "desc": "خنجر صغير مغطى بسم خفيف."}
}

DARK_SHOP = {
    "نصل الجحيم المحرق": {"price": 1500, "attack": 220, "desc": "سيف مشتعل بنيران الحمم البركانية."},
    "خنجر التنين الأسود": {"price": 2200, "attack": 310, "desc": "مصنوع من مخالب التنانين القديمة."},
    "سيف الموت الأبدي": {"price": 4000, "attack": 500, "desc": "يشع طاقة مظلمة تفتك بالأرواح."},
    "صولجان الخراب المظلم": {"price": 6500, "attack": 750, "desc": "سلاح الدمار الشامل في الحروب الكبرى."},
    "درع الروح التائهة": {"price": 1800, "defense": 300, "desc": "يحاط بدرع شبحي يصد الضربات السحرية."},
    "عباءة التخفي المطلق": {"price": 2500, "defense": 400, "desc": "تجعل مرتديها غير مرئي في الظلام."},
    "خوذة التنين المرعبة": {"price": 3000, "defense": 500, "desc": "تبث الرعب في قلوب الخصوم قبل النزال."},
    "درع الفوضى المطلقة": {"price": 8000, "defense": 1200, "desc": "درع أسطوري لا يمكن اختراقه أبداً."},
    "رمح الشياطين الدموي": {"price": 5000, "attack": 580, "desc": "رمح طويل يمتص دماء الأعداء عند طعنهم."},
    "مطرقة التيتان المظلمة": {"price": 9500, "attack": 1400, "desc": "مطرقة ثقيلة تهز الأرض وتدمر الحصون."},
    "شفرة الأبعاد الساقطة": {"price": 12000, "attack": 1850, "desc": "سيف أسطوري يقطع نسيج الزمان والمكان."},
    "درع الظلال المطلقة": {"price": 11000, "defense": 1600, "desc": "درع يعكس الهجمات السحرية بالكامل."}
}

# ==================== أمر الملف الشخصي ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي (مرئي للعامة وبدون تعديل لغيرك)")
async def profile(interaction: discord.Interaction):
    target = interaction.user
    eco = get_user_economy(target.id)
    equipped = USER_EQUIPPED.get(target.id, "لا يوجد سلاح مركب حالياً")
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {target.display_name}", color=0xE67E22)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="🛡️ العتاد المُركب:", value=f"`{equipped}`", inline=False)
    
    # يظهر للجميع دون خيارات أو معاينة لملفات الآخرين
    await interaction.response.send_message(embed=embed, ephemeral=False)

# ==================== لوحة المطور ====================
@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم خاصة بالمطور فقط")
@app_commands.choices(الإجراء=[
    app_commands.Choice(name="💰 إضافة عملات للاعب", value="add_coins"),
    app_commands.Choice(name="🔨 إضافة مطور جديد", value="add_dev")
])
@app_commands.describe(الإجراء="اختر الإجراء المطلوب", اللاعب="المستهدف", القيمة="عدد العملات المضافة")
async def developer_panel(interaction: discord.Interaction, الإجراء: app_commands.Choice[str], اللاعب: discord.Member, القيمة: int = 0):
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمطور الأساسي والمطورين الإضافيين فقط!", ephemeral=True)
        return

    if الإجراء.value == "add_coins":
        eco = get_user_economy(اللاعب.id)
        eco["coins"] += القيمة
        await interaction.response.send_message(f"✅ تم إضافة `{القيمة}` عملة إلى رصيد {اللاعب.mention} بنجاح.", ephemeral=True)
    elif الإجراء.value == "add_dev":
        EXTRA_DEVS.add(اللاعب.id)
        await interaction.response.send_message(f"👑 تم تعيين {اللاعب.mention} كمطور إضافي بنجاح!", ephemeral=True)

# ==================== نظام المعارك (غرفة مخصصة ومشاهدة عامة) ====================
class BattleAcceptView(discord.ui.View):
    def __init__(self, challenger, opponent, battle_channel):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponent = opponent
        self.battle_channel = battle_channel
        self.accepted = False

    @discord.ui.button(label="⚔️ دخول المعركة", style=discord.ButtonStyle.green)
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ أنت لست المستهدف بهذا التحدي!", ephemeral=True)
            return
            
        self.accepted = True
        winning_side = random.choice([self.challenger, self.opponent])
        
        res_embed = discord.Embed(
            title="🏆 انتهت المعركة الأسطورية!",
            description=f"🔥 الفائز في هذه المعركة هو: **{winning_side.display_name}**!\n\n*(سيتم إغلاق وحذف هذه الغرفة المؤقتة خلال 10 ثوانٍ)*",
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=res_embed)
        
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        import asyncio
        await asyncio.sleep(10)
        try:
            await self.battle_channel.delete()
        except:
            pass
        self.stop()

@bot.tree.command(name="معركة", description="بدء معركة أسطورية في غرفة مؤقتة مخصصة يمكن للجميع مشاهدتها")
@app_commands.describe(الخصم="اختر الشخص الذي تريد تحديه")
async def battles(interaction: discord.Interaction, الخصم: discord.Member):
    if الخصم == interaction.user:
        await interaction.response.send_message("❌ لا يمكنك تحدي نفسك!", ephemeral=True)
        return

    guild = interaction.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), # المشاهدون يمكنهم القراءة فقط
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        الخصم: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    category = interaction.channel.category
    battle_channel = await guild.create_text_channel(
        name=f"⚔️-معركة-{interaction.user.name}",
        category=category,
        overwrites=overwrites,
        topic=f"غرفة معركة حية بين {interaction.user.name} و {الخصم.name}. المشاهدة متاحة للجميع."
    )

    embed = discord.Embed(
        title="🏟️ حلبة المعارك الحية",
        description=f"المتحدي: {interaction.user.mention}\nالخصم المستهدف: {الخصم.mention}\n\n*(تم إنشاء هذه الغرفة خصيصاً للمعركة، يمكن للجميع المشاهدة)*",
        color=0xE74C3C
    )
    
    view = BattleAcceptView(interaction.user, الخصم, battle_channel)
    await battle_channel.send(content=f"{الخصم.mention}، لقد تم تحديك من قبل {interaction.user.mention}!", embed=embed, view=view)
    
    await interaction.response.send_message(f"✅ تم إنشاء غرفة المعركة بنجاح: {battle_channel.mention}", ephemeral=True)

# ==================== أوامر المتاجر ====================
def format_shop_items(shop_dict):
    text = ""
    for name, data in shop_dict.items():
        stat_type = "هجوم" if "attack" in data else "دفاع"
        stat_val = data.get("attack", data.get("defense", 0))
        text += f"🔹 **{name}**\n💰 السعر: `{data['price']}` | ⚡ {stat_type}: `+{stat_val}`\n📜 {data['desc']}\n\n"
    return text

@bot.tree.command(name="متجر_العادي", description="عرض متجر المعدات العادية الشامل")
async def normal_shop_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمعدات", description=format_shop_items(NORMAL_SHOP), color=0x3498DB)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="متجر_الظلام", description="عرض متجر الظلام الأسطوري للأسلحة الفتاكة")
async def dark_shop_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🖤 متجر الظلام الأسطوري", description=format_shop_items(DARK_SHOP), color=0x992d22)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(os.getenv('TOKEN'))
