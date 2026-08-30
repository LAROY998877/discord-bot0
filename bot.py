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
        is_registered INTEGER DEFAULT 1,
        balance INTEGER DEFAULT 5000,
        bank_balance INTEGER DEFAULT 0,
        loan_amount INTEGER DEFAULT 0,
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


# نظام التحقق والتسجيل التلقائي الخفي (بدون نوافذ إجبار مزعجة)
def ensure_user(user_id: int, username: str):
    cursor.execute(
        "SELECT user_id FROM user_data WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO user_data (user_id, username, name, age, gender, is_registered)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (user_id, username, "مغامر جديد", 20, "غير محدد"),
        )
        db_connection.commit()


# ==========================================
# 2. الملف الشخصي
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
    ensure_user(target.id, str(target))

    cursor.execute(
        "SELECT name, age, gender, balance, bank_balance, loan_amount, equipment_score, floors, max_unlocked_floor, hero_name, equipment_name, title, hide_stats, hide_titles FROM user_data WHERE user_id = ?",
        (target.id,),
    )
    data = cursor.fetchone()
    (
        name,
        age,
        gender,
        balance,
        bank_balance,
        loan,
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
                f"• الرصيد اليدوي: `{balance}` 💎\n"
                f"• الرصيد البنكي: `{bank_balance}` 🏦\n"
                f"• القروض النشطة: `{loan}` 📜\n"
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
# 3. أمر الحقيبة المنفصل
# ==========================================


@bot.tree.command(name="الحقيبة", description="عرض حقيبتك والمعدات والعتاد الحالي")
async def inventory_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    cursor.execute(
        "SELECT equipment_name, equipment_score, balance, floors, max_unlocked_floor FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    eq_name, eq_score, balance, floors, max_unlocked = cursor.fetchone()

    embed = discord.Embed(
        title=f"🎒 حقيبة المغامر: {interaction.user.display_name}",
        description=(
            f"• 🗡️ **العتاد الحالي:** `{eq_name}`\n"
            f"• ⚔️ **نقاط قوة العتاد:** `{eq_score}`\n"
            f"• 💎 **العملات:** `{balance}`\n"
            f"• 🏢 **الطابق الحالي:** `{floors}` (أقصى طابق متاح: `{max_unlocked}/1000`)"
        ),
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# 4. نظام الطوابق الشامل (أمر رئيسي يفتح منيو التفاعل)
# ==========================================


class FloorBattleView(discord.ui.View):

    def __init__(self, user_id: int, target_floor: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.target_floor = target_floor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه المعركة لا تخصك!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="⚔️ تنفيذ الهجوم على الزعيم",
        style=discord.ButtonStyle.danger,
        emoji="🔥",
    )
    async def attack_boss(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        cursor.execute(
            "SELECT equipment_score, balance, max_unlocked_floor FROM user_data WHERE user_id = ?",
            (user_id,),
        )
        eq_score, balance, max_unlocked = cursor.fetchone()

        boss_power = self.target_floor * 15 + random.randint(50, 200)
        player_total_power = eq_score + random.randint(10, 80)

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
            reward_coins = self.target_floor * 50 + random.randint(100, 500)
            reward_eq_score = self.target_floor * 2 + random.randint(5, 15)
            loot_names = [
                "سيف برونزي مهترئ",
                "درع جلدي متين",
                "خنجر الصياد السريع",
                "صولجان الحارس القديم",
                "عباءة الظل الخفية",
            ]
            won_loot = random.choice(loot_names) + f" (طابق {self.target_floor})"

            new_max = (
                max(max_unlocked, self.target_floor + 1)
                if self.target_floor == max_unlocked
                else max_unlocked
            )

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
                title=f"🎉 انتصار في الطابق {self.target_floor}!",
                description=(
                    f"**⚔️ الزعيم المنهزم:** `{boss_title}` (قوة الزعيم: {boss_power})\n"
                    f"**🛡️ قوتك:** {player_total_power}\n\n"
                    f"🎁 **الجوائز:**\n"
                    f"• عملات: `+{reward_coins}` 💎\n"
                    f"• نقاط عتاد: `+{reward_eq_score}` ⚔️\n"
                    f"• العتاد الجديد: **{won_loot}**"
                ),
                color=discord.Color.green(),
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            embed = discord.Embed(
                title=f"💀 هزيمة في الطابق {self.target_floor}!",
                description=(
                    f"**⚔️ الزعيم:** `{boss_title}` (قوة الزعيم: {boss_power})\n"
                    f"**🛡️ قوتك:** {player_total_power}\n\n"
                    f"❌ عتادك ضعيف جداً مقارنة بقوة الزعيم في هذا الطابق! قم بتطوير عتادك أولاً."
                ),
                color=discord.Color.dark_red(),
            )
            await interaction.response.edit_message(embed=embed, view=self)


class SelectFloorDropdown(discord.ui.Select):

    def __init__(self, max_unlocked: int):
        options = []
        start_f = max(1, max_unlocked - 20)
        end_f = max_unlocked
        for f in range(end_f, start_f - 1, -1):
            options.append(
                discord.SelectOption(
                    label=f"الطابق رقم {f}",
                    description=f"دخول معركة زعيم الطابق {f}",
                    emoji="🏢",
                    value=str(f),
                )
            )
        super().__init__(
            placeholder="اختر الطابق الذي تريد خوض معركته...",
            min_values=1,
            max_values=1,
            options=options[:25],
        )

    async def callback(self, interaction: discord.Interaction):
        floor_num = int(self.values[0])
        embed = discord.Embed(
            title=f"🏢 الاستعداد لمعركة الطابق [{floor_num}/1000]",
            description="اضغط على زر الهجوم بالأسفل لبدء المعركة ضد زعيم الطابق:",
            color=discord.Color.dark_gold(),
        )
        view = FloorBattleView(interaction.user.id, floor_num)
        await interaction.response.send_message(
            embed=embed, view=view, ephemeral=True
        )


class FloorMainMenuView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة لا تخصك!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="صعود الطوابق",
        style=discord.ButtonStyle.primary,
        emoji="🏢",
        row=0,
    )
    async def choose_floor_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT max_unlocked_floor FROM user_data WHERE user_id = ?",
            (self.user_id,),
        )
        max_unlocked = cursor.fetchone()[0]

        view = discord.ui.View()
        view.add_item(SelectFloorDropdown(max_unlocked))
        await interaction.response.send_message(
            "اختر الطابق الذي ترغب باختراقه من القائمة:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="المتجر العادي",
        style=discord.ButtonStyle.success,
        emoji="🛍️",
        row=0,
    )
    async def normal_shop_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🛍️ المتجر العادي الإمبراطوري",
            description="استخدم أمر `/المتجر` لعرض الأسلحة أو قم بشرائها مباشرة.",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(
            embed=embed, view=NormalShopView(), ephemeral=True
        )

    @discord.ui.button(
        label="متجر الظلام",
        style=discord.ButtonStyle.danger,
        emoji="🌑",
        row=0,
    )
    async def dark_shop_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌑 متجر الظلام السري",
            description="أسلحة محرمة تمنحك قوة خارقة.",
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(
            embed=embed, view=DarkShopView(), ephemeral=True
        )

    @discord.ui.button(
        label="تطوير العتاد",
        style=discord.ButtonStyle.secondary,
        emoji="⚒️",
        row=1,
    )
    async def upgrade_eq_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT balance, equipment_score FROM user_data WHERE user_id = ?",
            (self.user_id,),
        )
        bal, eq_sc = cursor.fetchone()
        cost = 150
        if bal < cost:
            await interaction.response.send_message(
                "❌ رصيدك غير كافي لتطوير العتاد! تكلفة التطوير `150 💎`.",
                ephemeral=True,
            )
            return

        cursor.execute(
            "UPDATE user_data SET balance = balance - ?, equipment_score = equipment_score + 25 WHERE user_id = ?",
            (cost, self.user_id),
        )
        db_connection.commit()
        await interaction.response.send_message(
            "⚒️ تم تطوير عتادك بنجاح مقابل `150 💎` وزادت نقاط قوتك بقيمة `+25`!",
            ephemeral=True,
        )

    @discord.ui.button(
        label="الحقيبة", style=discord.ButtonStyle.secondary, emoji="🎒", row=1
    )
    async def bag_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT equipment_name, equipment_score, balance, floors, max_unlocked_floor FROM user_data WHERE user_id = ?",
            (self.user_id,),
        )
        eq_name, eq_score, balance, floors, max_unlocked = cursor.fetchone()

        embed = discord.Embed(
            title="🎒 حقيبة المغامر",
            description=(
                f"• 🗡️ **العتاد الحالي:** `{eq_name}`\n"
                f"• ⚔️ **نقاط قوة العتاد:** `{eq_score}`\n"
                f"• 💎 **العملات:** `{balance}`\n"
                f"• 🏢 **الطابق الحالي:** `{floors}` (أقصى طابق: `{max_unlocked}/1000`)"
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="الطوابق", description="فتح منيو برج الطوابق الألف والخيارات الرئيسية"
)
async def floors_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    cursor.execute(
        "SELECT max_unlocked_floor, equipment_score, floors FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    max_unlocked, eq_score, current_floor = cursor.fetchone()

    embed = discord.Embed(
        title="🏢 برج الطوابق الأسطوري (1 إلى 1000)",
        description=(
            "مرحباً بك في بوابة الأبراج الكبرى.\n"
            f"• طابقك الحالي: `{current_floor}`\n"
            f"• أعلى طابق متاح: `{max_unlocked}/1000`\n"
            f"• قوتك الحالية: `{eq_score}` ⚔️\n\n"
            "اختر ما تحب من الأزرار بالأسفل للتنقل بين الصعود، المتاجر، تطوير العتاد، أو الحقيبة:"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"
    )

    view = FloorMainMenuView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 5. الأبطال الأسطوريين الجدد (3 ذكور + 3 إناث)
# ==========================================
HEROES_DATA = {
    "vanguard": {
        "title": "فانغارد - فارس الإمبراطورية الأبدي",
        "gender": "ذكر",
        "power": 920,
        "defense": 950,
        "story": "قائد الحرس الملكي الذي صمد وحيداً أمام جيش من التنانين لمدة ثلاثة أيام بلياليها، درعه مصنوع من حجر النيزك القديم.",
        "image": "https://images.unsplash.com/photo-1599839575945-a9e5af0c3fa5?w=800",
    },
    "kaelthas": {
        "title": "كائيلثاس - سيد اللهب المحرق",
        "gender": "ذكر",
        "power": 980,
        "defense": 700,
        "story": "أمير السحرة المنفي الذي سخر أرواح النيران البدائية في يديه، لتصبح تعويذاته قادرة على إذابة الجبال وتحويلها إلى رماد.",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800",
    },
    "fenrir": {
        "title": "فنرير - صياد العواصف الشبح",
        "gender": "ذكر",
        "power": 940,
        "defense": 810,
        "story": "محارب غامض يتحرك بسرعة البرق بين ظلال الغابات الملعونة، يحمل خنجراً مسحوراً يمتص طاقة الأعداء بنظرة واحدة.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?w=800",
    },
    "valkyrie": {
        "title": "فالكيري - فارسة السماء المضيئة",
        "gender": "أنثى",
        "power": 930,
        "defense": 900,
        "story": "محاربة مقدسة هبطت من السماء بجناحي نور، تقود أرواح الأبطال في المعارك العظمى وتزرع الرعب في قلوب الشياطين.",
        "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800",
    },
    "morgana": {
        "title": "مورغانا - ساحرة الظلال المطلقة",
        "gender": "أنثى",
        "power": 990,
        "defense": 680,
        "story": "ملكة الفنون المظلمة التي تلاعبت بالزمن والأبعاد، تستطيع فتح بوابات الجحيم وسحب أعدائها إلى العدم الأبدي.",
        "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800",
    },
    "Aria": {
        "title": "آريا - أميرة الرياح الفضية",
        "gender": "أنثى",
        "power": 910,
        "defense": 850,
        "story": "رامية السهام الأسطورية التي لا تخطئ هدفها أبداً، تطلق سهاماً مشبعة برياح عاصفة تقتلع الجيوش من جذورها.",
        "image": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800",
    },
}


class HeroSelectDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="فانغارد (فارس الإمبراطورية)",
                description="ذكر | دفاع فولاذي وصلابة مطلقة",
                emoji="🛡️",
                value="vanguard",
            ),
            discord.SelectOption(
                label="كائيلثاس (سيد اللهب)",
                description="ذكر | هجوم ناري مدمر",
                emoji="🔥",
                value="kaelthas",
            ),
            discord.SelectOption(
                label="فنرير (صياد العواصف)",
                description="ذكر | سرعة وخفة برقية",
                emoji="⚡",
                value="fenrir",
            ),
            discord.SelectOption(
                label="فالكيري (فارسة السماء)",
                description="أنثى | توازن عالي ونور مقدس",
                emoji="✨",
                value="valkyrie",
            ),
            discord.SelectOption(
                label="مورغانا (ساحرة الظلال)",
                description="أنثى | طاقة سحرية مظلمة فائقة",
                emoji="🌑",
                value="morgana",
            ),
            discord.SelectOption(
                label="آريا (أميرة الرياح)",
                description="أنثى | دقة قاتلة وسهام عاصفة",
                emoji="🏹",
                value="Aria",
            ),
        ]
        super().__init__(
            placeholder="اختر بطلاً أسطورياً لعرض قصته...",
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
            title=f"🛡️ البطل: {hero['title']}",
            description=(
                f"**📖 القصة:**\n{hero['story']}\n\n"
                f"📊 **المعدلات:**\n"
                f"• الهجوم: `{hero['power']}` ⚔️\n"
                f"• الدفاع: `{hero['defense']}` 🛡️\n\n"
                "✅ تم تعيينه بطلاً أساسياً!"
            ),
            color=discord.Color.purple(),
        )
        embed.set_image(url=hero["image"])
        await interaction.response.edit_message(embed=embed, view=self.view)


class HeroMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HeroSelectDropdown())


@bot.tree.command(name="الابطال", description="فتح قاعة الأبطال الفانتازيا")
async def heroes_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    embed = discord.Embed(
        title="🌟 قاعة الأبطال الأسطوريين",
        description="اختر بطلاً من القائمة لاستعراضه:",
        color=discord.Color.dark_gold(),
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
        "desc": "سيف مشتعل بنيران التنانين.",
    },
    "hammer": {
        "title": "مطرقة الرعد الكونية",
        "price": "320 💎",
        "desc": "مطرقة من نيازك ساطعة.",
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
            f"✅ تم شراء وتجهيز `{item['title']}` بنجاح!", ephemeral=True
        )


class NormalShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(NormalShopDropdown())


@bot.tree.command(name="المتجر", description="فتح المتجر العادي للأسلحة")
async def shop_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    embed = discord.Embed(
        title="🛍️ المتجر العادي الإمبراطوري",
        description="اختر سلاحاً لتعزيز قوتك:",
        color=discord.Color.gold(),
    )
    view = NormalShopView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


DARK_SHOP_ITEMS = {
    "dark_blade": {
        "title": "شفرة الموت المظلمة",
        "price": "666 💎",
        "desc": "شفرة مسحورة بطاقة الهلاك.",
    }
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
            placeholder="اختر سلاحاً من متجر الظلام...",
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
            f"💀 تم شراء وتجهيز `{item['title']}` بنجاح!", ephemeral=True
        )


class DarkShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(DarkShopDropdown())


@bot.tree.command(name="متجر_الظلام", description="فتح متجر الظلام السري")
async def dark_shop_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    embed = discord.Embed(
        title="🌑 متجر الظلام السري",
        description="أسلحة محرّمة قوية جداً:",
        color=discord.Color.dark_red(),
    )
    view = DarkShopView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 7. نظام البنك المطور، القروض، والتحذيرات الفخم
# ==========================================


class LoanModal(discord.ui.Modal, title="طلب قرض بنكي"):
    amount = discord.ui.TextInput(
        label="مبلغ القرض المطلوب",
        placeholder="اكتب المبلغ الذي تريد اقتراضه...",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            loan_val = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ يرجى إدخال أرقام صحيحة فقط!", ephemeral=True
            )
            return

        if loan_val <= 0:
            await interaction.response.send_message(
                "❌ المبلغ غير صالح!", ephemeral=True
            )
            return

        cursor.execute(
            "SELECT loan_amount FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current_loan = cursor.fetchone()[0]

        if current_loan > 0:
            await interaction.response.send_message(
                "❌ لديك قرض قديم لم تقم بسداده بعد! لا يمكنك أخذ قرض جديد.",
                ephemeral=True,
            )
            return

        if loan_val > 50000:
            await interaction.response.send_message(
                "❌ الحد الأقصى للقرض الواحد هو `50,000` عملة!", ephemeral=True
            )
            return

        cursor.execute(
            "UPDATE user_data SET bank_balance = bank_balance + ?, loan_amount = loan_amount + ? WHERE user_id = ?",
            (loan_val, loan_val, interaction.user.id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title="🏦 صندوق البنك المركزي - تمت الموافقة على القرض",
            description=(
                f"لقد حصلت على قرض بنكي بقيمة `💎 {loan_val}` بنجاح.\n\n"
                "⚠️ **تنبيه هام:** يجب عليك سداد القرض في أقرب وقت عبر زر **سداد القرض**، وفي حال تخلفك عن السداد، سيتم بيع عتادك وأغراضك تلقائياً لاستسوية الدين!"
            ),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BankView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه اللوحة لا تخصك، قم بفتح لوحتك الخاصة عبر `/البنك`!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="إيداع رصيد بالتوفير (+50)",
        style=discord.ButtonStyle.success,
        emoji="📥",
        row=0,
    )
    async def deposit(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "UPDATE user_data SET bank_balance = bank_balance + 50 WHERE user_id = ?",
            (self.user_id,),
        )
        db_connection.commit()
        cursor.execute(
            "SELECT bank_balance FROM user_data WHERE user_id = ?",
            (self.user_id,),
        )
        new_bank = cursor.fetchone()[0]
        await interaction.response.send_message(
            f"✅ تم إيداع 50 جوهرة في حسابك البنكي الآمن! الرصيد البنكي الحالي: `{new_bank}` 🏦",
            ephemeral=True,
        )

    @discord.ui.button(
        label="اقتراض مبلغ",
        style=discord.ButtonStyle.danger,
        emoji="📜",
        row=0,
    )
    async def take_loan(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(LoanModal())

    @discord.ui.button(
        label="سداد القرض",
        style=discord.ButtonStyle.primary,
        emoji="💸",
        row=1,
    )
    async def pay_loan(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        ensure_user(interaction.user.id, str(interaction.user))
        cursor.execute(
            "SELECT balance, bank_balance, loan_amount FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        balance, bank_balance, loan = cursor.fetchone()

        if loan <= 0:
            await interaction.response.send_message(
                "✨ ليس لديك أي قروض مسجلة لتسديدها!", ephemeral=True
            )
            return

        total_available = balance + bank_balance
        if total_available < loan:
            await interaction.response.send_message(
                f"❌ رصيدك الإجمالي (اليدوي + البنك = {total_available}) لا يكفي لسداد قيمة القرض البالغة `💎 {loan}`!",
                ephemeral=True,
            )
            return

        new_balance = balance
        new_bank = bank_balance
        remaining_loan = loan

        if new_bank >= remaining_loan:
            new_bank -= remaining_loan
        else:
            remaining_loan -= new_bank
            new_bank = 0
            new_balance -= remaining_loan

        cursor.execute(
            "UPDATE user_data SET balance = ?, bank_balance = ?, loan_amount = 0 WHERE user_id = ?",
            (new_balance, new_bank, interaction.user.id),
        )
        db_connection.commit()

        await interaction.response.send_message(
            "✅ تم سداد كامل القرض بنجاح وأصبح سجلك البنكي نظيفاً وآمناً!",
            ephemeral=True,
        )

    @discord.ui.button(
        label="فحص الإنذار والعقوبات",
        style=discord.ButtonStyle.secondary,
        emoji="🚨",
        row=1,
    )
    async def check_warning(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        ensure_user(interaction.user.id, str(interaction.user))
        cursor.execute(
            "SELECT loan_amount, equipment_score, equipment_name FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        loan, eq_score, eq_name = cursor.fetchone()

        if loan > 0:
            embed = discord.Embed(
                title="🚨 نظام الإنذار البنكي الخطر",
                description=(
                    f"لديك قرض نشط بقيمة: `💎 {loan}`\n"
                    f"العتاد الحالي المعرض للخطر: **{eq_name}** (قوة: `{eq_score}`)\n\n"
                    "⚠️ **تحذير نهائي:** إذا تخلفت عن السداد، ستقوم إدارة البنك ببيع أغراضك تلقائياً لاسترداد الأموال!"
                ),
                color=discord.Color.red(),
            )
        else:
            embed = discord.Embed(
                title="🛡️ الحالة المالية آمنة",
                description=(
                    "حسابك نظيف تماماً وليس عليك أي قروض أو إنذارات مالية حالية."
                ),
                color=discord.Color.green(),
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="البنك", description="فتح لوحة المصرف الإمبراطوري الفاخرة والقروض"
)
async def bank_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))
    cursor.execute(
        "SELECT balance, bank_balance, loan_amount, equipment_name, equipment_score FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    balance, bank_balance, loan, eq_name, eq_score = cursor.fetchone()

    embed = discord.Embed(
        title="🏛️ المصرف الإمبراطوري الملكي - لوحة المعاملات الفاخرة",
        description=(
            "مرحباً بك في المؤسسة المالية الرسمية للمغامرين.\n"
            "إليك ملخص حسابك المصرفي والخدمات المتاحة:"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_thumbnail(
        url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png"
    )

    embed.add_field(
        name="💰 الأرصدة المالية",
        value=(
            f"• الرصيد اليدوي (الكاش): `💎 {balance}`\n"
            f"• الرصيد البنكي الآمن: `💎 {bank_balance}`\n"
            f"• إجمالي الثروة: `💎 {balance + bank_balance}`"
        ),
        inline=False,
    )

    loan_status = (
        f"`💎 {loan}` (يوجد إنذار خطر!) 🚨" if loan > 0 else "لا يوجد (سجل نظيف) ✅"
    )
    embed.add_field(
        name="📜 حالة القروض والديون",
        value=(
            f"• قيمة القرض الحالي: {loan_status}\n"
            f"• العتاد المرهون للضمان: **{eq_name}**"
        ),
        inline=False,
    )

    embed.set_footer(
        text=(
            "استخدم الأزرار بالأسفل لإدارة الإيداع، القروض، السداد، أو فحص الإنذارات."
        ),
        icon_url=interaction.user.display_avatar.url,
    )

    view = BankView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 8. لوحة المطورين (مع شخصية السفاح السرية الخاصة بالمطور فقط)
# ==========================================

# بيانات شخصية السفاح المرعبة والسرية
BUTCHER_HERO = {
    "title": "السفاح - كابوس الأكوان المظلمة",
    "power": 9999,
    "defense": 9999,
    "story": "كيان شيطاني مرعب ولد من رحم الدماء والظدام الأبدي، لا ينام ولا يرحم. تلامس خطاه أراضي الموتى فيرتجف لروعبها ملوك الطوابق. يحمل منجل المنون المقطر بالسموم الفتاكة، وقوته تتجاوز حدود العقل والبشر.",
    "image": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800",
}


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(
        label="📊 إحصائيات الأوامر",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def stats_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]

        embed = discord.Embed(
            title="⚡ لوحة تحكم المطورين", color=discord.Color.dark_embed()
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين",
            value=f"`{total_users}` مسجل",
            inline=True,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="🗡️ تفعيل شخصية 'السفاح' (للمطور فقط)",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def unlock_butcher_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # التحقق الأمني الإضافي للتأكد أن المستخدم مطور حقاً
        if (
            not is_dev(interaction.user.id)
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.response.send_message(
                "❌ عذراً، هذه الشخصية المرعبة مخصصة للمطور حصرياً!",
                ephemeral=True,
            )
            return

        user_id = interaction.user.id
        cursor.execute(
            "UPDATE user_data SET hero_name = ?, equipment_score = 9999 WHERE user_id = ?",
            (BUTCHER_HERO["title"], user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title=f"⚠️ تم استدعاء الشخصية المرعبة: {BUTCHER_HERO['title']}",
            description=(
                f"**📖 القصة الملعونة:**\n{BUTCHER_HERO['story']}\n\n"
                f"💀 **المعدلات الخارقة:**\n"
                f"• الهجوم المطلق: `{BUTCHER_HERO['power']}` ⚔️\n"
                f"• الدفاع المطلق: `{BUTCHER_HERO['defense']}` 🛡️\n\n"
                "🩸 تم ربط سفاح الموت بملفك الشخصي بنجاح تام!"
            ),
            color=discord.Color.dark_red(),
        )
        embed.set_image(url=BUTCHER_HERO["image"])
        await interaction.response.send_message(
            embed=embed, ephemeral=True
        )


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
        description="اختر الخيار المناسب من لوحة التحكم السرية:",
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
# 9. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
