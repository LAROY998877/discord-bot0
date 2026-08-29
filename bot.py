import os
import random
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد مسار ثابت ودائم لقاعدة البيانات في مجلد العمل الحالي
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot_database.db")

db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = db_connection.cursor()

# إنشاء الجداول ودعم التحديث التلقائي للحقول إن وجدت مسبقاً
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        is_registered INTEGER DEFAULT 0,
        balance INTEGER DEFAULT 5000,
        equipment_score INTEGER DEFAULT 10,
        floors INTEGER DEFAULT 1,
        max_unlocked_floor INTEGER DEFAULT 1,
        hero_name TEXT DEFAULT 'لم يتم الاختيار',
        equipment_name TEXT DEFAULT 'لم يتم الاختيار',
        title TEXT DEFAULT 'مبتدئ',
        hide_stats INTEGER DEFAULT 0,
        hide_titles INTEGER DEFAULT 0
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS developers (
        user_id INTEGER PRIMARY KEY
    )
"""
)
db_connection.commit()

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
    print(f"قاعدة البيانات محفوظة في: {DB_PATH}")
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
# 2. نظام التسجيل التلقائي الذكي (Modal)
# ==========================================


class RegisterModal(discord.ui.Modal, title="التسجيل الإجباري الأول"):

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
                "❌ العمر يجب أن يكون أرقاماً صحيحة!", ephemeral=True
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
            f"✅ **تم تسجيلك بنجاح يابطل!**\n👤 الاسم: `{name}`\n🎂 العمر: `{age}`\n🚻 الجنس: `{gender}`\n\nالآن يمكنك خوض غمار برج الطوابق الألف!",
            ephemeral=True,
        )


@bot.tree.command(name="تسجيل", description="التسجيل في النظام لفتح جميع الأوامر")
async def register_command(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


# ==========================================
# 3. الملف الشخصي
# ==========================================


class EditTitleModal(discord.ui.Modal, title="تعديل اللقب الشخصي"):

    new_title = discord.ui.TextInput(
        label="اللقب الجديد",
        placeholder="اكتب لقبك الفانتازي الجديد...",
        required=True,
        max_length=30,
    )

    async def on_submit(self, interaction: discord.Interaction):
        cursor.execute(
            "UPDATE user_data SET title = ? WHERE user_id = ?",
            (self.new_title.value, interaction.user.id),
        )
        db_connection.commit()
        await interaction.response.send_message(
            f"✅ تم تحديث لقبك إلى: **{self.new_title.value}** بنجاح!",
            ephemeral=True,
        )


class ProfileControlView(discord.ui.View):

    def __init__(self, owner_id: int):
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ عذراً، هذا الملف الشخصي لا يخصك ولا يمكنك التعديل عليه!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="تعديل اللقب",
        style=discord.ButtonStyle.primary,
        emoji="✏️",
        row=0,
    )
    async def edit_title_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="إخفاء/إظهار المعدلات",
        style=discord.ButtonStyle.secondary,
        emoji="👁️",
        row=0,
    )
    async def toggle_stats_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT hide_stats FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current = cursor.fetchone()[0]
        new_val = 0 if current == 1 else 1
        cursor.execute(
            "UPDATE user_data SET hide_stats = ? WHERE user_id = ?",
            (new_val, interaction.user.id),
        )
        db_connection.commit()

        status_text = "مخفية 🔒" if new_val == 1 else "ظاهرة 🔓"
        await interaction.response.send_message(
            f"✅ تم تغيير حالة إخفاء المعدلات لتصبح: **{status_text}**",
            ephemeral=True,
        )

    @discord.ui.button(
        label="إخفاء/إظهار الألقاب",
        style=discord.ButtonStyle.secondary,
        emoji="🛡️",
        row=0,
    )
    async def toggle_titles_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT hide_titles FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current = cursor.fetchone()[0]
        new_val = 0 if current == 1 else 1
        cursor.execute(
            "UPDATE user_data SET hide_titles = ? WHERE user_id = ?",
            (new_val, interaction.user.id),
        )
        db_connection.commit()

        status_text = "مخفي 🔒" if new_val == 1 else "ظاهر 🔓"
        await interaction.response.send_message(
            f"✅ تم تغيير حالة إخفاء الألقاب لتصبح: **{status_text}**",
            ephemeral=True,
        )


@bot.tree.command(name="الملف", description="عرض الملف الشخصي")
@app_commands.describe(member="العضو المراد عرض ملفه (اختياري)")
async def profile_command(
    interaction: discord.Interaction, member: discord.Member = None
):
    target = member if member else interaction.user

    if not is_registered(target.id):
        if target.id == interaction.user.id:
            await interaction.response.send_modal(RegisterModal())
        else:
            await interaction.response.send_message(
                f"❌ المستخدم {target.mention} غير مسجل في النظام بعد!",
                ephemeral=True,
            )
        return

    cursor.execute(
        "SELECT name, age, gender, balance, equipment_score, floors, max_unlocked_floor, hero_name, equipment_name, title, hide_stats, hide_titles FROM user_data WHERE user_id = ?",
        (target.id,),
    )
    data = cursor.fetchone()
    (
        name,
        age,
        gender,
        balance,
        eq_score,
        floors,
        max_unlocked,
        hero,
        equipment,
        title,
        hide_stats,
        hide_titles,
    ) = data

    embed = discord.Embed(
        title=f"📜 الملف الشخصي لـ: {target.display_name}",
        color=discord.Color.dark_purple(),
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    display_title = "مخفي 🔒" if hide_titles == 1 else f"`{title}`"
    embed.add_field(name="🏷️ اللقب الشخصي", value=display_title, inline=False)

    embed.add_field(name="👤 الاسم الحقيقي", value=f"`{name}`", inline=True)
    embed.add_field(name="🎂 العمر", value=f"`{age}`", inline=True)
    embed.add_field(name="🚻 الجنس", value=f"`{gender}`", inline=True)

    if hide_stats == 1:
        embed.add_field(
            name="📊 المعدلات والقوة",
            value="*المعدلات مخفية بواسطة صاحب الملف 🔒*",
            inline=False,
        )
    else:
        embed.add_field(
            name="📊 المعدلات والقوة",
            value=(
                f"• الرصيد: `{balance}` 💎\n"
                f"• نقاط المعدات: `{eq_score}` ⚔️\n"
                f"• الطابق الحالي: `{floors}` 🏢 (أقصى طابق: {max_unlocked}/1000)\n"
                f"• البطل المختار: `{hero}` 🦸‍♂️\n"
                f"• العتاد الحالي: `{equipment}` 🗡️"
            ),
            inline=False,
        )

    view = ProfileControlView(target.id)
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================
# 4. نظام برج الطوابق الألف (1 إلى 1000) مع الـ Bosses والجوائز
# ==========================================


class FloorBattleView(discord.ui.View):

    def __init__(self, user_id: int, target_floor: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.target_floor = target_floor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه المعركة لا تخصك! ارفع طوابقك الخاصة عبر أمر `/الطوابق`.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="⚔️ هاجم زعيم الطابق!",
        style=discord.ButtonStyle.danger,
        emoji="🔥",
    )
    async def attack_boss(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id

        # جلب بيانات اللاعب وقوته
        cursor.execute(
            "SELECT equipment_score, balance, max_unlocked_floor FROM user_data WHERE user_id = ?",
            (user_id,),
        )
        eq_score, balance, max_unlocked = cursor.fetchone()

        # حساب صعوبة البوس بناءً على رقم الطابق (كلما زاد الطابق زادت الصعوبة وقوة البوس)
        boss_power = self.target_floor * 15 + random.randint(50, 200)
        player_total_power = eq_score + random.randint(10, 80)

        # أسماء زعماء عشوائية حسب مراحل الطوابق
        boss_names = [
            "حارس الظل الملعون",
            "ملك الغول الحديدي",
            "تنين الجحيم الرمادي",
            "سيد العواصف الشيطانية",
            "كارثة الأكوان المظلمة",
        ]
        boss_title = boss_names[
            min(self.target_floor // 200, len(boss_names) - 1)
        ]

        if player_total_power >= boss_power or self.target_floor <= max_unlocked:
            # ربح المعركة
            reward_coins = self.target_floor * 50 + random.randint(100, 500)
            reward_eq_score = self.target_floor * 2 + random.randint(5, 15)

            # أسماء عتاد بسيط ومتقدم يحصل عليه اللاعب
            loot_names = [
                "سيف برونزي مهترئ",
                "درع جلدي متين",
                "خنجر الصياد السريع",
                "صولجان الحارس القديم",
                "عباءة الظل الخفية",
                "رمح الفرسان الملكي",
            ]
            won_loot = random.choice(loot_names) + f" (طابق {self.target_floor})"

            new_max = (
                max(max_unlocked, self.target_floor + 1)
                if self.target_floor == max_unlocked
                else max_unlocked
            )
            next_floor = self.target_floor + 1 if new_max > max_unlocked else max_unlocked

            cursor.execute(
                """
                UPDATE user_data 
                SET balance = balance + ?, 
                    equipment_score = equipment_score + ?, 
                    floors = ?, 
                    max_unlocked_floor = ?,
                    equipment_name = ?
                WHERE user_id = ?
            """,
                (
                    reward_coins,
                    reward_eq_score,
                    self.target_floor,
                    new_max,
                    won_loot,
                    user_id,
                ),
            )
            db_connection.commit()

            embed = discord.Embed(
                title=f"🎉 انتصار ساحق في الطابق {self.target_floor}!",
                description=(
                    f"**⚔️ خصمك:** `{boss_title}` (قوة الزعيم: {boss_power})\n"
                    f"**🛡️ قوتك الإجمالية:** {player_total_power}\n\n"
                    f"🎁 **الغنائم والجوائز المكتسبة:**\n"
                    f"• عملات ذهبية: `+{reward_coins}` 💎\n"
                    f"• نقاط عتاد إضافية: `+{reward_eq_score}` ⚔️\n"
                    f"• العتاد المكتسب الجديد: **{won_loot}** 🛡️\n\n"
                    f"🚀 *تم فتح الطريق للصعود إلى الطابق التالي!*"
                ),
                color=discord.Color.green(),
            )
            embed.set_image(
                url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800"
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)

        else:
            # خسارة المعركة
            embed = discord.Embed(
                title=f"💀 هزيمة مريرة في الطابق {self.target_floor}!",
                description=(
                    f"**⚔️ خصمك الزعيم:** `{boss_title}` (قوة الزعيم: {boss_power})\n"
                    f"**🛡️ قوتك الإجمالية:** {player_total_power}\n\n"
                    f"❌ **السبب:** عتادك الحالي أو نقاط قوتك غير كافية لهزيمة هذا الزعيم المرعب في هذا العمق!\n"
                    f"💡 *نصيحة:* قم بتطوير عتادك عبر المتاجر أو كرر محاولة طوابق أقل لجمع نقاط قوة أعلى قبل العودة."
                ),
                color=discord.Color.dark_red(),
            )
            embed.set_image(
                url="https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800"
            )
            await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(
    name="الطوابق", description="اختر واصعد في برج الطوابق الألف (1 إلى 1000) وقاتل الزعماء للحصول على الغنائم"
)
@app_commands.describe(floor_number="رقم الطابق الذي ترغب في دخوله (من 1 إلى 1000)")
async def floors_command(
    interaction: discord.Interaction, floor_number: int = 1
):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    if floor_number < 1 or floor_number > 1000:
        await interaction.response.send_message(
            "❌ عذراً، برج الطوابق يتراوح بين الطابق **1** و **1000** كحد أقصى!",
            ephemeral=True,
        )
        return

    cursor.execute(
        "SELECT max_unlocked_floor, equipment_score FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    max_unlocked, eq_score = cursor.fetchone()

    if floor_number > max_unlocked:
        await interaction.response.send_message(
            f"❌ لا يمكنك دخول الطابق **{floor_number}** لأن أقصى طابق متاح لك فتحه هو `{max_unlocked}`! اكتسح الطوابق بترتيبها.",
            ephemeral=True,
        )
        return

    # حساب صعوبة الطابق المعروض
    difficulty_desc = (
        "سهل 🟢"
        if floor_number <= 100
        else (
            "متوسط 🟡"
            if floor_number <= 400
            else "صعب جداً 🔥" if floor_number <= 800 else "مستوى الهلاك الأبدي 💀"
        )
    )

    embed = discord.Embed(
        title=f"🏢 برج الطوابق الأسطوري - الطابق [{floor_number}/1000]",
        description=(
            f"مرحباً بك في أعماق الطابق رقم **{floor_number}**.\n"
            f"• مستوى الصعوبة: **{difficulty_desc}**\n"
            f"• قوتك الحالية للعتاد: `{eq_score}` ⚔️\n\n"
            f"⚠️ **تحذير:** ينتظرك زعيم شرس في هذا الطابق. هل أنت مستعد لخوض المعركة وربح العتاد والعملات؟"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"
    )

    view = FloorBattleView(interaction.user.id, floor_number)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 5. الأبطال الأسطوريين
# ==========================================
HEROES_DATA = {
    "arthur": {
        "title": "آرثر - فارس الظلال الملكي",
        "gender": "ذكر",
        "power": 950,
        "defense": 880,
        "story": "فارس محارب ارتدى درع الملوك الفولاذي، وحمل سيف النور المخضب بالنار ليطهر الأراضي من الوحوش الأسطورية.",
        "image": "https://images.unsplash.com/photo-1599839575945-a9e5af0c3fa5?w=800",
    },
    "zeus": {
        "title": "زيوس - إله الصواعق الأبدي",
        "gender": "ذكر",
        "power": 990,
        "defense": 750,
        "story": "سيد العواصف الذي يتسيد القمم العالية، يطلق رعداً يزلزل الجبال ويدمر جيوش الأعداء بلمح البصر.",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800",
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
        ]
        super().__init__(
            placeholder="اختر بطلاً أسطورياً لعرض قصته وصورته...",
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
            title=f"🛡️ استعراض البطل الفانتازي: {hero['title']}",
            description=(
                f"**📖 قصة البطل:**\n{hero['story']}\n\n"
                f"📊 **معدلات القوة:**\n"
                f"• قوة الهجوم: `{hero['power']}` ⚔️\n"
                f"• قوة الدفاع: `{hero['defense']}` 🛡️\n"
                f"• الجنس: `{hero['gender']}`\n\n"
                f"✅ *تم تعيين هذا البطل كبطل أساسي لحسابك!*"
            ),
            color=discord.Color.purple(),
        )
        embed.set_image(url=hero["image"])
        await interaction.response.edit_message(embed=embed, view=self.view)


class HeroMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HeroSelectDropdown())


@bot.tree.command(
    name="الابطال", description="فتح منيو الأبطال الفانتازيا وقصصهم الأسطورية"
)
async def heroes_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="🌟 قاعة الأبطال الفانتازيا الأسطوريين",
        description="اختر بطلاً من القائمة المنسدلة بالأسفل لاستعراض قصته ومعدلات قوته:",
        color=discord.Color.dark_gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"
    )
    view = HeroMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 6. المتاجر (المتجر العادي + متجر الظلام)
# ==========================================

NORMAL_SHOP_ITEMS = {
    "sword": {
        "title": "سيف اللهب الأبدي",
        "price": "250 💎",
        "damage": "+50 هجوم",
        "desc": "سيف مشتعل بنيران التنانين القديمة.",
        "image": "https://images.unsplash.com/photo-1589241062272-c0a000071dfa?w=800",
    },
    "hammer": {
        "title": "مطرقة الرعد الكونية",
        "price": "320 💎",
        "damage": "+70 تحطيم",
        "desc": "مطرقة مصممة من نيازك ساطعة.",
        "image": "https://images.unsplash.com/photo-1601933470077-0afdd71f5424?w=800",
    },
}


class NormalShopDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="سيف اللهب الأبدي",
                description="السعر: 250 💎",
                emoji="⚔️",
                value="sword",
            ),
            discord.SelectOption(
                label="مطرقة الرعد الكونية",
                description="السعر: 320 💎",
                emoji="🔨",
                value="hammer",
            ),
        ]
        super().__init__(
            placeholder="اختر معدة من المتجر العادي...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        item = NORMAL_SHOP_ITEMS[choice]
        user_id = interaction.user.id

        cursor.execute(
            "UPDATE user_data SET equipment_name = ?, equipment_score = equipment_score + 30 WHERE user_id = ?",
            (item["title"], user_id),
        )
        db_connection.commit()

        await interaction.response.send_message(
            f"✅ تم شراء وتجهيز `{item['title']}` بنجاح وزادت قوتك!",
            ephemeral=True,
        )


class NormalShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(NormalShopDropdown())


@bot.tree.command(name="المتجر", description="فتح المتجر العادي للأسلحة")
async def shop_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="🛍️ المتجر العادي الإمبراطوري",
        description="اختر سلاحاً لتعزيز قوتك في الطوابق:",
        color=discord.Color.gold(),
    )
    view = NormalShopView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


DARK_SHOP_ITEMS = {
    "dark_blade": {
        "title": "شفرة الموت المظلمة",
        "price": "666 💎",
        "damage": "+150 هجوم شيطاني",
        "desc": "شفرة مسحورة تنبعث منها طاقة الهلاك.",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800",
    },
}


class DarkShopDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="شفرة الموت المظلمة",
                description="السعر: 666 💎",
                emoji="🗡️",
                value="dark_blade",
            )
        ]
        super().__init__(
            placeholder="اختر سلاحاً محرماً من متجر الظلام...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        item = DARK_SHOP_ITEMS[choice]
        user_id = interaction.user.id

        cursor.execute(
            "UPDATE user_data SET equipment_name = ?, equipment_score = equipment_score + 80 WHERE user_id = ?",
            (item["title"], user_id),
        )
        db_connection.commit()

        await interaction.response.send_message(
            f"💀 عقدت صفقة مظلمة وتم تجهيز `{item['title']}` بنجاح!",
            ephemeral=True,
        )


class DarkShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(DarkShopDropdown())


@bot.tree.command(name="متجر_الظلام", description="فتح متجر الظلام السري")
async def dark_shop_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="🌑 متجر الظلام السري",
        description="أسلحة محرمة تمنحك قوة هائلة لاكتساح الطوابق:",
        color=discord.Color.dark_red(),
    )
    view = DarkShopView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 7. البنك ولوحة المطورين
# ==========================================


class BankMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إيداع بالتوفير (+50 جوهرة)",
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
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="✨ منيو المصرف الإمبراطوري",
        description="احصل على رصيد لدعم رحلتك:",
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

        embed = discord.Embed(
            title="⚡ منيو لوحة تحكم المطورين",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين",
            value=f"`{total_users}` مسجل",
            inline=True,
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
        description="اختر الخيار المناسب:",
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
# 8. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
