import os
import re
import random
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة جميع الأنظمة والألعاب بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل الآن باسم: {bot.user}")

# ================== قاعدة بيانات الأسئلة (50 سؤال لكل مستوى) ==================
TRIVIA_QUESTIONS = {
    "عادي": [
        "ما هو لون السماء في الأيام الصافية؟", "كم عدد أيام السنة الميلادية؟", "ما هو الحيوان المعروف بملك الجحيم/الغابة؟", "في أي قارة تقع مصر؟", "ما هو عاصمة المملكة العربية السعودية؟",
        "كم عدد ساعات اليوم الواحد؟", "ما هو أسرع حيوان بري في العالم؟", "من هو نبيل الكرتون الذي يبحث عن أمه (سندباد أم ريمي؟)", "ما هو العنصر الكيميائي للماء؟", "كم عدد الألوان في قزح (الطقس)؟",
        "ما هي عاصمة فرنسا؟", "ما هو أكبر كوكب في المجموعة الشمسية؟", "ما هو الحيوان الذي يعيش في الصحراء ويسمى سفينة الصحراء؟", "كم عدد أرجل العنكبوت؟", "ما هو الغاز الذي يتנفسه الإنسان؟",
        "ما هي الدولة الأكثر سكاناً في العالم؟", "ما هو أطول نهر في العالم؟", "ما هي العملة الرسمية في اليابان؟", "كم عدد أضلاع المثلث؟", "ما هو الفاكهة التي تُعرف بملك الفواكه (دوريان)؟",
        "في أي عام هبط الإنسان على سطح القمر لأول مرة؟", "ما هو المعدن الثمين الذي يُرمز له بالرمز Au؟", "ما هو الحيوان الذي ينام واقفاً؟", "كم عدد ألوان العلم العراقي؟", "ما هو الطائر الذي لا يمكنه الطيران ولكنه سريع الجري؟",
        "ما هي عاصمة إيطاليا؟", "ما هو الحيوان البحرى الذى يمتلك 3 قلوب؟", "ما هي عاصمة الإمارات العربية المتحدة؟", "ما هو أكبر بحر مغلق في العالم (بحر قزوين)؟", "كم عدد أسنان الإنسان البالغ الطبيعية؟",
        "ما هو الكوكب الملقب بالكوكب الأحمر؟", "من هو مصباح علاء الدين المرافق له؟", "ما هو الحيوان الأطول رقبة في العالم؟", "ما هي عاصمة ألمانيا؟", "كم عدد حروف اللغة العربية؟",
        "ما هو الحيوان الذي يغير رنگه حسب بيئته؟", "ما هي عاصمة إسبانيا؟", "ما هو البحر الذي يقع بين إفريقيا وآسيا؟", "كم عدد عجائب الدنيا السبع القديمة؟", "ما هو أسرع طائر في العالم؟",
        "ما هي عاصمة تركيا؟", "ما هو الكوكب الأقرب إلى الشمس؟", "من هو الكاتب المسرحي الشهير ويليام ...؟", "ما هي الدولة التي تقرع فيها أجراس الكنائس للإعلان عن بدء العام؟", "ما هو الحيوان الذي يُصدر صوت النعيب؟",
        "ما هي عاصمة روسيا؟", "كم عدد الولايات في الولايات المتحدة الأمريكية؟", "ما هو الحيوان الذي يُعتبر رمزا للذكاء والحكمة في الأساطير؟", "ما هي عاصمة الصين؟", "ما هو العنصر الأكثر توفراً في قشرة الأرض؟"
    ],
    "متوسط": [
        "ما هي عاصمة أستراليا (ليست سيدني)؟", "من هو القائد المسلم الذي فتح قسطنطينية؟", "في أي عام قامت الحرب العالمية الأولى؟", "ما هو أكبر أقيانوس في العالم؟", "من هو مكتوب قانون الجاذبية الأرضية؟",
        "ما هي الدولة التي تُلقب ببلاد الـ 1000 بحيرة؟", "ما هو أعمق أخدود في العالم؟", "من هو مؤلف رواية البؤساء؟", "ما هو الكوكب الذي يدور حول نفسه بشكل معكوس تقريباً (الزهرة)؟", "ما هي أصغر دولة مستقلة في العالم مساحة؟",
        "في أي معركة استشهد حمزة بن عبد المطلب رضي الله عنه؟", "ما هو غاز الحياة الذي تنتجه النباتات بعملية البناء الضوئي؟", "من هو صاحب لقب أمير الشعراء؟", "ما هي الدولة الأكثر إنتاجاً للقهوة في العالم؟", "ما هو أسرع قطار في العالم حالياً (ماغليف)؟",
        "كم عدد مساحات قارة آسيا مقارنة بيابس الأرض؟", "من هو الإمبراطور الروماني الذي تم اغتياله في ايام مارس؟", "ما هو أطول جسر بحري في العالم؟", "ما هي عاصمة كندا؟", "ما هو الحيوان الذي له القدرة على تجديد أطرافه المقطوعة (السمندل)؟",
        "ما هو أكبر صحراء غير جليدية في العالم؟", "في أي عام تم توقيع اتفاقية سايكس بيكو؟", "من هو مخترع المصباح الكهربائي التجاري؟", "ما هي عاصمة البرازيل؟", "ما هو الحيوان البري الذي يمتلك أقوى قوة عض؟",
        "ما هي الدولة العربية الوحيدة التي لا تملك حدوداً برية مع دول أخرى (جزيرة)؟", "من هو أول رئيس للولايات المتحدة الأمريكية؟", "ما هو أطول جبل في العالم فوق سطح البحر؟", "ما هي عاصمة الأرجنتين؟", "ما هو اسم الفيلسوف اليوناني الذي أعدم بشرب السم؟",
        "ما هي المعاهدة التي أنهت الحرب العالمية الأولى رسمياً؟", "من هو رائد الفضاء الذي كان أول من مشى على سطح القمر؟", "ما هي عاصمة جنوب إفريقيا (الإدارية)؟", "ما هو الكوكب ذو الحلقات الأكثر وضوحاً؟", "من هو مكتوب الدورة الدموية الصغرى؟",
        "ما هي عاصمة الهند؟", "ما هو أقدم هرم في مصر القديمة (هرم سقارة المدرج)؟", "من هو مؤسس علم الاجتماع الحديث؟", "ما هي عاصمة النمسا؟", "ما هو العنصر الكيميائي الأكثر وفرة في الكون؟",
        "في أي عام تأسست منظمة الأمم المتحدة؟", "من هو القائد العسكري الذي هزم هانيبال في معركة زاما؟", "ما هي عاصمة اليونان؟", "ما هو الحيوان البحري الذي يُعتبر الأسرع سباحة؟", "من هو الشاعر الذي كتب المعلقة الشهيرة التي تبدأ بـ (قفا نبكِ)؟",
        "ما هي عاصمة كوريا الجنوبية؟", "ما هو أقدم جامعة مستمرة في العالم (جامعة القرويين)؟", "من هو العالم الذي وضع نظرية النسبية؟", "ما هي عاصمة نيوزيلندا؟", "ما هو أطول نهر في قارة أوروبا؟"
    ],
    "جريئ جدا": [
        "ما هو أكثر شيء تندم عليه بجدية في حياتك الماضية؟", "لو اضطررت لسرقة شيء واحد للنجاة بحياتك، ماذا ستسرق ومن أين؟", "من هو الشخص في هذا السيرفر الذي تتمنى لو لم تقابله أبداً؟", "ما هو أكبر سر تحافظ عليه بشدة وتخافه أن ينكشف لعائلتك؟", "هل سبق لك أن كذبت كذبة كبيرة ونجحت فيها تماماً دون أن يعلم أحد؟ ما هي؟",
        "لو أتيحت لك الفرصة لمسح شخص واحد من ذاكرتك للأبد، من سيكون؟", "ما هو أغبى مبلغ مال دفعته على شيء تافه وندمت عليه لاحقاً؟", "هل تشعر بالغيرة من أحد أصدقائك المقربين؟ من ولماذا؟",
        "ما هو الموقف الأكثر إحراجاً الذي تعرضت له أمام شخص تعجب به؟", "لو كان بإمكانك معرفة يوم وفاتك بالتحديد، هل ستختار معرفته؟ ولماذا؟",
        "ما هو أكثر صفة تكرهها في نفسك وتتمنى تغييرها فوراً؟", "هل قمت بيوم من الأيام بخيانة ثقة شخص ضحى بالكثير من أجلك؟", "ما هو أجرأ قرار اتخذته في حياتك وعرضك لخطر حقيقي؟",
        "من هو الشخص الذي تعتبره منافسك الأكبر في الحياة؟", "لو طُلب منك توجيه انتقاد لاذع ولا يُنسى لأحد الأشخاص الآن، لمن ستوجهه؟",
        "ما هي أقوى كذبة قلتها لأهلك وصدقوها دون شك؟", "هل تبكي سراً غالباً؟ متى كانت آخر مرة ولمَ؟", "ما هو الشيء الذي تفعله سراً وتخاف أن يعلم به المجتمع؟",
        "لو خيروك بين العيش بلا إحساس نهائياً أو الشعور بالألم المضاعف، ماذا تختار؟", "هل تؤمن بالحب من أول نظرة أم تعتقد أنه مجرد وهم مؤقت؟",
        "ما هو أكبر خطأ ارتكبته في حق شخص آخر ولم تعتذر عنه أبداً؟", "لو كان بإمكانك العودة بالزمن لتغيير قرار واحد مصيري، أي قرار ستغير؟",
        "من هو الشخص الذي إذا غاب عن حياتك تشعر بأن نصفك قد ضاع؟", "ما هو أكثر شعور مرعب جربته طوال حياتك؟", "هل تفضل العيش غنياً ولكن مكروهاً من الجميع، أم فقيراً ومحبوباً؟",
        "ما هو السر الذي تخفيه عن أعز أصدقائك حتى هذه اللحظة؟", "لو أُتيح لك أن تسرق فكرة شخص آخر وتنسبها لك، هل ستفعلها؟", "ما هي الكلمة الوحيدة التي لا تستطيع قولها لوالديك أبداً؟",
        "هل سبق لك أن تنمرت على شخص ما وندمت على ذلك لاحقاً؟", "ما هو أكثر موقف شعرت فيه بالحقارة تجاه نفسك؟", "لو خيروك بين معرفة متى تموت أو كيف تموت، ماذا تختار؟",
        "هل تعتبر نفسك شخصاً أنانياً عندما يتعلق الأمر بمصالحك الشخصية؟", "ما هي أقصى عقوبة تعرضت لها في طفولتك وبقيت محفورة بذاكرتك؟", "ما هو الشيء الذي لو خسبته تشعر بأن حياتك انتهت؟",
        "هل قمت بيوم من الأيام بسرقة شيء صغير ولم يعلم أحد؟", "من هو الشخص الذي تتمنى الانتقام منه يوماً ما؟", "ما هو أكثر عيب جسدي أو نفسي تتمنى إخفاءه عن عيون الناس؟",
        "لو كان بإمكانك تغيير اسمك وجنسيتك تماماً والهرب لبلد آخر، هل ستفعلها؟", "ما هو أكثر اعتراف تخشى أن تقوله بصوت علني أمام الجميع؟", "هل تثق في أي شخص بالكامل بنسبة 100%، أم أن الشك أساس المعاملة؟",
        "ما هي أكبر خذلان تعرضت له من شخص كنت تظنه سنداً لك؟", "لو طُلب منك التضحية بشيء ثمين جداً مقابل تحقيق أمنية واحدة، ماذا ستضحي؟",
        "هل تعتقد أنك شخص ظالم في بعض مواقفك الحياتية؟", "ما هو الهاجس أو الكابوس المتكرر الذي يطاردك في منامك؟", "هل تجد صعوبة في مسامحة الآخرين أم أن قلبك قاسي؟",
        "ما هو القرار الأرعن الذي اتخذته ونجوت منه بأعجوبة؟", "من هو الشخص الذي تتهرب من مكالماته ورسائله دائماً؟", "هل سبق لك أن تمنت الشر لشخص تسبب في أذاك؟",
        "ما هو أقسى وصف قيل لك في وجهك وجرح كرامتك بعمق؟", "لو عاد بك الزمن للوراء، هل ستختار نفس مسار حياتك الحالي؟"
    ]
}

# ================== نظام الألعاب المنفصل (أمر /العاب) ==================
class TriviaQuestionView(discord.ui.View):
    def __init__(self, difficulty, questions_list, author_id):
        super().__init__(timeout=300)
        self.difficulty = difficulty
        self.questions_list = questions_list
        self.author_id = author_id
        self.current_q = random.choice(questions_list)

    @discord.ui.button(label="سؤال جديد 🎲", style=discord.ButtonStyle.primary)
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
        
        self.current_q = random.choice(self.questions_list)
        embed = discord.Embed(
            title=f"🧠 لعبة الأسئلة (مستوى: {self.difficulty})",
            description=f"**السؤال:**\n{self.current_q}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه اللعبة تخص شخصاً آخر!", ephemeral=True)
            return False
        return True

class TriviaDifficultySelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="عادي", description="أسئلة عامة وبسيطة (50 سؤالاً)", emoji="🟢", value="عادي"),
            discord.SelectOption(label="متوسط", description="أسئلة ثقافية وتاريخية (50 سؤالاً)", emoji="🟡", value="متوسط"),
            discord.SelectOption(label="جريئ جدا", description="أسئلة صريحة وتحديات شخصية (50 سؤالاً)", emoji="🔴", value="جريئ جدا")
        ]
        super().__init__(placeholder="اختر مستوى صعوبة الأسئلة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        level = self.values[0]
        q_list = TRIVIA_QUESTIONS.get(level, TRIVIA_QUESTIONS["عادي"])
        selected_q = random.choice(q_list)

        embed = discord.Embed(
            title=f"🧠 لعبة الأسئلة (مستوى: {level})",
            description=f"**السؤال:**\n{selected_q}",
            color=discord.Color.purple()
        )
        view = TriviaQuestionView(level, q_list, self.author_id)
        await interaction.response.edit_message(content=None, embed=embed, view=view)

class TriviaDifficultyView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.add_item(TriviaDifficultySelect(author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

class GamesMenuSelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="لعبة الأسئلة", description="تحديات وأسئلة بمستويات مختلفة (عادي، متوسط، جريئ)", emoji="❓", value="trivia"),
            # يمكنك إضافة ألعاب أخرى هنا مستقبلاً
        ]
        super().__init__(placeholder="اختر اللعبة التي تريد إطلاقها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        if choice == "trivia":
            embed = discord.Embed(
                title="❓ اختيار مستوى لعبة الأسئلة",
                description="يرجى تحديد مستوى الصعوبة المطلوب من القائمة أدناه:",
                color=discord.Color.blue()
            )
            view = TriviaDifficultyView(self.author_id)
            await interaction.response.edit_message(content=None, embed=embed, view=view)

class GamesMenuView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.add_item(GamesMenuSelect(author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="العاب", description="قائمة الألعاب الترفيهية المستقلة في السيرفر")
async def games_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="🎮 قاعة الألعاب الترفيهية",
        description="أهلاً بك في قسم الألعاب! اختر لعبتك المفضلة من القائمة بالأسفل:",
        color=discord.Color.dark_magenta()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/808/808439.png")
    
    view = GamesMenuView(interaction.user.id)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# ================== بقية الأوامر الأساسية (معارك، ملف، بنك، متاجر) ==================

class ShopSpecificSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category, page=0):
        self.items_pool = items_pool
        self.shop_type = shop_type
        self.category = category
        self.page = page
        start = page * 25
        current_items = items_pool[start:start + 25]
        options = [
            discord.SelectOption(label=f"{item['name']} [{item['tier']}]", value=item["id"], description=f"السعر: {item['price']} | {item['stats']}")
            for item in current_items
        ]
        super().__init__(placeholder=f"اختر من قسم {category} (صفحة {page+1})...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        item_id = self.values[0]
        item = next((it for it in self.items_pool if it["id"] == item_id), None)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if self.shop_type == "normal":
            if user_data.get("balance", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك العادي غير كافٍ! تحتاج `{item['price']}` 🪙.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}}, upsert=True)
        else:
            if user_data.get("diamonds", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك من الألماس غير كافٍ! تحتاج `💎 {item['price']}`.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}}, upsert=True)

        await interaction.followup.send(f"🎉 **تم الشراء بنجاح!** حصلت على **{item['name']}** `[{item['tier']}]`", ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self, author_id, shop_type):
        super().__init__(timeout=None)
        self.author_id = author_id
        options = [
            discord.SelectOption(label="خوذة", value="خوذة", emoji="🪖"),
            discord.SelectOption(label="درع", value="درع", emoji="🛡️"),
            discord.SelectOption(label="سيف", value="سيف", emoji="⚔️"),
            discord.SelectOption(label="عصا سحرية", value="عصا سحرية", emoji="🪄")
        ]
        self.add_item(discord.ui.Select(placeholder="اختر الفئة...", options=options))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى")
async def battle_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🏟️ ساحة المعارك", description="اختر نوع التحدي من القائمة:", color=discord.Color.dark_gold())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="الملف", description="عرض الملف الأسطوري")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    embed = discord.Embed(title="📜 الملف الشخصي", description=f"⚡ **اللقب:** `{user_data.get('custom_title', 'مقاتل مستجد')}`", color=discord.Color.dark_gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="بنك", description="فتح الحساب البنكي")
async def bank_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    embed = discord.Embed(title="🏦 البنك المركزي", description=f"رصيدك الحالي: `{user_data.get('balance', 0)}` 🪙", color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

bot.run(DISCORD_TOKEN)
