import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجداول
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

# جدول بيانات المستخدمين والشروط الجديدة (الاسم، العمر، الجنس، والبطل المختار)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        is_registered INTEGER DEFAULT 0,
        balance INTEGER DEFAULT 100,
        equipment_score INTEGER DEFAULT 10,
        floors INTEGER DEFAULT 1,
        hero_name TEXT DEFAULT 'لم يتم الاختيار'
    )
"""
)

# جدول المطورين المصرح لهم
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS developers (
        user_id INTEGER PRIMARY KEY
    )
"""
)
db_connection.commit()

# 2. إعداد البوت والصلاحيات
intents = discord.Intents.default()
intents.members = True
intents.guilds = True


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تم مزامنة أوامر السلاش بنجاح!")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"-----------------------------------------")
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})")
    print(f"البوت متصل حالياً في {len(bot.guilds)} سيرفر/ات.")
    print(f"-----------------------------------------")


def is_dev(user_id: int) -> bool:
    cursor.execute("SELECT user_id FROM developers WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


def is_registered(user_id: int) -> bool:
    cursor.execute(
        "SELECT is_registered FROM user_data WHERE user_id = ?", (user_id,)
    )
    result = cursor.fetchone()
    if result and result[0] == 1:
        return True
    return False


# ==========================================
# 3. نظام التسجيل (Modal & Command)
# ==========================================


class RegisterModal(discord.ui.Modal, title="نظام التسجيل الإجباري"):

    name_input = discord.ui.TextInput(
        label="الاسم الكامل", placeholder="اكتب اسمك هنا...", required=True
    )
    age_input = discord.ui.TextInput(
        label="العمر", placeholder="اكتب عمرك (أرقام فقط)...", required=True
    )
    gender_input = discord.ui.TextInput(
        label="الجنس", placeholder="ذكر / أنثى", required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = str(interaction.user)
        name = self.name_input.value
        age = self.age_input.value
        gender = self.gender_input.value

        if not age.isdigit():
            await interaction.response.send_message(
                "❌ العمر يجب أن يكون أرقاماً صحيحة! يرجى إعادة المحاولة.",
                ephemeral=True,
            )
            return

        cursor.execute(
            """
            INSERT INTO user_data (user_id, username, name, age, gender, is_registered)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name, age=excluded.age, gender=excluded.gender, is_registered=1
        """,
            (user_id, username, name, int(age), gender),
        )
        db_connection.commit()

        await interaction.response.send_message(
            f"✅ **تم تسجيلك بنجاح!**\n👤 الاسم: `{name}`\n🎂 العمر: `{age}`\n🚻 الجنس: `{gender}`\n\nالآن يمكنك استخدام الأوامر وقوائم المنيو بحرية!",
            ephemeral=True,
        )


@bot.tree.command(name="تسجيل", description="التسجيل في النظام لفتح جميع الأوامر والمنيو")
async def register_command(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


# ==========================================
# 4. شخصية "السفاح" (خاصة بالمطورين فقط)
# ==========================================


@bot.tree.command(name="السفاح", description="[خاص بالمطورين] استدعاء شخصية السفاح المرعبة")
async def assassin_command(interaction: discord.Interaction):
    # التأكد من أن المستخدم مطور أو مالك السيرفر
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT OR IGNORE INTO developers (user_id) VALUES (?)",
            (interaction.user.id,),
        )
        db_connection.commit()

    if (
        not is_dev(interaction.user.id)
        and interaction.user.id != interaction.guild.owner_id
    ):
        await interaction.response.send_message(
            "❌ **خطأ أمني:** هذا الأمر مرعب وخاص بالمطورين المعتمدين فقط ولا يمكن للعامة استخدامه!",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="🩸 السفاح - كابوس الظلال المطلق",
        description=(
            "**📖 القصة المرعبة:**\n"
            "في أعمق قيعان الجحيم الرقمي، حيث تتساقط أرواح الأكواد التالفة، وُلد السفاح.\n"
            "كيان شيطاني لا يرحم، يرتدي قناعاً متآكلاً من الديحان، ويحمل منجلًا مصبوغًا بدماء من حاولوا عبثاً اختراق الأنظمة الإمبراطورية.\n"
            "لا صرخات تنفع أمامه، ولا دفاعات تصد ضرباته.. إنه الحارس الشخصي للمطورين والجلاد الأكبر لكل متطفل!\n\n"
            "📊 **معدلات القوة المرعبة:**\n"
            "• قوة الفتاك: `999,999` 🔪\n"
            "• رعب الدمار: `لا نهائي` 💀\n"
            "• نسبة النجاة منه: `0%`\n\n"
            "⚠️ *تحذير: حضور هذا الكيان يعني أن الإمبراطورية تحت السيطرة المطلقة للمطور.*"
        ),
        color=discord.Color.dark_red(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500"
    )
    embed.set_footer(
        text=f"استدعاء سري بواسطة المطور: {interaction.user.display_name}"
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# 5. نظام الأبطال العاديين (6 أبطال)
# ==========================================
HEROES_DATA = {
    "arthur": {
        "title": "آرثر - فارس الظلال",
        "gender": "ذكر",
        "power": 950,
        "defense": 880,
        "story": "فارس محارب عانى من دمار مملكته، فحمل سيف النور المقدس ليطهر الأراضي من قوى الظلام وينتقم لشعبه.",
        "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=500",
    },
    "zeus": {
        "title": "زيوس - سيده الصواعق",
        "gender": "ذكر",
        "power": 990,
        "defense": 750,
        "story": "إله الرعد الأسطوري، وُلد وسط العواصف العاتية، يمتلك القدرة على تدمير الأعداء بصاعقة واحدة تهز الأكوان.",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500",
    },
    "kane": {
        "title": "كين - قناص البراري",
        "gender": "ذكر",
        "power": 890,
        "defense": 810,
        "story": "مقاتل خفي عاش في الغابات المظلمة، لا يخطئ هدفه أبداً، ويعتبر أشرس مرتزق في القارة.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?w=500",
    },
    "athena": {
        "title": "أثينا - حارسة المعابد",
        "gender": "أنثى",
        "power": 930,
        "defense": 920,
        "story": "إلهة الحكمة والقتال، قادت الجيوش بحنكة لا نظير لها، درعها لا ينكسر وسيفها يفرق بين الحق والباطل.",
        "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500",
    },
    "valkyrie": {
        "title": "فالكيري - محاربة الفضاء",
        "gender": "أنثى",
        "power": 970,
        "defense": 830,
        "story": "مقاتلة شرسة تهبط من سماء الأساطير لتختار الأرواح الشجاعة في ساحات المعارك الكبرى.",
        "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=500",
    },
    "selene": {
        "title": "سيلين - أميرة القمريات",
        "gender": "أنثى",
        "power": 910,
        "defense": 860,
        "story": "ساحرة الليل الأبدي، تستمد قوتها من ضوء القمر لتجميد الخصوم وإلقاء تعويذات مدمرة لا تُرد.",
        "image": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=500",
    },
}


class HeroSelectDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="آرثر (فارس الظلال)",
                description="ذكر | قوة عالية وسيف مقدس",
                emoji="⚔️",
                value="arthur",
            ),
            discord.SelectOption(
                label="زيوس (سيد الصواعق)",
                description="ذكر | طاقة رعدية مدمرة",
                emoji="⚡",
                value="zeus",
            ),
            discord.SelectOption(
                label="كين (قناص البراري)",
                description="ذكر | دقة واستخبارات قتالية",
                emoji="🏹",
                value="kane",
            ),
            discord.SelectOption(
                label="أثينا (حارسة المعابد)",
                description="أنثى | دفاع أسطوري وحكمة",
                emoji="🛡️",
                value="athena",
            ),
            discord.SelectOption(
                label="فالكيري (محاربة الفضاء)",
                description="أنثى | سرعة وهجوم خاطف",
                emoji="🪽",
                value="valkyrie",
            ),
            discord.SelectOption(
                label="سيلين (أميرة القمريات)",
                description="أنثى | سحر قمري مرعب",
                emoji="🌙",
                value="selene",
            ),
        ]
        super().__init__(
            placeholder="اختر بطلاً لعرض تفاصيله وقصته...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        hero = HEROES_DATA[choice]
        user_id = interaction.user.id

        cursor.execute(
            "UPDATE user_data SET hero_name = ? WHERE user_id = ?",
            (hero["title"], user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title=f"🛡️ استعراض البطل: {hero['title']}",
            description=(
                f"**📖 قصة البطل:**\n{hero['story']}\n\n"
                f"📊 **معدلات القوة:**\n"
                f"• قوة الهجوم: `{hero['power']}` ⚔️\n"
                f"• قوة الدفاع: `{hero['defense']}` 🛡️\n"
                f"• الجنس: `{hero['gender']}`\n\n"
                f"✅ *تم تعيين هذا البطل كبطل أساسي لحسابك تلقائياً!*"
            ),
            color=discord.Color.purple(),
        )
        embed.set_image(url=hero["image"])
        embed.set_footer(
            text=f"تم الاختيار بواسطة: {interaction.user.display_name}"
        )

        await interaction.response.edit_message(embed=embed, view=self.view)


class HeroMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HeroSelectDropdown())


@bot.tree.command(name="الابطال", description="فتح منيو اختيار الأبطال وقصصهم وقوتهم")
async def heroes_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_message(
            "❌ **عذراً!** يجب عليك التسجيل أولاً لاستخدام منيو الأبطال.\nاستخدم أمر: `/تسجيل`",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="🌟 ساحة الأبطال الأسطوريين",
        description=(
            "مرحباً بك في قاعة الأبطال.\n"
            "اختر بطلاً من القائمة المنسدلة بالأسفل لاستعراض **قصته، صورته الخاصة، ومعدلات قوته ودفاعه**!"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500"
    )

    view = HeroMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 6. الأوامر الأخرى (البنك والمطورين)
# ==========================================


class BankMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إيداع بالتوفير",
        style=discord.ButtonStyle.success,
        emoji="📥",
        row=0,
    )
    async def deposit(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        cursor.execute(
            "UPDATE user_data SET balance = balance + 50 WHERE user_id = ?",
            (user_id,),
        )
        db_connection.commit()
        cursor.execute(
            "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
        )
        new_balance = cursor.fetchone()[0]
        await interaction.response.send_message(
            f"✅ تم الإيداع بنجاح! رصيدك الحالي: `{new_balance}` 💎",
            ephemeral=True,
        )


@bot.tree.command(name="البنك", description="فتح منيو المصرف الإمبراطوري")
async def bank_panel(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_message(
            "❌ التسجيل إجباري أولاً عبر أمر: `/تسجيل`", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✨ منيو المصرف الإمبراطوري",
        description="اختر العملية التي تريد تنفيذها:",
        color=discord.Color.gold(),
    )
    view = BankMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(
        label="إحصائيات والأوامر",
        style=discord.ButtonStyle.blurple,
        emoji="📊",
        row=0,
    )
    async def stats_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT COUNT(*) FROM user_data WHERE is_registered=1")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM developers")
        total_devs = cursor.fetchone()[0]

        synced_commands = bot.tree.get_commands()
        commands_list = (
            ", ".join([f"`/{cmd.name}`" for cmd in synced_commands])
            if synced_commands
            else "لا توجد"
        )

        embed = discord.Embed(
            title="⚡ منيو لوحة تحكم المطورين",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين",
            value=f"`{total_users}` مسجل",
            inline=True,
        )
        embed.add_field(
            name="🛡️ عدد المطورين", value=f"`{total_devs}` مطور", inline=True
        )
        embed.add_field(
            name="📌 الأوامر المضافة تلقائياً",
            value=commands_list,
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(name="مطور", description="فتح منيو لوحة تحكم المطورين")
async def dev_panel(interaction: discord.Interaction):
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT OR IGNORE INTO developers (user_id) VALUES (?)",
            (interaction.user.id,),
        )
        db_connection.commit()

    if (
        not is_dev(interaction.user.id)
        and interaction.user.id != interaction.guild.owner_id
    ):
        await interaction.response.send_message(
            "❌ عذراً، هذا الأمر مخصص للمطورين فقط.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✨ منيو الإدارة المركزية للمطورين",
        description="اختر الخيار المناسب من الأزرار أدناه:",
        color=discord.Color.from_rgb(40, 40, 45),
    )
    view = DevPanelView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="اضافة_مطور", description="إضافة مطور جديد للنظام")
@app_commands.describe(member="العضو المراد ترقيته")
async def add_developer(interaction: discord.Interaction, member: discord.Member):
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] > 0 and not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ هذا الأمر للمطورين فقط!", ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO developers (user_id) VALUES (?)", (member.id,)
    )
    db_connection.commit()
    await interaction.response.send_message(
        f"✅ تم تعيين {member.mention} مطوراً بنجاح!", ephemeral=True
    )


# ==========================================
# 7. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
