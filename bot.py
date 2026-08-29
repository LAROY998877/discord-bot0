import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قاعدة بيانات مؤقتة لتخزين بيانات اللاعبين المسجلين
REGISTERED_USERS = {}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")


# ==================== نظام التسجيل بالقائمة (Menu) ====================
class RegistrationModal(discord.ui.Modal, title="📝 استمارة التسجيل في اللعبة"):
    def __init__(self, gender: str):
        super().__init__()
        self.gender = gender

    name_input = discord.ui.TextInput(
        label="اسم الشخصية",
        placeholder="اكتب اسم شخصيتك هنا...",
        max_length=30
    )
    
    age_input = discord.ui.TextInput(
        label="العمر",
        placeholder="اكتب عمرك بالأرقام (مثال: 20)...",
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age = int(self.age_input.value)
        except ValueError:
            await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً! يرجى إعادة المحاولة.", ephemeral=True)
            return

        # حفظ البيانات في القاموس
        REGISTERED_USERS[interaction.user.id] = {
            "name": self.name_input.value,
            "age": age,
            "gender": self.gender
        }

        embed = discord.Embed(
            title="✅ تمت عملية التسجيل بنجاح!",
            description=f"أهلاً بك يا **{self.name_input.value}**! تم حفظ بياناتك الشخصية.",
            color=0x2ECC71
        )
        embed.add_field(name="🏷️ الاسم", value=self.name_input.value, inline=True)
        embed.add_field(name="🎂 العمر", value=str(age), inline=True)
        embed.add_field(name="⚧️ الجنس", value=self.gender, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class GenderSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="اختر جنس الشخصية...",
        options=[
            discord.SelectOption(label="ذكر", description="شخصية ذكر", emoji="👦"),
            discord.SelectOption(label="أنثى", description="شخصية أنثى", emoji="👧"),
            discord.SelectOption(label="آخر / تفضيل عدم الإفصاح", description="غير محدد", emoji="⭐")
        ]
    )
    async def select_gender(self, interaction: discord.Interaction, select: discord.ui.Select):
        chosen_gender = select.values[0]
        # فتح نافذة إدخال الاسم والعمر بعد اختيار الجنس
        modal = RegistrationModal(gender=chosen_gender)
        await interaction.response.send_modal(modal)


@bot.tree.command(name="تسجيل", description="افتح قائمة التسجيل لإنشاء حسابك الشخصي في اللعبة")
async def register(interaction: discord.Interaction):
    if interaction.user.id in REGISTERED_USERS:
        await interaction.response.send_message("⚠️ أنت مسجل بالفعل مسبقاً ولا تحتاج للتسجيل مرة أخرى!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 نظام التسجيل الإجباري",
        description="للبدء واستخدام أوامر اللعبة، يرجى اختيار جنس الشخصية من القائمة أدناه:",
        color=0x3498DB
    )
    await interaction.response.send_message(embed=embed, view=GenderSelectView(), ephemeral=True)


# ==================== أمر تجريبي (يتطلب التسجيل مسبقاً) ====================
@bot.tree.command(name="الملف", description="عرض ملفك الشخصي المسجل")
async def profile(interaction: discord.Interaction):
    # التحقق مما إذا كان المستخدم مسجلاً أم لا
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك تسجيل حسابك أولاً باستخدام الأمر: `/تسجيل` لكي تتمكن من استخدام الأوامر!", ephemeral=True)
        return

    user_data = REGISTERED_USERS[interaction.user.id]
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {interaction.user.display_name}", color=0xE67E22)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🏷️ اسم الشخصية:", value=f"`{user_data['name']}`", inline=False)
    embed.add_field(name="🎂 العمر:", value=f"`{user_data['age']}` سنة", inline=True)
    embed.add_field(name="⚧️ الجنس:", value=f"`{user_data['gender']}`", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)


bot.run(os.getenv('TOKEN'))
