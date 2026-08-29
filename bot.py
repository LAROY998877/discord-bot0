import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجداول
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

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
            f"✅ **تم تسجيلك بنجاح يابطل!**\n👤 الاسم: `{name}`\n🎂 العمر: `{age}`\n🚻 الجنس: `{gender}`\n\nالآن يمكنك استخدام جميع الأوامر بحرية تامّة!",
            ephemeral=True,
        )


@bot.tree.command(name="تسجيل", description="التسجيل في النظام لفتح جميع الأوامر")
async def register_command(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


# ==========================================
# 3. الملف الشخصي (ظاهر للكل مع تحكم خاص بصاحب الملف فقط)
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


@bot.tree.command(name="الملف", description="عرض الملف الشخصي (ظاهر للجميع مع أزرار تحكم خاصة بصاحبه)")
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
        "SELECT name, age, gender, balance, equipment_score, floors, hero_name, equipment_name, title, hide_stats, hide_titles FROM user_data WHERE user_id = ?",
        (target.id,),
    )
    data = cursor.fetchone()
    name, age, gender, balance, eq_score, floors, hero, equipment, title, hide_stats, hide_titles = (
        data
    )

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
                f"• الطوابق المكتسحة: `{floors}` 🏢\n"
                f"• البطل المختار: `{hero}` 🦸‍♂️\n"
                f"• العتاد الحالي: `{equipment}` 🗡️"
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"طلب بواسطة: {interaction.user.display_name} | الملف مرئي للجميع"
        )
    )

    view = ProfileControlView(target.id)
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================
# 4. شخصية "السفاح" (خاص بالمطورين)
# ==========================================


@bot.tree.command(name="السفاح", description="[خاص بالمطورين] استدعاء شخصية السفاح الفانتازية المرعبة")
async def assassin_command(interaction: discord.Interaction):
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
            "❌ **خطأ أمني:** هذا الكيان الفانتازي مرعب وخاص بالمطورين فقط!",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="🩸 السفاح - حاصد الأرواح الأسطوري",
        description=(
            "**📖 القصة الفانتازية المرعبة:**\n"
            "في أعمق قيعان العوالم المظلمة، وُلد سلالة 'السفاحين'؛ كيانات مرعبة ترتدي دروعاً من العظام الملعونة.\n"
            "سيفه يقطر شؤماً ودماءً، ولا يقف في وجهه أي كائن حي إلا وتمزق إرتباطه بالواقع للأبد.\n\n"
            "📊 **معدلات القوة الفانتازية:**\n"
            "• قوة الفتاك: `999,999` ⚔️\n"
            "• هالة الرعب: `أبدية` 💀\n"
            "• نسبة النجاة: `0%`"
        ),
        color=discord.Color.dark_red(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800"
    )
    embed.set_footer(
        text=f"استدعاء حصري بواسطة المطور: {interaction.user.display_name}"
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


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
        embed.set_footer(
            text=f"تم الاختيار بواسطة: {interaction.user.display_name}"
        )

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
        description=(
            "مرحباً بك في عالم الأساطير.\n"
            "اختر بطلاً من القائمة المنسدلة بالأسفل لاستعراض **قصته، صورته الفانتازية الخيالية، ومعدلات قوته**!"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"
    )

    view = HeroMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 6. المتاجر (المتجر العادي + متجر الظلام - معدات كثيرة جداً)
# ==========================================

# 1. المتجر العادي (تعدّد كبير ومقسّم بعناية)
NORMAL_SHOP_ITEMS = {
    "sword": {
        "title": "سيف اللهب الأبدي (Flame Blade)",
        "price": "250 💎",
        "damage": "+500 هجوم ناري",
        "desc": "سيف أسطوري مشتغل بنيران التنانين القديمة، يحرق دروع الأعداء بضربة واحدة.",
        "image": "https://images.unsplash.com/photo-1589241062272-c0a000071dfa?w=800",
    },
    "hammer": {
        "title": "مطرقة الرعد الكونية (Thunder Hammer)",
        "price": "320 💎",
        "damage": "+600 قوة تحطيم",
        "desc": "مطرقة ثقيلة مصممة من نيازك ساطعة، تحدث هلعاً في ساحات القتال.",
        "image": "https://images.unsplash.com/photo-1601933470077-0afdd71f5424?w=800",
    },
    "bow": {
        "title": "قوس الضوء المقدس (Holy Bow)",
        "price": "280 💎",
        "damage": "+450 دقة وبصيرة",
        "desc": "يطلق سهاماً من الطاقة الصافية التي تخترق أعتى الحصون وتلاحق الهدف.",
        "image": "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=800",
    },
    "shield": {
        "title": "درع التنين الأسطوري (Dragon Shield)",
        "price": "350 💎",
        "damage": "+800 دفاع مطلق",
        "desc": "درع من حراشف أقدم تنين في الممالك السحرية، يعكس سحر وسهام الأعداء.",
        "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800",
    },
    "spear": {
        "title": "رمح البرق السريع (Lightning Spear)",
        "price": "300 💎",
        "damage": "+550 طعنة خاطفة",
        "desc": "رمح يلمع ببرق الصواعق، يمزق صفوف الأعداء بسرعة الصوت.",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800",
    },
    "axe": {
        "title": "فأس الجليد العظيم (Frost Axe)",
        "price": "290 💎",
        "damage": "+520 تجميد وتكسير",
        "desc": "فأس محفور من جبال الجليد الأبدي، يجمد الأعداء في مكانهم.",
        "image": "https://images.unsplash.com/photo-1599839575945-a9e5af0c3fa5?w=800",
    },
    "dagger": {
        "title": "خنجر الظل الخفي (Shadow Dagger)",
        "price": "220 💎",
        "damage": "+400 سرعة اغتيال",
        "desc": "خنجر قصير لا يرى بالعين المجردة، يوجه ضربات حرجة قاتلة.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?w=800",
    },
}


class NormalShopDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="سيف اللهب الأبدي",
                description="السعر: 250 💎 | هجوم ناري قوي",
                emoji="⚔️",
                value="sword",
            ),
            discord.SelectOption(
                label="مطرقة الرعد الكونية",
                description="السعر: 320 💎 | قوة تحطيم مهولة",
                emoji="🔨",
                value="hammer",
            ),
            discord.SelectOption(
                label="قوس الضوء المقدس",
                description="السعر: 280 💎 | دقة وبصيرة عالية",
                emoji="🏹",
                value="bow",
            ),
            discord.SelectOption(
                label="درع التنين الأسطوري",
                description="السعر: 350 💎 | دفاع مطلق ضد السحر",
                emoji="🛡️",
                value="shield",
            ),
            discord.SelectOption(
                label="رمح البرق السريع",
                description="السعر: 300 💎 | طعنة خاطفة بالبرق",
                emoji="⚡",
                value="spear",
            ),
            discord.SelectOption(
                label="فأس الجليد العظيم",
                description="السعر: 290 💎 | تجميد شامل للأعداء",
                emoji="🪓",
                value="axe",
            ),
            discord.SelectOption(
                label="خنجر الظل الخفي",
                description="السعر: 220 💎 | اغتيال سريع وخفي",
                emoji="🗡️",
                value="dagger",
            ),
        ]
        super().__init__(
            placeholder="اختر معدة أو سلاحاً من المتجر العادي...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        item = NORMAL_SHOP_ITEMS[choice]
        user_id = interaction.user.id

        cursor.execute(
            "UPDATE user_data SET equipment_name = ? WHERE user_id = ?",
            (item["title"], user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title=f"🛒 المتجر العادي: {item['title']}",
            description=(
                f"**📖 وصف السلاح:**\n{item['desc']}\n\n"
                f"📊 **التفاصيل:**\n• السعر: `{item['price']}`\n• التأثير: `{item['damage']}`\n\n"
                f"✅ *تم اقتناء وتجهيز هذه المعدة بنجاح!*"
            ),
            color=discord.Color.gold(),
        )
        embed.set_image(url=item["image"])
        await interaction.response.edit_message(embed=embed, view=self.view)


class NormalShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(NormalShopDropdown())


@bot.tree.command(name="المتجر", description="فتح المتجر العادي للأسلحة والمعدات بصور فانتزي")
async def shop_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="🛍️ المتجر العادي الإمبراطوري",
        description="تصفح الترسانة الواسعة من الأسلحة والمعدات القياسية المتاحة للشراء:",
        color=discord.Color.gold(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1589241062272-c0a000071dfa?w=800"
    )
    view = NormalShopView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# 2. متجر الظلام (Dark Shop - مجموعة ضخمة جداً من المعدات المحرمة)
DARK_SHOP_ITEMS = {
    "dark_blade": {
        "title": "شفرة الموت المظلمة (Dark Death Blade)",
        "price": "666 💎",
        "damage": "+1200 هجوم شيطاني",
        "desc": "شفرة مسحورة تنبعث منها طاقة الهلاك، تلتهم أرواح الأعداء وتضاعف الضرر بالظلام.",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800",
    },
    "shadow_hammer": {
        "title": "مطرقة الفوضى الملعونة (Chaos Hammer)",
        "price": "800 💎",
        "damage": "+1500 تحطيم مظلم",
        "desc": "مطرقة نحس صُنعت في سراديب العوالم السفلى، هجماتها تسبب شلل تام للخصم.",
        "image": "https://images.unsplash.com/photo-1601933470077-0afdd71f5424?w=800",
    },
    "abyss_scythe": {
        "title": "منجل الهاوية الأبدي (Abyss Scythe)",
        "price": "950 💎",
        "damage": "+1800 حصد الأرواح",
        "desc": "منجل عملاق يقطر طاقة سوداء، يحصد أرواح جماعات الأعداء بضربة واحدة.",
        "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800",
    },
    "blood_bow": {
        "title": "قوس الدم القرمزي (Blood Bow)",
        "price": "700 💎",
        "damage": "+1100 سهام دموية",
        "desc": "قوس مشبع بدماء الشياطين القديمة، يطلق سهاماً تلتصق بقلب العدو.",
        "image": "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=800",
    },
    "necromancer_staff": {
        "title": "عصا مستحضر الأرواح (Necro Staff)",
        "price": "850 💎",
        "damage": "+1400 سحر أسود مرعب",
        "desc": "عصا تعود لعصور الظلام الأولى، تستدعي أطيافاً وجيشاً من الموتى لقتالك.",
        "image": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800",
    },
    "void_shield": {
        "title": "درع الفراغ المطلق (Void Shield)",
        "price": "900 💎",
        "damage": "+2000 امتصاص الضرر",
        "desc": "درع مظلم يفتح ثقباً أسود يمتص هجمات الأعداء ويثنيهم عن التقدم.",
        "image": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800",
    },
    "infernal_daggers": {
        "title": "خناجر الجحيم المزدوجة (Infernal Daggers)",
        "price": "750 💎",
        "damage": "+1300 سرعة وحرق شيطاني",
        "desc": "خنجران تشتعلان بنيران لا تنطفئ، تسرع من حركات القاتل وتخترق أعتى الدروع.",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?w=800",
    },
}


class DarkShopDropdown(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="شفرة الموت المظلمة",
                description="السعر: 666 💎 | شفرة شيطانية فتاكة",
                emoji="🗡️",
                value="dark_blade",
            ),
            discord.SelectOption(
                label="مطرقة الفوضى الملعونة",
                description="السعر: 800 💎 | مطرقة دمار شامل",
                emoji="🔨",
                value="shadow_hammer",
            ),
            discord.SelectOption(
                label="منجل الهاوية الأبدي",
                description="السعر: 950 💎 | منجل حصد الأرواح الجماعي",
                emoji="🪓",
                value="abyss_scythe",
            ),
            discord.SelectOption(
                label="قوس الدم القرمزي",
                description="السعر: 700 💎 | سهام دموية خارقة",
                emoji="🏹",
                value="blood_bow",
            ),
            discord.SelectOption(
                label="عصا مستحضر الأرواح",
                description="السعر: 850 💎 | سحر أسود واستدعاء",
                emoji="🪄",
                value="necromancer_staff",
            ),
            discord.SelectOption(
                label="درع الفراغ المطلق",
                description="السعر: 900 💎 | امتصاص كامل للهجمات",
                emoji="🛡️",
                value="void_shield",
            ),
            discord.SelectOption(
                label="خناجر الجحيم المزدوجة",
                description="السعر: 750 💎 | سرعة وحرق شيطاني",
                emoji="⚔️",
                value="infernal_daggers",
            ),
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
            "UPDATE user_data SET equipment_name = ? WHERE user_id = ?",
            (item["title"], user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title=f"🖤 متجر الظلام: {item['title']}",
            description=(
                f"**📖 وصف السلاح المحرم:**\n{item['desc']}\n\n"
                f"📊 **التفاصيل:**\n• السعر: `{item['price']}`\n• التأثير: `{item['damage']}`\n\n"
                f"💀 *لقد عقدت صفقة مظلمة وتم تجهيز السلاح بنجاح!*"
            ),
            color=discord.Color.dark_red(),
        )
        embed.set_image(url=item["image"])
        await interaction.response.edit_message(embed=embed, view=self.view)


class DarkShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(DarkShopDropdown())


@bot.tree.command(name="متجر_الظلام", description="فتح متجر الظلام للأسلحة والعتاد المحرم والمظلم")
async def dark_shop_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_modal(RegisterModal())
        return

    embed = discord.Embed(
        title="🌑 متجر الظلام السري",
        description="تحذير: الأسلحة هنا تنبض بطاقة مظلمة وممحوة قوية جداً. اختر بحذر:",
        color=discord.Color.dark_red(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800"
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
        await interaction.response.send_modal(RegisterModal())
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
# 8. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
