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

# قاعدة بيانات وهمية لتخزين البيانات الأساسية
USER_ECONOMY = {}
USER_STATS = {}
USER_EQUIPPED = {}
REGISTERED_USERS = {}
GUILDS_DATA = {}

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 5000}
    return USER_ECONOMY[user_id]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

# ==================== 1. نظام التسجيل واختيار الشخصيات ====================
class CharacterSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر شخصيتك الأساسية...",
        options=[
            discord.SelectOption(label="محارب", description="قوة دفاعية وعضلية عالية", emoji="🛡️"),
            discord.SelectOption(label="مقاتل", description="أضرار هجومية سريعة وعالية", emoji="⚔️"),
            discord.SelectOption(label="ساحر", description="مهارات سحرية ودمار واسع", emoji="🔮"),
            discord.SelectOption(label="قاتل", description="سرعة فائقة وضربات حرجة", emoji="🗡️")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        chosen_char = select.values[0]
        REGISTERED_USERS[interaction.user.id] = {
            "character": chosen_char,
            "level": 1,
            "hp": 100
        }
        await interaction.response.send_message(f"✅ تم اختيار شخصية **{chosen_char}** بنجاح! تم تسجيلك في اللعبة.", ephemeral=True)

@bot.tree.command(name="تسجيل", description="تسجيل حسابك واختيار شخصيتك في اللعبة")
async def register(interaction: discord.Interaction):
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل بالفعل مسبقاً!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🎮 التسجيل واختيار الشخصية", description="اختر فئة شخصيتك من القائمة أدناه للبدء:", color=0x2ECC71)
    await interaction.response.send_message(embed=embed, view=CharacterSelectView(), ephemeral=True)


# ==================== 2. نظام النقابات (القديم + المطور) ====================
@bot.tree.command(name="انشاء_نقابة", description="إنشاء نقابة جديدة خاصة بك")
@app_commands.describe(اسم_النقابة="اسم النقابة التي تريد تأسيسها")
async def create_guild(interaction: discord.Interaction, اسم_النقابة: str):
    user_id = interaction.user.id
    if user_id in GUILDS_DATA.values():
        await interaction.response.send_message("❌ أنت منضم أو تمتلك نقابة بالفعل!", ephemeral=True)
        return
    
    GUILDS_DATA[اسم_النقابة] = {"owner": user_id, "members": [user_id]}
    await interaction.response.send_message(f"🏰 تم تأسيس نقابة **{اسم_النقابة}** بنجاح وأنت قائدها!", ephemeral=False)

@bot.tree.command(name="نقابتي", description="عرض معلومات نقابتك الحالية")
async def my_guild(interaction: discord.Interaction):
    user_id = interaction.user.id
    found_guild = None
    for g_name, g_info in GUILDS_DATA.items():
        if user_id in g_info["members"]:
            found_guild = g_name
            break
            
    if not found_guild:
        await interaction.response.send_message("❌ أنت لست منضماً لأي نقابة حالياً!", ephemeral=True)
        return
        
    await interaction.response.send_message(f"🛡️ أنت تنتمي إلى نقابة: **{found_guild}**", ephemeral=True)


# ==================== 3. أمر الملف الشخصي (المعدل المطلوب) ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي (مرئي للعامة وبدون تعديل لغيرك)")
async def profile(interaction: discord.Interaction):
    target = interaction.user
    eco = get_user_economy(target.id)
    char_info = REGISTERED_USERS.get(target.id, {"character": "غير مسجل", "level": 1})
    equipped = USER_EQUIPPED.get(target.id, "لا يوجد سلاح مركب")
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {target.display_name}", color=0xE67E22)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🏷️ الشخصية:", value=f"`{char_info['character']}` (مستوى {char_info.get('level', 1)})", inline=False)
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="🛡️ العتاد المُركب:", value=f"`{equipped}`", inline=False)
    
    # يظهر للعامة ولصاحبه فقط، بدون أي قوائم معاينة للآخرين
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ==================== 4. لوحة المطور ====================
@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم خاصة بالمطور فقط")
@app_commands.choices(الإجراء=[
    app_commands.Choice(name="💰 إضافة عملات للاعب", value="add_coins"),
    app_commands.Choice(name="🔨 إضافة مطور جديد", value="add_dev")
])
@app_commands.describe(الإجراء="اختر الإجراء المطلوب", اللاعب="المستهدف", القيمة="عدد العملات المضافة")
async def developer_panel(interaction: discord.Interaction, الإجراء: app_commands.Choice[str], اللاعب: discord.Member, القيمة: int = 0):
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ هذا الأمر مخصص للمطورين فقط!", ephemeral=True)
        return

    if الإجراء.value == "add_coins":
        eco = get_user_economy(اللاعب.id)
        eco["coins"] += القيمة
        await interaction.response.send_message(f"✅ تم إضافة `{القيمة}` عملة إلى رصيد {اللاعب.mention} بنجاح.", ephemeral=True)
    elif الإجراء.value == "add_dev":
        EXTRA_DEVS.add(اللاعب.id)
        await interaction.response.send_message(f"👑 تم تعيين {اللاعب.mention} كمطور إضافي بنجاح!", ephemeral=True)


# ==================== 5. نظام المعارك (روم خاص ومشاهدة للجميع) ====================
class BattleAcceptView(discord.ui.View):
    def __init__(self, challenger, opponent, battle_channel):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponent = opponent
        self.battle_channel = battle_channel

    @discord.ui.button(label="⚔️ دخول المعركة", style=discord.ButtonStyle.green)
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ أنت لست المستهدف بهذا التحدي!", ephemeral=True)
            return
            
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

@bot.tree.command(name="معركة", description="بدء معركة في روم مؤقت ومخصص يمكن للجميع مشاهدته")
@app_commands.describe(الخصم="اختر الشخص الذي تريد تحديه")
async def battles(interaction: discord.Interaction, الخصم: discord.Member):
    if الخصم == interaction.user:
        await interaction.response.send_message("❌ لا يمكنك تحدي نفسك!", ephemeral=True)
        return

    guild = interaction.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), # المشاهدون للقراءة فقط
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
        description=f"المتحدي: {interaction.user.mention}\nالخصم المستهدف: {الخصم.mention}\n\n*(تم إنشاء هذه الغرفة خصيصاً للمعركة، ويمكن للجميع المشاهدة)*",
        color=0xE74C3C
    )
    
    view = BattleAcceptView(interaction.user, الخصم, battle_channel)
    await battle_channel.send(content=f"{الخصم.mention}، لقد تم تحديك من قبل {interaction.user.mention}!", embed=embed, view=view)
    
    await interaction.response.send_message(f"✅ تم إنشاء غرفة المعركة بنجاح: {battle_channel.mention}", ephemeral=True)


# ==================== 6. المتاجر (معدات كثيرة ومختلفة المعدلات) ====================
NORMAL_SHOP = {
    "سيف التدريب الخشبي": {"price": 50, "attack": 10, "desc": "سيف خفيف للتدريب الأساسي."},
    "خنجر الصياد السريع": {"price": 120, "attack": 25, "desc": "خنجر رشق سريع الطعنات."},
    "سيف الفارس الفولاذي": {"price": 300, "attack": 55, "desc": "سيف حديدي متين وقوي."},
    "رمح الحراس": {"price": 450, "attack": 75, "desc": "رمح طويل لإبعاد الأعداء."},
    "درع الجلد الطبيعي": {"price": 100, "defense": 20, "desc": "درع يحمي من الضربات الخفيفة."},
    "درع الفولاذ المقاوم": {"price": 350, "defense": 60, "desc": "درع صلب يمتص الصدمات القوية."},
    "خوذة الحراسة الملكية": {"price": 200, "defense": 35, "desc": "خوذة تحمي الرأس من الإصابات."},
    "قوس الرماة الخشبي": {"price": 250, "attack": 40, "desc": "قوس تقليدي بدقة متوسطة."},
    "فأس الحطاب الثقيلة": {"price": 500, "attack": 90, "desc": "فأس ضخمة تحدث أضراراً بالغة."},
    "درع النحاس المرصع": {"price": 280, "defense": 45, "desc": "درع نحاسي جيد ضد الضربات الحادة."}
}

DARK_SHOP = {
    "نصل الجحيم المحرق": {"price": 1500, "attack": 220, "desc": "سيف مشتعل بنيران الحمم البركانية."},
    "خنجر التنين الأسود": {"price": 2200, "attack": 310, "desc": "مصنوع من مخالب التنانين القديمة."},
    "سيف الموت الأبدي": {"price": 4000, "attack": 500, "desc": "يشع طاقة مظلمة تفتك بالأرواح."},
    "صولجان الخراب المظلم": {"price": 6500, "attack": 750, "desc": "سلاح الدمار الشامل في الحروب."},
    "درع الروح التائهة": {"price": 1800, "defense": 300, "desc": "يحاط بدرع شبحي يصد الضربات السحرية."},
    "عباءة التخفي المطلق": {"price": 2500, "defense": 400, "desc": "تجعل مرتديها غير مرئي في الظلام."},
    "خوذة التنين المرعبة": {"price": 3000, "defense": 500, "desc": "تبث الرعب في قلوب الخصوم قبل النزال."},
    "درع الفوضى المطلقة": {"price": 8000, "defense": 1200, "desc": "درع أسطوري لا يمكن اختراقه أبداً."}
}

def format_shop_items(shop_dict):
    text = ""
    for name, data in shop_dict.items():
        stat_type = "هجوم" if "attack" in data else "دفاع"
        stat_val = data.get("attack", data.get("defense", 0))
        text += f"🔹 **{name}**\n💰 السعر: `{data['price']}` | ⚡ {stat_type}: `+{stat_val}`\n📜 {data['desc']}\n\n"
    return text

@bot.tree.command(name="متجر", description="عرض المتجر العادي للمعدات والأسلحة")
async def normal_shop_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمعدات", description=format_shop_items(NORMAL_SHOP), color=0x3498DB)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="متجر_الظلام", description="عرض متجر الظلام الأسطوري للأسلحة والعتاد الفتاك")
async def dark_shop_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🖤 متجر الظلام الأسطوري", description=format_shop_items(DARK_SHOP), color=0x992d22)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(os.getenv('TOKEN')
