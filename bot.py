import os, random, asyncio, pymongo, discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MAIN_DEV_ID = "1103985971638325269"

client = pymongo.MongoClient(MONGO_URI)
db = client["game_database"]
users_col, guilds_col, devs_col = db["users"], db["guilds"], db["devs"]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
AUTO_BATTLES = {}
ACTIVE_GAMES = {}

def is_user_registered(uid) -> bool:
    return users_col.find_one({"user_id": str(uid)}) is not None

def is_dev(uid) -> bool:
    suid = str(uid)
    if suid == MAIN_DEV_ID or devs_col.find_one({"user_id": suid}):
        return True
    u = users_col.find_one({"user_id": suid})
    return bool(u and u.get("is_dev"))

def add_game_win(uid: str, game_key: str, pts: int = 1):
    users_col.update_one(
        {"user_id": str(uid)},
        {
            "$inc": {
                f"game_score.{game_key}": pts,
                "game_score.total": pts,
                "balance": pts * 100
            }
        },
        upsert=True
    )

CATEGORIES = ["خوذة", "درع", "بنطال", "حذاء", "سيف", "مطرقة", "خنجر", "عصا سحرية"]
DARK_RANKS = ["مشعوذ الظلال", "السفاح القرمزي", "الجحيم القاتل", "الشيطان الأبدي", "حاكم الظلمات"]
GEN_R = [("مبتدئ","🟢"), ("فولاذي","🪙"), ("ملكي","👑"), ("أسطوري","🌟"), ("إمبراطوري","🐉")]
DRK_R = [("مشعوذ الظلال","🌑"), ("السفاح القرمزي","🩸"), ("الجحيم القاتل","🔥"), ("الشيطان الأبدي","😈"), ("حاكم الظلمات","☠️")]

GEAR_DATA, ALL_GENERAL_ITEMS, ALL_DARK_ITEMS = {}, [], []
for cat in CATEGORIES:
    GEAR_DATA[cat] = []
    for i in range(1, 26):
        rk, em = GEN_R[(i-1)//5]
        g_item = {"id": f"gen_{cat}_{i}", "name": f"{em} {cat} [{rk}] T{i}", "rank": rk, "emoji": em, "power": i*50, "price": i*400, "store": "general"}
        GEAR_DATA[cat].append(g_item)
        ALL_GENERAL_ITEMS.append(g_item)

        drk, dem = DRK_R[(i-1)//5]
        d_item = {"id": f"dark_{cat}_{i}", "name": f"💀 {cat} [{drk}] T{i}", "rank": drk, "emoji": dem, "power": i*250, "price": i*8, "store": "dark"}
        GEAR_DATA[cat].append(d_item)
        ALL_DARK_ITEMS.append(d_item)

GEN_ITEM_POWER_MAP = {it["name"]: it["power"] for it in ALL_GENERAL_ITEMS}
DARK_ITEM_POWER_MAP = {it["name"]: it["power"] for it in ALL_DARK_ITEMS}

HEROES_CFG = {
    "valerian": {"name": "فالريان، سيف الشمس", "gender": "ذكر", "emoji": "⚔️", "story": "فارس أسطوري ولد تحت نجم ملتهب.", "base_power": 1200, "stats": {"leadership": 35, "attack": 30, "defense": 25, "aim": 10, "magic": 5, "intelligence": 15, "deception": 5}},
    "ignis": {"name": "إغنيس، سيد اللهب الأسود", "gender": "ذكر", "emoji": "🔥", "story": "ساحر ظلال قديم تحكم بعناصر النار المظلمة.", "base_power": 1350, "stats": {"magic": 40, "intelligence": 30, "attack": 25, "leadership": 10, "aim": 10, "defense": 10, "deception": 10}},
    "zephyr": {"name": "زفير، ظل الرماة", "gender": "ذكر", "emoji": "🎯", "story": "قناص الغابات المحرمة الذي لا تخطئ سهامه.", "base_power": 1150, "stats": {"aim": 40, "deception": 25, "attack": 25, "intelligence": 15, "defense": 10, "magic": 5, "leadership": 10}},
    "lucian": {"name": "لوكيان، حارس العرش الفولاذي", "gender": "ذكر", "emoji": "🛡️", "story": "درع الإمبراطورية الأخير الذي صمد أمام الجيوش.", "base_power": 1250, "stats": {"defense": 45, "leadership": 25, "intelligence": 20, "attack": 15, "aim": 5, "magic": 5, "deception": 5}},
    "malakai": {"name": "مالاكاي، حائك الأوهام", "gender": "ذكر", "emoji": "🎭", "story": "سيد التجسس والدسائس الذي يتلاعب بالعقول.", "base_power": 1100, "stats": {"deception": 45, "intelligence": 35, "aim": 15, "magic": 15, "leadership": 10, "attack": 10, "defense": 5}},
    "athena": {"name": "أثينا، قائدة الفرسان الستة", "gender": "أنثى", "emoji": "👑", "story": "إمبراطورة الميدان التي تقود الجيش بذكاء.", "base_power": 1300, "stats": {"leadership": 40, "defense": 25, "attack": 25, "intelligence": 20, "aim": 10, "magic": 5, "deception": 5}},
    "serene": {"name": "سيرين، كاهنة القمر والبحار", "gender": "أنثى", "emoji": "🔮", "story": "سيدة السحر السماوي لتطهير الأرض.", "base_power": 1400, "stats": {"magic": 45, "intelligence": 30, "leadership": 20, "defense": 15, "aim": 10, "deception": 5, "attack": 10}},
    "lyra": {"name": "ليرا، عاصفة السهام", "gender": "أنثى", "emoji": "🏹", "story": "صيادة سريعة كالعاصفة بأسلحة ضوئية.", "base_power": 1200, "stats": {"aim": 42, "attack": 28, "deception": 20, "intelligence": 15, "leadership": 10, "defense": 5, "magic": 10}},
    "morgana": {"name": "مورغانا، ملكة الدسائس", "gender": "أنثى", "emoji": "🖤", "story": "حاكمة الظلال التي تلاعبت بعقول الملوك.", "base_power": 1250, "stats": {"deception": 42, "magic": 30, "intelligence": 28, "aim": 10, "leadership": 10, "attack": 5, "defense": 5}},
    "hilda": {"name": "هيلدا، جدار الجليد", "gender": "أنثى", "emoji": "❄️", "story": "محاربة الشمال الأسطورية التي تسخر طاقة الجليد.", "base_power": 1280, "stats": {"defense": 40, "attack": 30, "leadership": 20, "intelligence": 15, "magic": 10, "aim": 10, "deception": 5}}
}

HERO_STATS_CFG = {
    "aim": ("التصويب", "🎯"), "magic": ("السحر", "🔮"), "attack": ("الهجوم", "🗡️"),
    "defense": ("الدفاع", "🛡️"), "intelligence": ("الذكاء", "🧠"), "deception": ("الخداع", "🎭"), "leadership": ("القيادة", "👑")
}

# ==================== بنك بيانات الألعاب ====================

QUESTIONS_DATA = {
    "normal": [f"ما هي موهبتك السرية رقم {i}؟" for i in range(1, 51)],
    "medium": [f"ما هو أكبر قرار ندمت عليه في حياتك رقم {i}؟" for i in range(1, 51)],
    "bold": [f"سؤال شديد السرية والجريء رقم {i}: هل خنت ثقة صديق من قبل؟" for i in range(1, 51)]
}

PUNISHMENTS_DATA = {
    "normal": [f"قم بغناء مقطع من أغنيتك المفضلة بصوت عالٍ." for _ in range(50)],
    "medium": [f"غير صورتك الشخصية لصورة مضحكة يختارها الروم لمدة 10 دقائق." for _ in range(50)],
    "bold": [f"اعترف بكلمة صريحة لشخص في السيرفر أمام الجميع فوراً." for _ in range(50)]
}

RIDDLES = [
    ("ما هو الشيء الذي كلما أخذت منه كبر؟", "الحفرة"),
    ("ما هو الشيء الذي يمشي بلا أرجل ويدخل الأذنين؟", "الصوت"),
    ("ما هو الشيء الذي ينبض بلا قلب؟", "الساعة"),
    ("ما هو الشيء الذي يحترق لِيُضيء لغيره؟", "الشمعة"),
    ("أخضر في الأرض، وأسود في السوق، وأحمر في البيت؟", "الشاي")
] + [(f"لغز رقم {i}: ما هو الشيء الذي له عين واحدة ولا يرى؟", "الابرة") for i in range(6, 151)]

MATH_EQUATIONS = [
    ("5 + 7 * 2", "19"), ("12 * 12", "144"), ("100 / 4 + 15", "40"),
    ("15 * 3 - 10", "35"), ("81 / 9 + 7", "16")
] + [(f"{i} + {i*2}", str(i + i*2)) for i in range(6, 151)]

ANIME_DATA = [
    ("بطل يستدعي تنين الجنيهات السبعة بالكرات الأسطورية", ["دراغون بول", "درغون بول"]),
    ("نينجا يطمح ليصبح الهوكاجي ويحمل الثعلب ذو التسعة أذيل", ["ناروتو", "ناروتو شيبودن"]),
    ("قرصان قبعة القش يبحث عن الكنز الأسطوري ليكون ملك القراصنة", ["ون بيس", "ونبيس"]),
    ("صياد يبحث عن والده ويخوض امتحان الصيادين مع أصدقائه", ["القناص", "هنتر"]),
    ("عمالقة يهاجمون الأسوار الشامخة والطفل ينتقم لأمه", ["هجوم العمالقة", "هجوم عمالقة"]),
    ("قاتل شياطين يحمل أخته في صندوق خشبي على ظهره", ["قاتل الشياطين", "ديمون سلاير"]),
    ("مستلهم السحر يستدعي كتاب المهارات ذو الخمس أوراق", ["بلاك كلوفر"]),
    ("أنمي عن الشينجامي والمفكرة السحرية التي تقتل من يُكتب اسمه فيها", ["دفتر الموت", "مذكرة الموت", "ديث نوت"]),
    ("طالب يبتلع إصبع ملك اللعنات لينتقل لعالم السحر واللعنات", ["جوجوتسو كايسن", "جوجوتسو"]),
    ("بطل صلب لا يهزم ويقضي على الأعداء بضربة واحدة فقط", ["ون بنش مان", "رجل الضربة الواحدة"]),
    ("طفل متحري يتقلص حجمه بعد تناول عقار سري ويحل القضايا", ["المحقق كونان", "كونان"]),
    ("طبيب نفسي يتعقب قاتلاً متسلسلاً عبقرياً في ألمانيا", ["مونستر", "مانستر"]),
    ("مجموعة من النينجا يرتدون زي الشينجامي ويحملون سيوف الزانباكتو", ["بليتش"]),
    ("محارب يرتدي قناع ليلوش ويقود ثورة ضد إمبراطورية بريطانيا", ["كود غياس", "كود جياس"]),
    ("عالم ألعاب افتراضية حيث الموت في اللعبة يعني الموت في الحقيقة", ["سورد آرت أونلاين", "سورد ارت اونلاين"]),
    ("لاعب شطرنج وسلاح مظلم يتم استدعاؤه في عالم موازٍ ليصبح الحاكم الأكبر", ["سولو ليفلينج", "سولو ليفلينغ"]),
    ("كيميائيان يبحثان عن حجر الفلاسفة لاستعادة أجسادهم المفقودة", ["الكيميائي المعدني", "فل ميتال"]),
    ("فتاة وأخيها يخوضان معركة في عالم الألعاب حيث كل شيء يتقرر باللعب", ["نو جيم نو لايف"]),
    ("مجموعة من العلماء الهواة يكتشفون طريقة لإرسال رسائل عبر الزمن", ["شتاينز جيت", "شتاينز غيت"]),
    ("فتى ينتحر في طوكيو فيتحول إلى نصف غول بعد زرع أعضاء له", ["طوكيو غول", "طوكيو جول"])
]

CUT_TWEETS = [
    "هل الصداقة بين الجنسين ممكنة بدون مشاعر حب مستقبلاً؟",
    "هل الذكاء الاصطناعي يستطيع استبدال الوظائف البشرية بالكامل؟",
    "هل المال يشتري السعادة الحقيقية بنسبة 100%؟",
    "هل خيانة الصديق أشد إيلاماً من خيانة الحبيب؟",
    "هل التغاضي يعتبر ضعف شخصية أم قمة الحكمة؟"
]

DECONSTRUCT_WORDS = [
    ("إمبراطورية", "إ م ب ر ا ط و ر ي ة"),
    ("شيطان", "ش ي ط ا ن"),
    ("مقاتل", "م ق ا ت ل"),
    ("أسطورة", "أ س ط و ر ة"),
    ("فرسان", "ف ر س ا ن")
] + [(f"كلمة{i}", " ".join(list(f"كلمة{i}"))) for i in range(6, 101)]

FASTEST_WORDS = [
    "الإمبراطورية العظمى", "سيد الظلال", "مقاتل الظلال الأسطوري",
    "بوت الديسكورد", "السفاح القرمزي", "الانتصار الملكي", "القتال الملكي",
    "ملك العالم", "سرعة البديهة", "البطل الأسطوري", "العرش الإمبراطوري",
    "البطل الخارق", "حاكم الجحيم", "فرسان الشرف", "درع الفولاذ", "سيف العدالة"
] + [f"كلمة_سريعة_{i}" for i in range(17, 150)]

# ==================== كلاسات أنظمة الألعاب ====================

class StopGameView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        ACTIVE_GAMES[self.channel_id] = False
        await ctx.response.send_message("🛑 تم إيقاف اللعبة التلقائية بنجاح!", ephemeral=False)

class GamesLeaderboardSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="أبطال الألعاب الشامل", value="total", emoji="🏆"),
            discord.SelectOption(label="أبطال الألغاز", value="riddles", emoji="🧩"),
            discord.SelectOption(label="أبطال الرياضيات", value="math", emoji="🧮"),
            discord.SelectOption(label="أبطال خمن الأنمي", value="anime", emoji="🎌"),
            discord.SelectOption(label="أبطال أسرع", value="fastest", emoji="⚡"),
            discord.SelectOption(label="أبطال فكك", value="deconstruct", emoji="🔤")
        ]
        super().__init__(placeholder="🏆 اختر ليدربورد الألعاب...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        all_u = list(users_col.find({"game_score": {"$exists": True}}))

        def get_score(u):
            gs = u.get("game_score", {})
            return gs.get(v, 0) if isinstance(gs, dict) else 0

        all_u.sort(key=get_score, reverse=True)

        txt_lines = []
        for idx, u in enumerate(all_u[:10]):
            score = get_score(u)
            if score > 0:
                txt_lines.append(f"#{idx+1} **{u.get('name','لاعب')}** — `{score:,}` نقطة 🏅")

        txt = "\n".join(txt_lines) if txt_lines else "لا يوجد متصدرين مسجلين في هذا التصنيف بعد!"

        emb = discord.Embed(
            title=f"🏆 │ ليدربورد الألعاب — [{self.values[0].upper()}]",
            description=txt,
            color=discord.Color.gold()
        )
        vw = discord.ui.View()
        vw.add_item(GamesLeaderboardSelect())
        await ctx.response.edit_message(embed=emb, view=vw)

class QuestionsGameView(discord.ui.View):
    def __init__(self, channel_id: int, level: str, players: list):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.level = level
        self.players = players

    @discord.ui.button(label="💥 طلب عقاب", style=discord.ButtonStyle.danger, row=0)
    async def punish_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        p = random.choice(PUNISHMENTS_DATA.get(self.level, PUNISHMENTS_DATA["normal"]))
        await ctx.response.send_message(f"💥 **العقاب المستحق:**\n`{p}`", ephemeral=False)

    @discord.ui.button(label="🛑 إيقاف اللعبة", style=discord.ButtonStyle.secondary, row=0)
    async def stop_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        ACTIVE_GAMES[self.channel_id] = False
        await ctx.response.send_message("🛑 تم إيقاف جلسة الأسئلة بنجاح.", ephemeral=False)

    async def start_loop(self, initial_msg):
        msg = initial_msg
        while ACTIVE_GAMES.get(self.channel_id, False):
            await asyncio.sleep(15)
            if not ACTIVE_GAMES.get(self.channel_id, False): break

            target_player = random.choice(self.players)
            question = random.choice(QUESTIONS_DATA.get(self.level, QUESTIONS_DATA["normal"]))

            emb = discord.Embed(
                title=f"🎲 │ لعبة الأسئلة والجريئة — [{self.level.upper()}]",
                description=(
                    f"🎲 **جاري تدوير النرد لاختيار الضحية...**\n"
                    f"🎯 **الدور على:** {target_player.mention}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❓ **السؤال:**\n`{question}`\n"
                    f"⏱️ **سيتغير السؤال واللاعب تلقائياً خلال 15 ثانية!**"
                ),
                color=discord.Color.red() if self.level == "bold" else discord.Color.gold()
            )
            try:
                await msg.edit(embed=emb, view=self)
            except:
                break

class QuestionsLevelSelect(discord.ui.Select):
    def __init__(self, players: list):
        self.players = players
        opts = [
            discord.SelectOption(label="المستوى العادي", value="normal", emoji="🟢", description="أسئلة خفيفة وممتعة"),
            discord.SelectOption(label="المستوى المتوسط", value="medium", emoji="🟡", description="أسئلة شخصية وتحديات"),
            discord.SelectOption(label="المستوى الجريء جداً", value="bold", emoji="🔴", description="أسئلة صريحة وقوية")
        ]
        super().__init__(placeholder="🎯 اختر مستوى صراحة الأسئلة...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        level = self.values[0]
        cid = ctx.channel.id
        ACTIVE_GAMES[cid] = True

        target_player = random.choice(self.players)
        question = random.choice(QUESTIONS_DATA[level])

        emb = discord.Embed(
            title=f"🎲 │ بداية لعبة الأسئلة والجريئة — [{level.upper()}]",
            description=(
                f"🎲 **جاري تدوير النرد لاختيار الضحية...**\n"
                f"🎯 **الدور الأول على:** {target_player.mention}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❓ **السؤال:**\n`{question}`\n"
                f"⏱️ **سيتغير السؤال واللاعب تلقائياً خلال 15 ثانية!**"
            ),
            color=discord.Color.gold()
        )

        game_view = QuestionsGameView(cid, level, self.players)
        await ctx.response.send_message(embed=emb, view=game_view)
        msg = await ctx.original_response()
        asyncio.create_task(game_view.start_loop(msg))

class SpyGuessSelect(discord.ui.Select):
    def __init__(self, spy_user: discord.User, correct_word: str, words_options: list):
        self.spy_user = spy_user
        self.correct_word = correct_word
        opts = [discord.SelectOption(label=w, value=w) for w in words_options]
        super().__init__(placeholder="🕵️‍♂️ اختر الكلمة التي تعتقد أنها الكلمة السرية...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        if ctx.user.id != self.spy_user.id:
            await ctx.response.send_message("❌ هذا الخيار للجاسوس فقط!", ephemeral=True)
            return

        choice = self.values[0]
        if choice == self.correct_word:
            await ctx.response.send_message(f"🎉 **ذكاء أسطوري!** تمكن الجاسوس {self.spy_user.mention} من تخمين الكلمة الصحيحة **[{self.correct_word}]** وفاز باللعبة! 🕵️‍♂️🔥")
        else:
            await ctx.response.send_message(f"💀 **هزيمة الجاسوس!** خمن الجاسوس {self.spy_user.mention} الكلمة الخاطئة `[{choice}]`!\nالكلمة الصحيحة كانت **[{self.correct_word}]**. انتصر المواطنون! 🏰")

class SpyVoteSelect(discord.ui.Select):
    def __init__(self, players: list, spy_user: discord.User, correct_word: str, similar_words: list):
        self.players = players
        self.spy_user = spy_user
        self.correct_word = correct_word
        self.similar_words = similar_words
        self.votes = {}

        opts = [discord.SelectOption(label=p.display_name, value=str(p.id), emoji="👤") for p in players]
        super().__init__(placeholder="🗳️ صوّت للشخص المشتبه به كجاسوس...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        voter_id = str(ctx.user.id)
        target_id = self.values[0]
        self.votes[voter_id] = target_id

        await ctx.response.send_message(f"✅ تم تسجيل تصويتك ضد <@{target_id}>!", ephemeral=True)

        if len(self.votes) >= len(self.players):
            counts = {}
            for t in self.votes.values():
                counts[t] = counts.get(t, 0) + 1
            most_voted_id = max(counts, key=counts.get)

            if most_voted_id == str(self.spy_user.id):
                emb_spy = discord.Embed(
                    title="🕵️‍♂️ │ كشف الجاسوس!",
                    description=(
                        f"🎯 **نجح المواطنون في كشف الجاسوس الحقيقي {self.spy_user.mention}!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"❓ **الفرصة الأخيرة للجاسوس:** اختر الكلمة السرية الصحيحة من المنيو بالأسفل لتنقذ نفسك وتفوز!"
                    ),
                    color=discord.Color.red()
                )
                words_opts = self.similar_words.copy()
                if self.correct_word not in words_opts:
                    words_opts[0] = self.correct_word
                random.shuffle(words_opts)

                vw = discord.ui.View()
                vw.add_item(SpyGuessSelect(self.spy_user, self.correct_word, words_opts))
                await ctx.channel.send(embed=emb_spy, view=vw)
            else:
                await ctx.channel.send(f"💀 **خطأ قاتل!** تم طرد المقاتل البريء <@{most_voted_id}>!\n🎉 **فاز الجاسوس المخادع {self.spy_user.mention} بالمعركة!** الكلمة كانت: `[{self.correct_word}]`")

class CutTweetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.agree = 0
        self.disagree = 0

    @discord.ui.button(label="👍 مـع", style=discord.ButtonStyle.success)
    async def agree_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        self.agree += 1
        tot = self.agree + self.disagree
        await ctx.response.send_message(f"✅ تصويتك: **مـع**! (النسبة: `{int(self.agree/tot*100)}%` مـع | `{int(self.disagree/tot*100)}%` ضـد)", ephemeral=True)

    @discord.ui.button(label="👎 ضـد", style=discord.ButtonStyle.danger)
    async def disagree_btn(self, ctx: discord.Interaction, button: discord.ui.Button):
        self.disagree += 1
        tot = self.agree + self.disagree
        await ctx.response.send_message(f"❌ تصويتك: **ضـد**! (النسبة: `{int(self.agree/tot*100)}%` مـع | `{int(self.disagree/tot*100)}%` ضـد)", ephemeral=True)

class MainGamesSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="لعبة الأسئلة والجريئة", value="q_game", emoji="🎲", description="3 مستويات + 50 سؤال وعقاب لكل مستوى"),
            discord.SelectOption(label="لعبة الألغاز", value="riddle_game", emoji="🧩", description="150 لغز متدرج الصعوبة (تلقائي)"),
            discord.SelectOption(label="لعبة الجواسيس (Spyfall)", value="spy_game", emoji="🕵️‍♂️", description="3+ لاعبين + تصويت وتخمين"),
            discord.SelectOption(label="لعبة الرياضيات", value="math_game", emoji="🧮", description="معادلات سريعة ومؤقت 15 ثانية (تلقائي)"),
            discord.SelectOption(label="لعبة خمن الأنمي", value="anime_game", emoji="🎌", description="أنميات متنوعة كلاسيكية وحديثة (تلقائي)"),
            discord.SelectOption(label="لعبة كت تويت", value="cut_tweet", emoji="💬", description="تغريدات ونقاشات مع أم ضد"),
            discord.SelectOption(label="لعبة فكّك", value="deconstruct", emoji="🔤", description="تفكيك الكلمات بالحروف ومؤقت 15s (تلقائي)"),
            discord.SelectOption(label="لعبة أسرع", value="fastest", emoji="⚡", description="كتابة الكلمات السريعة بالعربية (تلقائي)")
        ]
        super().__init__(placeholder="🎮 اختر اللعبة المطلوبة لبدء المرح...", options=opts)

    async def callback(self, ctx: discord.Interaction):
        v = self.values[0]
        cid = ctx.channel.id

        if v == "q_game":
            players = [m for m in ctx.channel.members if not m.bot]
            if len(players) < 2:
                await ctx.response.send_message("❌ هذه اللعبة تتطلب وجود **لاعبين اثنين (2) على الأقل** في الروم!", ephemeral=True)
                return
            vw = discord.ui.View()
            vw.add_item(QuestionsLevelSelect(players))
            await ctx.response.send_message("🎲 اختر مستوى صراحة الأسئلة للبدء:", view=vw)

        elif v == "riddle_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة الألغاز التلقائية!** ستستمر الأسئلة تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                riddle, ans = random.choice(RIDDLES)
                emb = discord.Embed(
                    title="🧩 │ لعبة الألغاز الإمبراطورية",
                    description=f"❓ **اللغز:**\n`{riddle}`\n\n💡 اكتب الإجابة الصحيحة في الشات فوراً!",
                    color=discord.Color.green()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and ans in m.content.strip()

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=30.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "riddles")
                    await ctx.channel.send(f"🎉 **تهنئة ملكية!** إجابة صحيحة يا بطل {winner_msg.author.mention}! 🏆 الإجابة هي: **[{ans}]**")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** لم يتمكن أحد من حل اللغز. الإجابة الصحيحة كانت: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "spy_game":
            players = [m for m in ctx.channel.members if not m.bot][:6]
            if len(players) < 3:
                await ctx.response.send_message("❌ لعبة الجواسيس تتطلب وجود **3 لاعبين على الأقل** في السيرفر/الروم!", ephemeral=True)
                return

            spy = random.choice(players)
            secret_words = ["مستشفى", "مطار", "مدرسة", "قلعة أسطورية", "سفينة قرصان", "مركز شرطة", "مطعم"]
            correct_word = random.choice(secret_words)

            for p in players:
                if p.id == spy.id:
                    try: await p.send("🕵️‍♂️ **أنت الجاسوس!** حاول التمويه واكتشاف الكلمة السرية من تلميحات المواطنين!")
                    except: pass
                else:
                    try: await p.send(f"🤫 **أنت مواطن صالي!** الكلمة السرية هي: **[{correct_word}]**. أعطِ تلميحات ذكية ولا تكشفها للجاسوس!")
                    except: pass

            emb_spy = discord.Embed(
                title="🕵️‍♂️ │ بدأت لعبة الجواسيس (Spyfall)",
                description=(
                    f"👥 **اللاعبون المشاركون:** {', '.join([p.mention for p in players])}\n"
                    f"🤫 تم إرسال الأدور والكلمة السرية في الخاص!\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 ابدأوا في تقديم التلميحات بالروم وصوتوا ضد الجاسوس عبر القائمة بالأسفل:"
                ),
                color=discord.Color.purple()
            )
            vw = discord.ui.View()
            vw.add_item(SpyVoteSelect(players, spy, correct_word, secret_words))
            await ctx.response.send_message(embed=emb_spy, view=vw)

        elif v == "math_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة الرياضيات التلقائية!** ستستمر المعادلات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                eq, ans = random.choice(MATH_EQUATIONS)
                emb = discord.Embed(
                    title="🧮 │ لعبة الرياضيات والسرعة",
                    description=f"⚡ **احسب الناتج بسرعة خلال 15 ثانية:**\n`{eq} = ؟`",
                    color=discord.Color.blue()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == ans

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "math")
                    await ctx.channel.send(f"🎉 **سرعة أسطورية!** {winner_msg.author.mention} حل المعادلة الصحيحة **[{ans}]** بنجاح! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **خسرتم الوقت!** انتهت الـ 15 ثانية بدون إجابة. الناتج الصحيح كان: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "anime_game":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة خمن الأنمي التلقائية!** ستستمر الأنميات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                hint, valid_answers = random.choice(ANIME_DATA)
                emb = discord.Embed(
                    title="🎌 │ لعبة خمن الأنمي",
                    description=f"💡 **التلميح:**\n`{hint}`\n\n⏱️ **معكم 25 ثانية فقط لمعرفة اسم الأنمي!**",
                    color=discord.Color.gold()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    if m.channel.id != cid or m.author.bot:
                        return False
                    user_ans = m.content.strip().lower()
                    return any(ans.lower() in user_ans for ans in valid_answers)

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=25.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "anime")
                    await ctx.channel.send(f"🎉 **أوتاكو أسطوري!** {winner_msg.author.mention} عرف الأنمي الصحيح **[{valid_answers[0]}]** بنجاح! 👑")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** اسم الأنمي الصحيح كان: **[{valid_answers[0]}]**")

                await asyncio.sleep(2.5)

        elif v == "cut_tweet":
            tweet = random.choice(CUT_TWEETS)
            emb = discord.Embed(
                title="💬 │ كت تويت (Cut Tweet)",
                description=f"📜 **المقولة/النقاش:**\n`{tweet}`\n━━━━━━━━━━━━━━━━━━━━\nهل أنت **مع أم ضد** القول أعلاه؟",
                color=discord.Color.teal()
            )
            await ctx.response.send_message(embed=emb, view=CutTweetView())

        elif v == "deconstruct":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة فكّك الكلمات التلقائية!** ستستمر الكلمات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                word, ans = random.choice(DECONSTRUCT_WORDS)
                emb = discord.Embed(
                    title="🔤 │ لعبة فكّك الكلمات",
                    description=f"🎯 **فكّك الكلمة التالية بحروف بينها مسافات خلال 15 ثانية:**\n`[{word}]`",
                    color=discord.Color.orange()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == ans

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "deconstruct")
                    await ctx.channel.send(f"🎉 **إجابة رائعة!** {winner_msg.author.mention} فكك الكلمة بشكل صحيح **[{ans}]**! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهت الـ 15 ثانية!** التفكيك الصحيح كان: **[{ans}]**")

                await asyncio.sleep(2.5)

        elif v == "fastest":
            if ACTIVE_GAMES.get(cid, False):
                await ctx.response.send_message("⚠️ هناك لعبة جارية بالفعل في هذه القناة! أوقفها أولاً.", ephemeral=True)
                return

            ACTIVE_GAMES[cid] = True
            await ctx.response.send_message("🚀 **بدأت لعبة أسرع كتابة التلقائية!** ستستمر الكلمات تلقائياً حتى ضغط زر الإيقاف.")

            while ACTIVE_GAMES.get(cid, False):
                word = random.choice(FASTEST_WORDS)
                emb = discord.Embed(
                    title="⚡ │ لعبة أسرع كتابة",
                    description=f"🚀 **اكتب الكلمة التالية بسرعة وطابقها بالضبط خلال 15 ثانية:**\n`{word}`",
                    color=discord.Color.magenta()
                )
                await ctx.channel.send(embed=emb, view=StopGameView(cid))

                def check(m):
                    return m.channel.id == cid and not m.author.bot and m.content.strip() == word

                try:
                    winner_msg = await bot.wait_for('message', check=check, timeout=15.0)
                    if not ACTIVE_GAMES.get(cid, False): break
                    add_game_win(winner_msg.author.id, "fastest")
                    await ctx.channel.send(f"⚡ **سرعة خارقة!** {winner_msg.author.mention} كتب الكلمة أولاً خلال الثواني الأسرع! 🏆")
                except asyncio.TimeoutError:
                    if not ACTIVE_GAMES.get(cid, False): break
                    await ctx.channel.send(f"⌛ **انتهى الوقت!** لم يكتب أحد الكلمة المطابقة `{word}` في الـ 15 ثانية.")

                await asyncio.sleep(2.5)

class MainGamesView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(MainGamesSelect())

# ==================== الأوامر والتسجيل ====================

@bot.tree.command(name="الالعاب", description="🎮 مركز وقاعة الألعاب الإمبراطورية الملكية الـ 8")
async def games_hub_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    emb = discord.Embed(
        title="🎮 │ صالة الألعاب الإمبراطورية العظمى — IMPERIAL GAMES",
        description=(
            "مرحباً بك يا صاحب السعادة في مجمع الترفيه والتحديات الممتعة!\n"
            "اختر اللعبة المناسبة لك ولأصدقائك من القائمة بالأسفل وباشر بالقتال والتحدي:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎲 **الأسئلة والجريئة** │ 🧩 **الألغاز** │ 🕵️‍♂️ **الجواسيس**\n"
            "🧮 **الرياضيات** │ 🎌 **خمن الأنمي** │ 💬 **كت تويت**\n"
            "🔤 **فكّك** │ ⚡ **أسرع**"
        ),
        color=discord.Color.gold()
    )
    emb.set_thumbnail(url=ctx.user.display_avatar.url)
    emb.set_footer(text="👑 استمتع بالتحديات المباشرة واكسب نقاط الليدربورد!")
    await ctx.response.send_message(embed=emb, view=MainGamesView())

@bot.tree.command(name="ليدربورد_الالعاب", description="🏆 عرض أبطال ومتصدري الألعاب في السيرفر")
async def games_leaderboard_command(ctx: discord.Interaction):
    if not is_user_registered(ctx.user.id):
        await ctx.response.send_message("❌ سجل أولاً عبر `/تسجيل`!", ephemeral=True)
        return

    emb = discord.Embed(title="🏆 قاعة العظماء للألعاب — اختر تصنيف اللعبة من القائمة بالأسفل", color=discord.Color.gold())
    vw = discord.ui.View()
    vw.add_item(GamesLeaderboardSelect())
    await ctx.response.send_message(embed=emb, view=vw)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✨ تم مزامنة البوت بنجاح! يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ المزامنة: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
