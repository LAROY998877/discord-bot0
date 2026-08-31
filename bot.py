import os
import discord
from discord import app_commands
from discord.ext import commands
import pymongo
from datetime import datetime

# ================== إعدادات الاتصال وقاعدة البيانات ==================
MONGO_URI = os.getenv("MONGO_URI", "رابط_الاتصال_الخاص_بـ_MongoDB")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col = db["users"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== دالة التحقق من التسجيل ==================
def is_user_registered(user_id: str) -> bool:
    return users_col.find_one({"user_id": str(user_id)}) is not None


# ================== نافذة منيو التسجيل (Modal) ==================
class RegisterModal(discord.ui.Modal, title="📜 استمارة التسجيل في الإمبراطورية"):
    name_input = discord.ui.TextInput(
        label="الاسم الخاص بك",
        placeholder="أدخل اسم شخصيتك داخل اللعبة...",
        min_length=2,
        max_length=30,
        required=True
    )

    age_input = discord.ui.TextInput(
        label="العمر (أرقام فقط كحد أقصى 3000)",
        placeholder="مثال: 25",
        min_length=1,
        max_length=4,
        required=True
    )

    gender_input = discord.ui.TextInput(
        label="الجنس (اكتب: ذكر أو أنثى)",
        placeholder="ذكر / أنثى",
        min_length=3,
        max_length=4,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # 1. التحقق من رقمية العمر والحد الأقصى
        try:
            age = int(self.age_input.value.strip())
        except ValueError:
            embed_err = discord.Embed(
                title="❌ خطأ في الإدخال",
                description="يرجى كتابة العمر **كأرقام فقط** (مثال: 20)!",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed_err, ephemeral=True)

        if age < 1 or age > 3000:
            embed_err = discord.Embed(
                title="❌ خطأ في العمر",
                description="يجب أن يكون العمر بين **1** و **3000** سنة!",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed_err, ephemeral=True)

        # 2. التحقق من إدخال الجنس
        gender = self.gender_input.value.strip()
        if gender not in ["ذكر", "أنثى"]:
            embed_err = discord.Embed(
                title="❌ خطأ في تحديد الجنس",
                description="يرجى كتابة كلمة **ذكر** أو **أنثى** فقط في خانة الجنس!",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed_err, ephemeral=True)

        # 3. حفظ البيانات في قاعدة البيانات
        new_user = {
            "user_id": user_id,
            "name": self.name_input.value.strip(),
            "age": age,
            "gender": gender,
            "created_at": datetime.utcnow(),
            "balance": 1000,
            "bank": 0,
            "diamonds": 10,
            "power": 100,
            "custom_title": "المبتدئ الأسطوري",
            "selected_hero": "لم يتم الاختيار",
            "inventory": []
        }
        users_col.insert_one(new_user)

        # 4. بطاقة الانضمام الأنيقة
        embed_success = discord.Embed(
            title="👑 أهلاً بك في عرش الإمبراطورية!",
            description="تمت معالجة وثيقة هويتك بنجاح وأصبحت عضواً رسمياً.",
            color=discord.Color.gold()
        )
        embed_success.add_field(name="🪪 الاسم", value=f"`{self.name_input.value.strip()}`", inline=True)
        embed_success.add_field(name="⏳ العمر", value=f"`{age}` سنة", inline=True)
        embed_success.add_field(name="👤 الجنس", value=f"`{gender}`", inline=True)
        embed_success.add_field(
            name="🎁 المكافأة المكتسبة",
            value="• `1,000` 🪙 عملة ذهبية\n• `10` 💎 جواهر ألماس\n• اللقب: **المبتدئ الأسطوري**",
            inline=False
        )
        embed_success.set_thumbnail(url=interaction.user.display_avatar.url)
        embed_success.set_footer(
            text="الإمبراطورية العظمى • تم الحفظ بنجاح",
            icon_url=interaction.guild.icon.url if interaction.guild else None
        )

        await interaction.response.send_message(embed=embed_success, ephemeral=False)


# ================== أحداث البوت والأوامر ==================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✨ تم مزامنة {len(synced)} أمر بنجاح!")
    except Exception as e:
        print(f"❌ خطأ أثناء المزامنة: {e}")
    print(f"👑 البوت يعمل الآن باسم: {bot.user}")


@bot.tree.command(name="تسجيل", description="📜 فتح منيو التسجيل وإنشاء هويتك الإمبراطورية")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if is_user_registered(user_id):
        embed_error = discord.Embed(
            title="⚠️ تنبيه",
            description="**أنت مسجل بالفعل في قاعدة البيانات!** لا يمكنك التسجيل مرتين.",
            color=discord.Color.orange()
        )
        return await interaction.response.send_message(embed=embed_error, ephemeral=True)

    # عرض استمارة المنيو المنبثقة مباشرة
    await interaction.response.send_modal(RegisterModal())


# --- تشغيل البوت ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
