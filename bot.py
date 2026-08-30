import os
import random
import re
import asyncio
import discord
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
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
# توليد 500 قطعة عتاد لكل فئة ديناميكياً
# ==========================================
CATEGORIES = ["خناجر", "سيوف", "مطرقات", "خوذ", "دروع", "ساق", "حذاء"]

def generate_shop_items(shop_type):
    items_dict = {}
    prefixes = [
        "ظلال", "صاعقة", "لهب", "دمار", "ملعون", "مبارك",
        "أبدي", "فاني", "جلمود", "برق", "سحيق", "أساطير",
        "ملوكي", "عاصف", "حارق"
    ]
    suffixes = [
        "الردى", "الخلود", "الفناء", "الجهنم", "الظلام", "النور",
        "الشفق", "الجبابرة", "الأسسياد", "التنين", "الموت",
        "السيوف", "الدم", "الفرسان", "العرش"
    ]

    for cat in CATEGORIES:
        cat_items = []

        for i in range(1, 501):
            p = random.choice(prefixes)
            s = random.choice(suffixes)
            name = f"{cat} {p} {s} #{i}"

            if shop_type == "dark":
                if i > 480:
                    tier = "الشيطان"
                elif i > 440:
                    tier = "الجحيم"
                elif i > 380:
                    tier = "السفاح"
                elif i > 250:
                    tier = "أسطوري"
                elif i > 150:
                    tier = "ملحمي"
                elif i > 50:
                    tier = "نادر"
                else:
                    tier = "شائع"

                power = i * 3 + random.randint(15, 60)
                price = i * 4 + random.randint(10, 50)
            else:
                if i > 450:
                    tier = "مقدس"
                elif i > 350:
                    tier = "فريد"
                elif i > 250:
                    tier = "أسطوري"
                elif i > 150:
                    tier = "ملحمي"
                elif i > 50:
                    tier = "نادر"
                else:
                    tier = "شائع"

                power = i * 2 + random.randint(5, 30)
                price = i * 15 + random.randint(50, 200)

            cat_items.append({
                "id": f"{shop_type[0]}_{cat}_{i}",
                "name": name,
                "tier": tier,
                "power": power,
                "price": price
            })

        items_dict[cat] = cat_items

    return items_dict

NORMAL_SHOP_ITEMS = generate_shop_items("normal")
DARK_SHOP_ITEMS = generate_shop_items("dark")

# ==========================================
# قوائم الأسئلة
# ==========================================
NORMAL_QUESTIONS = [
    "ما هي أكلتك المفضلة التي لا يمكنك الاستغناء عنها؟", "ما هو لونك المفضل ولماذا؟",
    "لو كان بإمكانك السفر لأي مكان في العالم الآن، أين ستذهب؟", "ما هي أكثر مادة دراسية أو مجال تحبه؟",
    "ما هو حيوانك الأليف المفضل؟", "ما هو أكثر فيلم شاهدته وأثر فيك؟",
    "هل تفضل فصل الصيف أم الشتاء؟", "متى آخر مرة ضحكت فيها من قلبك وعلى ماذا؟",
    "ما هو كارتون طفولتك المفضل الذي تذكره دائماً؟", "لو كان معك مليون دولار الآن، ماذا ستفعل بها أولاً؟",
    "هل تفضل تناول الشاي أم القهوة؟", "ما هي أكثر أغنية تستمع لها هذه الأيام؟",
    "هل تفضل الخروج مع الأصدقاء أم البقاء وحيداً في المنزل؟", "ما هو فريقك الرياضي أو ناديك المفضل؟",
    "شيء بسيط لا تستطيع العيش بدونه ليوم واحد؟", "ما هو الوقت المفضل لديك خلال اليوم (صباح أم مساء)؟",
    "هل تحب الطبخ وما هو أفضل طبق تحسنه؟", "ما هو التطبيق الأكثر استخداماً على هاتفك؟",
    "لو خيروك بين العيش في مدينة صاخبة أو قرية هادئة، ماذا تختار؟", "ما هي الهواية التي تقضي وقتاً طويلاً في ممارستها؟",
    "هل تستيقظ مبكراً بسهولة أم تعاني مع المنبه؟", "ما هو أول شيء تفعله عندما تستيقظ من النوم؟",
    "هل تفضل قراءة الكتب أَم مشاهدة الأفلام؟", "ما هو المكان المفضل لديك للجلوس بمفردك؟",
    "إذا أصبح بإمكانك الطيران ليوم واحد، إلى أين ستطير؟", "ما هو الطقس المفضل لديك؟",
    "هل تحب الحيوانات المفترسة أم الأليفة؟", "ما هو العصير أو المشروب البارد المفضل لديك؟",
    "هل تقضي وقتاً طويلاً على وسائل التواصل الاجتماعي؟", "ما هو هدفك القادم في الحياة؟",
    "هل تمتلك موهبة خفية مثل الرسم أو العزف؟", "ما هو أكثر موقف محظوظ مر بحياتك؟",
    "لو طُلب منك تغيير اسمك، ما الاسم الذي ستختاره؟", "ما هو طعم الآيس كريم المفضلة لديك؟",
    "هل تحب ألعاب الفيديو وما هي لعبتك المفضلة؟", "ما هو اليوم الأفضل بالنسبة لك خلال أسبوعك؟",
    "هل تفضل السفر بالسيارة أم بالطائرة؟", "ما هو أول جهاز تلفاز امتلكته في طفولتك؟",
    "هل تحب المفاجآت أم تفضل معرفة كل شيء مسبقاً؟", "ما هي الصفة التي تميزك بين أصدقائك؟"
]

MEDIUM_QUESTIONS = [
    "من هو أكثر شخص تثق به تماماً في هذا السيرفر؟", "متى آخر مرة بكيت فيها ولماذا؟",
    "هل سبق أن كذبت كذبة كبيرة على أهلك ونجلت منها؟", "ما هو أكبر خوف (فوبيا) يسيطر عليك؟",
    "لو كان بإمكانك تغيير شيء واحد في مظهرك، ماذا ستغير؟", "هل قمت من قبل بمقلب قوي بأحد أصدقاحك؟ احكِ لنا.",
    "متى آخر مرة شعرت فيها بإحراج شديد أمام الناس؟", "هل ندمت على معرفة شخص معين في حياتك؟",
    "ما هي أكثر صفة تكرهها في طبعك وتتمنى تغييرها؟", "ما هو السر الصغير الذي لا يعرفه الكثيرون عنك؟",
    "لو اضطررت لحذف جميع تطبيقات هاتفك ما عدا تطبيقاً واحداً، ماذا تختار؟", "هل تثق في الناس بسرعة أم تأخذ وقتاً طويلاً؟",
    "ما هو أغبى شيء فعلته عندما كنت طفلاً صغيراً؟", "هل سبق لك أن أخذت شيئاً ليس لك دون إذن (حتى لو بقصد المزاح)؟",
    "شخص في حياتك تتمنى لو لم تقابله أبداً؟", "ما هي أكبر مخاوفك من المستقبل؟",
    "هل تتاثر سريعاً بانتقادات الآخرين لك؟", "ما هو الموقف الذي جعلك تتغير بشكل جذرى؟",
    "هل سبق أن سامحت شخصاً أخطأ بحقك خطأً كبيراً؟", "ما هي الكلمة التي تجرحك أكثر إذا وجهها لك أحدهم؟",
    "هل تشعر بالرضا الكامل عن حياتك الحالية؟", "ما هو القرار الأهم الذي اتخذته وندمت عليه لاحقاً؟",
    "هل تكتم مشاعرك أم تعبر عنها فوراً لمن تحب؟", "ما هو الموقف الذي جعل تحترم شخصاً ما بشدة؟",
    "هل تميل إلى العزلة عندما تواجه مشكلة خاصة؟", "ما هو أكثر موقف شعرت فيه بالظلم الشديد؟",
    "هل تمتلك شجاعة الاعتراف بالخطأ فوراً؟", "ما هو الحلم الذي تطارد تحقيقه منذ سنوات؟",
    "هل تغيرت شخصيتك كثيراً عما كانت عليه قبل خمس سنوات؟", "ما هو أكثر موقف جعلك تفتخر بنفسك؟",
    "هل تعتقد أن الحظ يلعب دوراً أكبر أم الاجتهاد؟", "ما هو شعورك عندما يبتعد عنك صديق مقرب فجأة؟",
    "هل تستطيع مسامحة الخيانة بأنواعها؟", "ما هو الشيء الذي تعتبره خطا أحمر لا يمكن تجاوزه معك؟",
    "هل تندم بسرعة على قراراتك العاطفية؟", "ما هي العادة السيئة التي تعاني في التخلص منها؟",
    "هل تمانع في مصارحة شخص بعيوبه أم تفضل الصمت؟", "ما هو الموقف الذي أثبت لك معدن أصدقائك الحقيقي؟",
    "هل تعتقد أنك شخص يسهل إرضاؤه؟", "ما هو الشيء الذي تفتقده بشدة في أيامك الحالية؟"
]

BOLD_QUESTIONS = [
    "من هو الشخص الذي تعتبره 'مستفزاً' وتتجنب الحديث معه في هذا السيرفر؟", "ما هو أكثر شيء محرج بحثت عنه في سجل جوجل؟ (كن صادقاً)",
    "لو أخذنا هاتفك الآن وفتحت محادثاتك السرية، ما هي أكبر فضيحة سنجدها؟", "شخص موجود هنا تحب صوته أو شخصيته سراً؟",
    "هل سبق أن خنت ثقة شخص كان يعتبرك أخاً له؟", "ما هو أسوأ شيء قلته عن شخص وراء ظهره وعلم هو بذلك؟",
    "لو خيروك تطرد شخصاً واحداً نهائياً من السيرفر، من تختار ولماذا؟", "هل تملك حساباً وهمياً (فيك) تراقب به شخصاً معيناً سراً؟",
    "ما هي أكبر كذبة كذبتها للهروب من موعد أو موقف محرج؟", "هل سبق أن أعجبت بشخص مرتبط أو متزوج؟",
    "متى آخر مرة شعرت فيها بغيرة شديدة وعمياء تجاه صديق؟", "ما هي أكثر رسالة ندمت على إرسالها ولمن أرسلتها؟",
    "قيم جمالك وشكلك الخارجي من 10 بكل صراحة.", "شيء تفعله بالسر وتخجل تماماً أن يعرفه أهلك أو أصدقاؤك؟",
    "هل سبق أن تم رفضك علناً من شخص اعترفت له بمشاعرك؟", "من هو الشخص الذي لا يمكن أن تسامحه أبداً مهما حدث؟",
    "هل سبق أن نقلت سراً خطيراً أوتمنته لك صديقة أو صديق؟", "ما هو شعورك الحقيقي تجاه الشخص الجالس بجانبك الآن (أو آخر شخص تفاعلت معه)؟",
    "هل تتصرف بشخصية مزيفة أمام الناس لكي تعجبهم؟", "ما هو أكبر مبلغ مالى قمت بتبذيره على شيء تافه؟",
    "هل سبق أن تورطت في مشكلة كبيرة وكذبت لكي ينجو غيرك بدلاً منك؟", "من هو الشخص الذي تتمنى أن اعتذر له بشدة عما بدر منك؟",
    "هل تكره شخصاً لمجرد الغيرة منه؟", "ما هو أكثر موقف شعرت فيه أنك كنت شجاعاً رغم الخوف؟"
]

# ==========================================
# النوافذ التفاعلية ونظام البنك (Modal & Views)
# ==========================================

# نافذة تحويل العملات بالمنشن أو الـ ID
class TransferModal(Modal, title="تحويل العملات الفوري"):
    target_input = TextInput(
        label="منشن الشخص أو آيدي المستخدم (ID)",
        placeholder="مثال: @user أو 123456789012345678",
        style=discord.TextStyle.short,
        required=True
    )
    amount_input = TextInput(
        label="المبلغ المراد تحويله",
        placeholder="أدخل الرقم فقط (مثال: 500)",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        sender_id = str(interaction.user.id)
        raw_target = self.target_input.value.strip()
        raw_amount = self.amount_input.value.strip()

        # استخراج الآيدي من المنشن أو النص
        match_id = re.search(r'\d+', raw_target)
        if not match_id:
            return await interaction.response.send_message("❌ لم يتم التعرف على المستخدم المستهدف بشكل صحيح. يرجى استخدام المنشن أو الآيدي.", ephemeral=True)
        
        target_id = match_id.group()

        if target_id == sender_id:
            return await interaction.response.send_message("❌ لا يمكنك تحويل الأموال لنفسك!", ephemeral=True)

        try:
            amount = int(raw_amount)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return await interaction.response.send_message("❌ يرجى إدخال مبلغ صحيح وموجب.", ephemeral=True)

        # التحقق من رصيد المرسل في قاعدة البيانات
        sender_data = users_col.find_one({"user_id": sender_id})
        sender_balance = sender_data.get("balance", 0) if sender_data else 0

        if sender_balance < amount:
            return await interaction.response.send_message(f"❌ رصيدك غير كافٍ! رصيدك الحالي هو: `{sender_balance}` عملة.", ephemeral=True)

        # خصم المبلغ من المرسل وإضافته للمستقبل
        users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount}}, upsert=True)
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount}}, upsert=True)

        await interaction.response.send_message(
            f"✅ **تمت عملية التحويل بنجاح!**\n"
            f"💸 تم إرسال مبلغ ` {amount} ` عملة إلى <@{target_id}>.",
            ephemeral=True
        )

# قائمة الخدمات المصرفية
class BankSelect(Select):
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
                description="إرسال الأموال فورياً لأي عضو في السيرفر عبر المنشن.",
                value="bank_transfer",
                emoji="💸"
            )
        ]
        super().__init__(placeholder="✨ اختر الخدمة المصرفية المطلوبة من هنا...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        user_id = str(interaction.user.id)
        
        if choice == "bank_daily":
            # التحقق من الراتب اليومي عبر قاعدة البيانات
            user_data = users_col.find_one({"user_id": user_id})
            now = datetime.now(timezone.utc)
            
            last_claim = user_data.get("last_daily") if user_data else None
            
            if last_claim and now - last_claim < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_claim)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes = remainder // 60
                return await interaction.response.send_message(
                    f"⏳ لقد استلمت راتبك اليومي مسبقاً! يمكنك الاستلام مرة أخرى بعد `{hours} ساعة و {minutes} دقيقة`.",
                    ephemeral=True
                )

            # منح الراتب (مثلاً 5000 عملة) وتحديث الوقت
            daily_amount = 5000
            users_col.update_one(
                {"user_id": user_id},
                {"$set": {"last_daily": now}, "$inc": {"balance": daily_amount}},
                upsert=True
            )

            return await interaction.response.send_message(
                f"🎉 **مبروك!** تم إيداع الراتب اليومي بقيمة `{daily_amount}` عملة في حسابك بنجاح.",
                ephemeral=True
            )
        
        elif choice == "bank_loans":
            embed = discord.Embed(
                title="📜 | قسم القروض وضمان المعدات",
                description=(
                    "نظام القروض لدينا صارم لضمان حقوق الجميع:\n\n"
                    "⚠️ **شروط القرض:**\n"
                    "1. يتم تحديد مدة زمنية محددة لسداد القرض (مثال: 24 ساعة أو 3 أيام).\n"
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
                    # تسجيل القرض أو منح رصيد القرض مؤقتاً مع وقت انتهاء
                    loan_due = datetime.now(timezone.utc) + timedelta(days=3)
                    users_col.update_one(
                        {"user_id": str(interaction.user.id)},
                        {"$set": {"loan_due": loan_due}, "$inc": {"balance": 20000}},
                        upsert=True
                    )
                    await interaction.response.send_message(
                        "📝 **تم قبول طلب القرض بنجاح!**\n"
                        "تم إيداع `20,000` عملة في حسابك. لديك مهلة **3 أيام** للسداد، وإلا سيتم بيع معداتك تلقائياً.",
                        ephemeral=True
                    )

            return await interaction.response.send_message(embed=embed, view=LoanView(), ephemeral=True)
        
        elif choice == "bank_transfer":
            # فتح نافذة إدخال التحويل (Modal)
            return await interaction.response.send_modal(TransferModal())

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
            "• `💸` **تحويل العملات:** إرسال الأموال فورياً لأي شخص عبر المنشن بأمان تام."
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
