import os
import random
import re
import asyncio
import discord
from discord import app_commands
from discord.ui import View, Select, Button
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# ==========================================
# إعداد البوت
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "❌ متغير MONGO_URI غير موجود في Railway Environment Variables."
    )

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

# ==========================================
# واجهة قائمة الخدمات المصرفية (Select Menu)
# ==========================================
class BankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="الراتب اليومي",
                description="استلام مكافأتك المالية اليومية بانتظام.",
                value="bank_daily",
                emoji="💰"
            ),
            discord.SelectOption(
                label="نظام القروض والمعدات",
                description="طلب قرض ورهن/بيع المعدات تلقائياً عند انتهاء مهلة السداد.",
                value="bank_loans",
                emoji="📜"
            ),
            discord.SelectOption(
                label="تحويل العملات",
                description="إرسال الأموال فورياً لأي عضو في السيرفر بأمان.",
                value="bank_transfer",
                emoji="💸"
            )
        ]
        super().__init__(placeholder="✨ اختر الخدمة المصرفية المطلوبة من هنا...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        
        if choice == "bank_daily":
            has_claimed = False  # مثال افتراضي
            if has_claimed:
                return await interaction.response.send_message("⏳ لقد استلمت راتبك اليومي مسبقاً، عد غداً!", ephemeral=True)

            return await interaction.response.send_message(
                "🎉 **مبروك!** تم إيداع الراتب اليومي بقيمة `5,000` عملة في حسابك بنجاح.",
                ephemeral=True
            )
        
        elif choice == "bank_loans":
            embed = discord.Embed(
                title="📜 | قسم القروض وضمان المعدات",
                description=(
                    "نظام القروض لدينا صارم لضمان حقوق الجميع:\n\n"
                    "⚠️ **شروط القرض:**\n"
                    "1. يتم تحديد مدة زمنية محددة لسداد القرض (مثلاً: 24 ساعة أو 3 أيام).\n"
                    "2. في حال انتهاء المهلة ولم تقم بالسداد، **سيقوم النظام تلقائياً ببيع معداتك وأصولك** المعروضة للرهن لاسترداد الأموال!\n\n"
                    "اضغط على الزر بالأسفل لتقديم طلب قرض جديد."
                ),
                color=0x8B0000
            )
            
            class LoanView(View):
                def __init__(self):
                    super().__init__(timeout=180)

                @discord.ui.button(label="تقديم طلب قرض", style=discord.ButtonStyle.danger, emoji="⚖️", custom_id="request_loan_btn")
                async def request_loan(self, interaction: discord.Interaction, button: Button):
                    await interaction.response.send_message("📝 تم فتح نافذة تقديم طلب القرض بنجاح!", ephemeral=True)

            return await interaction.response.send_message(embed=embed, view=LoanView(), ephemeral=True)
        
        elif choice == "bank_transfer":
            return await interaction.response.send_message(
                "💸 ميزة التحويل قيد التفعيل.",
                ephemeral=True
            )

class BankView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BankSelect())

# ==========================================
# أمر البنك الرئيسي (Slash Command)
# ==========================================
@bot.tree.command(name="bank", description="النظام المصرفي الفاخر لإدارة الأموال، القروض، والتحويلات")
async def bank(interaction: discord.Interaction):
    bank_embed = discord.Embed(
        title="🏛️ | البنك المركزي الملكي - Royal Bank",
        description=(
            "مرحباً بك في النظام المصرفي الأكثر تطوراً وفخامة.\n"
            "نحن نضع ثروتك وأصولك بين يديك بأعلى معايير الأمان والسرعة.\n\n"
            "✨ **الخدمات المتاحة حالياً:**\n"
            "• `💰` **الراتب اليومي:** استلام مكافأتك المالية بانتظام.\n"
            "• `📜` **نظام القروض:** اقتراض مالي مع نظام حماية الأصول وبيع المعدات تلقائياً عند انتهاء المهلة.\n"
            "• `💸` **تحويل العملات:** إرسال الأموال فورياً لأي شخص بأمان تام."
        ),
        color=0xD4AF37
    )
    bank_embed.set_thumbnail(url="https://i.imgur.com/3Z66v7q.png")
    bank_embed.set_footer(
        text=f"طلب بواسطة: {interaction.user}", 
        icon_url=interaction.user.display_avatar.url
    )
    bank_embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=bank_embed, view=BankView(), ephemeral=False)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

# تشغيل البوت
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ متغير DISCORD_TOKEN غير موجود في البيئة.")
