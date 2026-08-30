import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://botuser:bot12345@laroy998877.makaovo.mongodb.net/discord_bot_db?retryWrites=true&w=majority&authSource=admin")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

# ==========================================
# قوائم الأسئلة الموسعة (مستوى عادي - 40 سؤال)
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

# ==========================================
# قائمة الأسئلة الموسعة (مستوى متوسط - 40 سؤال)
# ==========================================
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

# ==========================================
# قائمة الأسئلة الموسعة (مستوى جريء جداً وخصوصي - 40 سؤال)
# ==========================================
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
    "هل سبق أن تورطت في مشكلة كبيرة وكذبت لكي ينجو غيرك بدلاً منك؟", "من هو الشخص الذي تتمنى أن تعتذر له بشدة عما بدر منك؟",
    "هل تكره شخصاً لمجرد الغيرة منه؟", "ما هو أكثر موقف شعرت فيه أنك كنت 'شخصاً سيئاً'؟",
    "هل تحب مراقبة حياة الآخرين والفضول حول أسرارهم؟", "ما هو أغرب شعور مررت به في حياتك العاطفية؟",
    "هل سبق أن خططت للانتقام من شخص أهانك؟", "ما هو أعمق سر تخفيه عن عائلتك تماماً؟",
    "هل تشعر بالرضا عن صورتك وأفعالك أمام نفسك وأنت وحيد؟", "من هو الشخص الذي تخشى خسارته أكثر من أي شخص آخر؟",
    "هل سبق أن تسببت في مشكلة كبيرة بين شخصين ثم تظاهرت بالبراءة؟", "ما هو الشيء الذي تفعله سراً وتظن أنه عيب ولكنك تحبه؟",
    "هل تمتلك الجرأة لمواجهة شخص ظلمك أم تفضل الصمت؟", "ما هو الاعتراف الأخير الذي لا تملكه الجرأة لقوله لأحد هنا؟",
    "هل تعتقد أنك شخص أناني في تعاملاتك الخاصة؟", "ما هو الموقف الذي جعلك تشعر بالحقارة تجاه نفسك؟",
    "هل سبق أن استغلت طيبة شخص لغرض شخصي؟", "من هو أكثر شخص تسبب في تحطيم مشاعرك يوماً ما؟",
    "ما هو الشيء الذي لو عرفه الناس عنك لتغيرت نظرتهم لك تماماً؟", "هل أنت راضٍ عن الشخص الذي أصبحت عليه اليوم؟"
]

# ==========================================
# بيانات متجر الظلام (العتاد والمعدات والرتب)
# الرتب: شائع -> نادر -> ملحمي -> أسطوري -> السفاح -> الجحيم -> الشيطان (الأعلى)
# ==========================================
DARK_SHOP_ITEMS = {
    "خناجر": [
        {"id": "d1", "name": "خنجر الظل الصامت", "tier": "نادر", "power": 25, "price": 80},
        {"id": "d2", "name": "خنجر الدم الخفي", "tier": "أسطوري", "power": 85, "price": 300},
        {"id": "d3", "name": "خنجر دم الملوك", "tier": "السفاح", "power": 150, "price": 600}
    ],
    "سيوف": [
        {"id": "s1", "name": "سيف الفولاذ المظلم", "tier": "نادر", "power": 35, "price": 100},
        {"id": "s2", "name": "سيف الموت الأسود", "tier": "ملحمي", "power": 70, "price": 250},
        {"id": "s3", "name": "سيف إبليس العاصف", "tier": "الشيطان", "power": 300, "price": 1200}
    ],
    "مطرقات": [
        {"id": "h1", "name": "مطرقة الحطاب الملعونة", "tier": "نادر", "power": 40, "price": 120},
        {"id": "h2", "name": "مطرقة الأرض المحروقة", "tier": "أسطوري", "power": 100, "price": 400},
        {"id": "h3", "name": "مطرقة جحيم التردي", "tier": "الجحيم", "power": 250, "price": 950}
    ],
    "خوذ": [
        {"id": "hl1", "name": "خوذة الحارس المظلم", "tier": "نادر", "power": 20, "price": 70},
        {"id": "hl2", "name": "خوذة الأطياف", "tier": "ملحمي", "power": 65, "price": 220},
        {"id": "hl3", "name": "خوذة الرعب المطلق", "tier": "الجحيم", "power": 200, "price": 800}
    ],
    "دروع": [
        {"id": "a1", "name": "درع الجلد المتسخ", "tier": "شائع", "power": 15, "price": 50},
        {"id": "a2", "name": "درع الفولاذ الأسود", "tier": "ملحمي", "power": 80, "price": 300},
        {"id": "a3", "name": "درع الهالك الأبدي", "tier": "الشيطان", "power": 350, "price": 1500}
    ],
    "ساق": [
        {"id": "l1", "name": "واقي الساق الملعون", "tier": "نادر", "power": 18, "price": 60},
        {"id": "l2", "name": "دروع الأرجل الفولاذية", "tier": "أسطوري", "power": 70, "price": 250},
        {"id": "l3", "name": "واقي ساق السفاح", "tier": "السفاح", "power": 130, "price": 550}
    ],
    "حذاء": [
        {"id": "b1", "name": "حذاء اللصوص الخفيف", "tier": "شائع", "power": 10, "price": 40},
        {"id": "b2", "name": "حذاء الرياح المظلمة", "tier": "أسطوري", "power": 50, "price": 180},
        {"id": "b3", "name": "حذاء الجحيم السريع", "tier": "الجحيم", "power": 180, "price": 700}
    ]
}

# ==========================================
# كلاسات متجر الظلام (منيو تفاعلي)
# ==========================================
class DarkShopItemsView(discord.ui.View):
    def __init__(self, category_name):
        super().__init__(timeout=None)
        self.category_name = category_name
        self.add_item(DarkShopItemSelect(category_name))

class DarkShopItemSelect(discord.ui.Select):
    def __init__(self, category_name):
        self.category_name = category_name
        items = DARK_SHOP_ITEMS.get(category_name, [])
        options = []
        for item in items:
            emoji_map = {"شائع": "⚪", "نادر": "🟢", "ملحمي": "🔵", "أسطوري": "🟣", "السفاح": "🗡️", "الجحيم": "🔥", "الشيطان": "👑"}
            emo = emoji_map.get(item['tier'], "⚔️")
            options.append(
                discord.SelectOption(
                    label=item['name'],
                    description=f"الرتبة: {item['tier']} | القوة: +{item['power']} | السعر: {item['price']} عملة",
                    emoji=emo,
                    value=item['id']
                )
            )
        super().__init__(placeholder=f"اختر قطعة من قسم {category_name} للشراء...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_id = self.values[0]
        chosen_item = None
        for cat, items in DARK_SHOP_ITEMS.items():
            for it in items:
                if it['id'] == selected_id:
                    chosen_item = it
                    break
        
        if not chosen_item:
            await interaction.response.send_message("❌ القطعة غير موجودة!", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        user = users_col.find_one({"user_id": user_id})
        if not user:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`", ephemeral=True)
            return

        balance = user.get("balance", 0)
        price = chosen_item["price"]

        if balance < price:
            await interaction.response.send_message(f"❌ رصيدك غير كافي! تحتاج إلى {price} عملة بينما رصيدك هو {balance} عملة.", ephemeral=True)
            return

        # الخصم وإضافة القطعة للمقتنيات
        new_balance = balance - price
        inventory = user.get("inventory", [])
        inventory.append(f"{chosen_item['name']} (قوة: +{chosen_item['power']})")

        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance, "inventory": inventory}}
        )

        embed = discord.Embed(
            title="🛒 تم الشراء بنجاح من متجر الظلام!",
            description=f"لقد قمت بشراء **{chosen_item['name']}**!\n\n🛡️ **الرتبة:** {chosen_item['tier']}\n⚡ **القوة المضافة:** +{chosen_item['power']}\n💰 **السعر المدفوع:** {price} عملة\n💰 **رصيدك المتبقي:** {new_balance} عملة",
            color=0x2c2f33
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DarkShopCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر قسماً من أقسام متجر الظلام...",
        options=[
            discord.SelectOption(label="الخناجر", description="خناجر سريعة وقاتلة في الظل", emoji="🗡️"),
            discord.SelectOption(label="السيوف", description="سيوف ثقيلة ومدمرة للخصوم", emoji="⚔️"),
            discord.SelectOption(label="المطرقات", description="مطرقات تحطم الدروع بقسوة", emoji="🔨"),
            discord.SelectOption(label="الخوذ", description="حماية للرأس من الضربات القاتلة", emoji="🪖"),
            discord.SelectOption(label="الدروع", description="دروع صلبة لامتصاص الهجمات", emoji="🛡️"),
            discord.SelectOption(label="الساق", description="واقيات الأرجل والسيقان", emoji="🦵"),
            discord.SelectOption(label="الحذاء", description="أحذية خفيفة للسرعة والمناورة", emoji="👢")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat = select.values[0]
        embed = discord.Embed(
            title=f"🌑 متجر الظلام - قسم ({cat})",
            description=f"استعرض العتاد المتاح في قسم **{cat}**:\n*(أعلى ثلاث رتب في المتجر هي: السفاح، الجحيم، الشيطان)*",
            color=0x7289da
        )
        view = DarkShopItemsView(cat)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==========================================
# كلاسات اللعبة التفاعلية (أسئلة عامة مع الأدوار وأزرار التحكم)
# ==========================================
class ActiveQuestionsGame(discord.ui.View):
    def __init__(self, players, questions_list, level_name):
        super().__init__(timeout=None)
        self.players = players
        self.questions_list = questions_list
        self.level_name = level_name
        self.current_turn = 0

    @discord.ui.button(label="السؤال التالي 🎲", style=discord.ButtonStyle.primary, custom_id="next_q_btn")
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("❌ أنت لست مشاركاً في هذه اللعبة النشطة!", ephemeral=True)
            return

        self.current_turn = (self.current_turn + 1) % len(self.players)
        current_player = self.players[self.current_turn]
        question = random.choice(self.questions_list)

        embed = discord.Embed(
            title=f"🎯 لعبة الأسئلة والصراحة - مستوى ({self.level_name})",
            description=f"👤 **الدور الآن على:** {current_player.mention}\n\n💬 **السؤال:**\n`{question}`",
            color=0xe74c3c
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="إيقاف اللعبة 🛑", style=discord.ButtonStyle.danger, custom_id="stop_q_btn")
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("❌ المشاركون فقط في اللعبة يمكنهم إيقافها!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛑 تم إيقاف اللعبة",
            description=f"تم إنهاء جلسة اللعب بواسطة {interaction.user.mention}.\nشكراً لكل من شارك وتفاعل!",
            color=0x2c3e50
        )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

class GameLobby(discord.ui.View):
    def __init__(self, host, questions_list, level_name):
        super().__init__(timeout=None)
        self.host = host
        self.questions_list = questions_list
        self.level_name = level_name
        self.players = [host]

    def generate_embed(self):
        players_mentions = "\n".join([f"👤 {p.mention}" for p in self.players])
        return discord.Embed(
            title=f"⏳ غرفة انتظار لعبة الأسئلة ({self.level_name})",
            description=f"المستضيف: {self.host.mention}\n\n**اللاعبون المنضمون ({len(self.players)}):**\n{players_mentions}\n\n*(الحد الأدنى للبدء: لاعبان فأكثر)*",
            color=0x3498db
        )

    @discord.ui.button(label="مشاركة ✋", style=discord.ButtonStyle.success, custom_id="join_lobby_btn")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("❌ أنت منضم بالفعل في هذه الغرفة!", ephemeral=True)
            return
        
        self.players.append(interaction.user)
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="بدء اللعبة ▶️", style=discord.ButtonStyle.primary, custom_id="start_lobby_btn")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ المستضيف وحده هو من يمكنه بدء اللعبة!", ephemeral=True)
            return
        
        if len(self.players) < 2:
            await interaction.response.send_message("❌ يجب أن يكون هناك لاعبان على الأقل في الغرفة لبدء اللعبة!", ephemeral=True)
            return

        question = random.choice(self.questions_list)
        first_player = self.players[0]
        
        embed = discord.Embed(
            title=f"🎯 بدأت اللعبة - مستوى ({self.level_name})",
            description=f"👤 **الدور الأول على:** {first_player.mention}\n\n💬 **السؤال:**\n`{question}`",
            color=0xe74c3c
        )
        
        active_view = ActiveQuestionsGame(self.players, self.questions_list, self.level_name)
        await interaction.response.edit_message(embed=embed, view=active_view)

class DifficultySelection(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=None)
        self.host = host

    @discord.ui.button(label="عادي 🟢", style=discord.ButtonStyle.success)
    async def normal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host: return
        lobby = GameLobby(self.host, NORMAL_QUESTIONS, "عادي")
        await interaction.channel.send(embed=lobby.generate_embed(), view=lobby)
        await interaction.response.edit_message(content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!", embed=None, view=None)

    @discord.ui.button(label="متوسط 🟡", style=discord.ButtonStyle.secondary)
    async def medium_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host: return
        lobby = GameLobby(self.host, MEDIUM_QUESTIONS, "متوسط")
        await interaction.channel.send(embed=lobby.generate_embed(), view=lobby)
        await interaction.response.edit_message(content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!", embed=None, view=None)

    @discord.ui.button(label="جريء جداً وخصوصي 🔥", style=discord.ButtonStyle.danger)
    async def bold_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host: return
        lobby = GameLobby(self.host, BOLD_QUESTIONS, "جريء جداً وخصوصي")
        await interaction.channel.send(embed=lobby.generate_embed(), view=lobby)
        await interaction.response.edit_message(content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!", embed=None, view=None)

class GamesMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر لعبة من المنيو لتشغيلها...",
        options=[
            discord.SelectOption(label="لعبة الأسئلة والصراحة", description="أسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً وخصوصي)", emoji="🎯"),
            discord.SelectOption(label="لعبة لو خيروك", description="تخيير اللاعبين بين خيارين صعبين ومضحكين!", emoji="🆚"),
            discord.SelectOption(label="لعبة روليت الملكي", description="أدار الروليت الملكي واحصل على كنز الملك أو عقوبته!", emoji="👑")
        ]
    )
    async def select_game(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        
        if "الأسئلة" in choice:
            embed = discord.Embed(
                title="🎯 اختر مستوى صعوبة الأسئلة والصراحة",
                description="حدد المستوى المطلوب لكي يتم فتح غرفة الانتظار في الشات العام:",
                color=0x2ecc71
            )
            await interaction.response.send_message(embed=embed, view=DifficultySelection(interaction.user), ephemeral=True)
            
        elif "لو خيروك" in choice:
            options_list = [
                "🆚 تخسر كل أموالك أم تنسى أصدقائك المقربين للأبد؟",
                "🆚 تعيش بدون إنترنت لمدة سنة أم بدون هاتف محمول لمدة شهرين؟",
                "🆚 تتكلم لغة الحيوانات أم تقرأ أفكار الناس؟",
                "🆚 تطير في الهواء أم تغوص في أعماق البحار؟",
                "🆚 تأكل طعاماً حاراً جداً طوال حياتك أم طعاماً بلا صوص أبداً؟"
            ]
            await interaction.channel.send(f"**لعبة لو خيروك لـ {interaction.user.mention}:**\n`{random.choice(options_list)}`")
            await interaction.response.send_message("✅ تم إرسال لعبة لو خيروك في الشات العام!", ephemeral=True)
            
        elif "روليت الملكي" in choice:
            outcomes = [
                "👑 **حظ الملك:** لقد منحك الملك خزينة القلعة! ربحت 50 عملة ذهبية.",
                "👑 **غضب الملك:** أمر الملك بمصادرة جزء من أموالك! خسرت 20 عملة.",
                "👑 **عفو ملكي:** لم يحدث شيء، خرجت سالماً من قصر الملك دون خسارة أو ربح!",
                "👑 **وليمة القلعة:** أقام لك الملك وليمة فاخرة وكافأك بـ 30 عملة!"
            ]
            result = random.choice(outcomes)
            user_id = str(interaction.user.id)
            user = users_col.find_one({"user_id": user_id})
            
            if user:
                current_balance = user.get("balance", 0)
                if "ربحت 50" in result:
                    users_col.update_one({"user_id": user_id}, {"$set": {"balance": current_balance + 50}})
                    result += f"\n💰 رصيدك الجديد: {current_balance + 50} عملة"
                elif "خسرت 20" in result:
                    new_b = max(0, current_balance - 20)
                    users_col.update_one({"user_id": user_id}, {"$set": {"balance": new_b}})
                    result += f"\n💰 رصيدك الحالي: {new_b} عملة"
                elif "كافأك بـ 30" in result:
                    users_col.update_one({"user_id": user_id}, {"$set": {"balance": current_balance + 30}})
                    result += f"\n💰 رصيدك الجديد: {current_balance + 30} عملة"
                    
            await interaction.channel.send(f"{interaction.user.mention} 🎲\n{result}")
            await interaction.response.send_message("✅ تم تدوير الروليت الملكي في الشات العام!", ephemeral=True)

# ==========================================
# الأحداث والأوامر الأساسية للبوت
# ==========================================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f"✅ البوت {bot.user} جاهز ويعمل بكفاءة عالية!")

@bot.tree.command(name="تسجيل", description="تسجيل حساب جديد في النظام والحصول على الهدية")
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if users_col.find_one({"user_id": user_id}):
        await interaction.response.send_message("❌ أنت مسجل مسبقاً بالفعل في قاعدة البيانات!", ephemeral=True)
        return
    
    users_col.insert_one({
        "user_id": user_id,
        "username": interaction.user.name,
        "balance": 100,
        "inventory": []
    })
    await interaction.response.send_message("✅ تم تسجيلك بنجاح وحصلت على 100 عملة هدية ترحيبية!", ephemeral=True)

@bot.tree.command(name="بروفايل", description="عرض ملفك الشخصي ورصيدك ومقتنياتك")
async def profile(interaction: discord.Interaction):
    user = users_col.find_one({"user_id": str(interaction.user.id)})
    if not user:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`", ephemeral=True)
        return
        
    embed = discord.Embed(title=f"👤 ملف اللاعب: {interaction.user.name}", color=0x3498db)
    embed.add_field(name="💰 الرصيد", value=f"{user.get('balance', 0)} عملة", inline=False)
    inventory = user.get('inventory', [])
    items_text = ", ".join(inventory) if inventory else "لا توجد مقتنيات حالياً"
    embed.add_field(name="🎒 المقتنيات والعتاد", value=items_text, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="الابطال", description="عرض قاعة الأبطال الأسطوريين")
async def heroes(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة الأبطال الأسطوريين",
        description="🌸 **إيليا (Ilia):** أميرة النور والرياح\n(مهارات سرعة وسحر هائل).\n\n⚡ **المقاتل الظلي:** بطل هجمات الخفاء والسرعة.\n🛡️ **حارس القلعة:** مدافع لا يُقهر.",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر", description="عرض المتجر العادي لشراء الأدوات")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 المتجر العجيب",
        description="استخدم رصيدك لشراء الأدوات المميزة:\n\n1️⃣ **سيف أسطوري** - السعر: 50 عملة\n2️⃣ **درع حماية** - السعر: 40 عملة",
        color=0xf1c40f
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="متجر_الظلام", description="دخول متجر الظلام لشراء العتاد الأسطوري القوي")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌑 متجر الظلام المحرم",
        description="مرحباً بك أيها المتابع في أعماق متجر الظلام.\nهنا حيث تصنع الأسلحة الفتاكة والعتاد المظلم!\n\n👑 **أعلى ثلاث رتب في المتجر:**\n1️⃣ **الشيطان** (القوة المطلقة)\n2️⃣ **الجحيم** (مدمر الحصون)\n3️⃣ **السفاح** (سيد الخفاء والفتك)\n\nاختر القسم المطلوب من القائمة بالأسفل لاستعراض العتاد:",
        color=0x111111
    )
    await interaction.response.send_message(embed=embed, view=DarkShopCategoryView(), ephemeral=True)

@bot.tree.command(name="العاب", description="فتح قائمة الألعاب التفاعلية المتاحة للسيرفر")
async def games(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قائمة الألعاب المتاحة",
        description="اختر إحدى الألعاب من القائمة المنسدلة بالأسفل:",
        color=0x9b59b6
    )
    await interaction.response.send_message(embed=embed, view=GamesMenuView(), ephemeral=True)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
