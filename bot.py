import discord
from discord import app_commands
from discord.ui import View, Select, Button
from datetime import datetime, timedelta

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
        
        # 1. الراتب اليومي
        if choice == "bank_daily":
            # هنا تستعلم من قاعدة بيانات MongoDB إذا كان المستخدم قد استلم راتبه اليوم أم لا
            has_claimed = False  # مثال افتراضي
            
            if has_claimed:
                return await interaction.response.send_message("⏳ لقد استلمت راتبك اليومي مسبقاً، عد غداً!", ephemeral=True)

            return await interaction.response.send_message(
                "🎉 **مبروك!** تم إيداع الراتب اليومي بقيمة `5,000` عملة في حسابك بنجاح.",
                ephemeral=True
            )
        
        # 2. نظام القروض والمعدات
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
                color=0x8B0000  # أحمر ملكي تحذيري
            )
            
            # زر تقديم الطلب داخل نافذة القروض
            class LoanView(View):
                def __init__(self):
                    super().__init__(timeout=180)

                @discord.ui.button(label="تقديم طلب قرض", style=discord.ButtonStyle.danger, emoji="⚖️", custom_id="request_loan_btn")
                async def request_loan(self, interaction: discord.Interaction, button: Button):
                    await interaction.response.send_message("📝 تم فتح نافذة تقديم طلب القرض بنجاح! (يمكنك ربطها بـ Modal لتحديد المبلغ والمدة).", ephemeral=True)

            return await interaction.response.send_message(embed=embed, view=LoanView(), ephemeral=True)
        
        # 3. تحويل العملات
        elif choice == "bank_transfer":
            return await interaction.response.send_message(
                "💸 ميزة التحويل قيد التفعيل. (يمكنك استخدام Modal لطلب ID الشخص والمبلغ المراد تحويله).",
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
            "• `💰` **الراتب اليومي:** استلم مكافأتك المالية بانتظام.\n"
            "• `📜` **نظام القروض:** اقتراض مالي مع نظام حماية الأصول وبيع المعدات تلقائياً عند انتهاء المهلة.\n"
            "• `💸` **تحويل العملات:** إرسال الأموال فورياً لأي شخص بأمان تام."
        ),
        color=0xD4AF37  # لون الذهب الفاخر
    )
    bank_embed.set_thumbnail(url="https://i.imgur.com/3Z66v7q.png")
    bank_embed.set_footer(
        text=f"طلب بواسطة: {interaction.user}", 
        icon_url=interaction.user.display_avatar.url
    )
    bank_embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=bank_embed, view=BankView(), ephemeral=False)
