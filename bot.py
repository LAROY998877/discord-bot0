# ================== 🏰 8. نظام أبطال الإمبراطورية (فانتازي) ==================

HEROES_DATA = {
    "male": [
        {
            "id": "m1",
            "name": "فاليريون — فارس التنين الخالد",
            "emoji": "🐉",
            "story": "وُلد من قلب بركان محترق وتمتع بدم التنانين القديمة. يحمل سيفاً مصقولاً بنار التنين الأسطورية التي لا تنطفئ أبداً، ويخوض المعارك بلا رحمة.",
            "power": 12500,
            "stats": {"الهجوم": 95, "الدفاع": 90, "السحر": 70, "السرعة": 80, "ضربة قاتلة": 85}
        },
        {
            "id": "m2",
            "name": "كاليان — شبح الظلال السري",
            "emoji": "🗡️",
            "story": "سياف خفي يمتلك قدرة التنقل عبر الأبعاد والذوبان في الظلال. ضرباته خاطفة ولا تترك أثراً، ويهابه أعتى ملوك البرج.",
            "power": 11800,
            "stats": {"الهجوم": 98, "الدفاع": 50, "السحر": 65, "السرعة": 100, "ضربة قاتلة": 99}
        },
        {
            "id": "m3",
            "name": "إغنيس — أمير اللهب الأبدي",
            "emoji": "🔥",
            "story": "ساحر قديم يسيطر على ألسنة الجحيم النارية. أحرق جيوشاً كاملة بكلمة واحدة من تعاويذه المحرمة وشكل إمبراطورية من رماد أعدائه.",
            "power": 13000,
            "stats": {"الهجوم": 100, "الدفاع": 60, "السحر": 100, "السرعة": 75, "ضربة قاتلة": 90}
        },
        {
            "id": "m4",
            "name": "أوريون — حارس الغابات الأسطوري",
            "emoji": "🏹",
            "story": "رامٍ استثنائي تستجيب لنقرات قوسه الوحوش الضارية. أسهمه السحرية لا تخطئ هدفها حتى لو كانت مخفية بين غيوم السماء.",
            "power": 11200,
            "stats": {"الهجوم": 92, "الدفاع": 65, "السحر": 60, "السرعة": 95, "ضربة قاتلة": 92}
        },
        {
            "id": "m5",
            "name": "مالاكاي — ملك الأرواح المستدعاة",
            "emoji": "💀",
            "story": "حكيم سحري استطاع كسر حدود الموت، يستدعي جيوشاً من الفرسان العظميين لحمايته وتدمير كل من يتجرأ على الاعتداء على عرشه.",
            "power": 14000,
            "stats": {"الهجوم": 85, "الدفاع": 75, "السحر": 100, "السرعة": 60, "ضربة قاتلة": 80}
        }
    ],
    "female": [
        {
            "id": "f1",
            "name": "أليستريا — قدسية الضوء السماوي",
            "emoji": "✨",
            "story": "كاهنة نادرة تمتلك هالة شفائية قدسية تبدد الظلمات وتبطل السحر الأسود بلمسة واحدة، وتملك حماية ملائكية تجعلها صلبة في القتال.",
            "power": 12000,
            "stats": {"الهجوم": 70, "الدفاع": 85, "السحر": 98, "السرعة": 85, "ضربة قاتلة": 75}
        },
        {
            "id": "f2",
            "name": "سيرابينا — ملكة العواصف والرعد",
            "emoji": "⚡",
            "story": "ولدت في قلب إعصار مدمر واستوعبت طاقة الصواعق السماوية. تستدعي البرق لتشطير الجبال وإبادة أعتى الوحوش في ثوانٍ.",
            "power": 13500,
            "stats": {"الهجوم": 98, "الدفاع": 65, "السحر": 99, "السرعة": 90, "ضربة قاتلة": 95}
        },
        {
            "id": "f3",
            "name": "ليثيا — صيادة القمر المظلم",
            "emoji": "🌙",
            "story": "محاربة غامضة تتضاعف قوتها القتالية عند اكتمال القمر. تستخدم قوساً فضياً مصنوعاً من شظايا النجوم وتسدد ضربات قاضية في ظلام الليل.",
            "power": 11900,
            "stats": {"الهجوم": 94, "الدفاع": 60, "السحر": 75, "السرعة": 98, "ضربة قاتلة": 96}
        },
        {
            "id": "f4",
            "name": "فالينتيا — الفالكيري الحديدية",
            "emoji": "🛡️",
            "story": "قائدة الجيوش الملكية وحاملة الدرع الأسطوري المصنوع من الماجما. تقف في الخطوط الأمامية وتستقبل أعتى الضربات دون أن تتزحزح خطوة.",
            "power": 12800,
            "stats": {"الهجوم": 88, "الدفاع": 100, "السحر": 50, "السرعة": 70, "ضربة قاتلة": 80}
        },
        {
            "id": "f5",
            "name": "مورغانا — سيدة الفراغ المحرم",
            "emoji": "🔮",
            "story": "ساحر غامضة تتقن سحر الأبعاد والفراغ. قادرة على ابتلاع هجمات الخصوم وحبس الأعداء داخل ثقوب سوداء سحرية لا مخرج منها.",
            "power": 13800,
            "stats": {"الهجوم": 96, "الدفاع": 70, "السحر": 100, "السرعة": 80, "ضربة قاتلة": 88}
        }
    ]
}

class SpecificHeroSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        heroes = HEROES_DATA[category]
        options = [
            discord.SelectOption(
                label=h["name"],
                value=h["id"],
                description=f"القوة: {h['power']:,} ⚡ | اضغط لرؤية التفاصيل",
                emoji=h["emoji"]
            ) for h in heroes
        ]
        placeholder = "⚔️ اختر بطلاً من فرسان الظلال والنور..." if category == "male" else "🔮 اختر بطلة من سيدات السحر والحرب..."
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        hero_id = self.values[0]
        hero = next(h for h in HEROES_DATA[self.category] if h["id"] == hero_id)
        
        stats_text = "\n".join([f"• **{stat}:** `{val}`" for stat, val in hero["stats"].items()])
        
        embed = discord.Embed(
            title=f"{hero['emoji']} {hero['name']}",
            description=f"📜 **القصة والأسطورة:**\n*{hero['story']}*\n\n"
                        f"⚡ **القوة القتالية الأساسية:** `{hero['power']:,}`\n\n"
                        f"📊 **المعدلات والخصائص:**\n{stats_text}",
            color=discord.Color.gold() if self.category == "male" else discord.Color.purple()
        )
        embed.set_footer(text="🏰 قاعة عظماء إمبراطورية الفانتازيا")
        
        view = discord.ui.View()
        view.add_item(HeroCategorySelect())
        view.add_item(SpecificHeroSelect(self.category))
        
        await interaction.response.edit_message(embed=embed, view=view)

class HeroCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الأبطال الذكور (5 فرسان)", value="male", description="استعراض أعتى الفرسان والسحرة الذكور", emoji="⚔️"),
            discord.SelectOption(label="الأبطال الإناث (5 سيدات)", value="female", description="استعراض سيدات الحرب والسحر الملكيات", emoji="🔮")
        ]
        super().__init__(placeholder="👑 اختر فئة الأبطال للاستعراض...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        view = discord.ui.View()
        view.add_item(HeroCategorySelect())
        view.add_item(SpecificHeroSelect(category))
        
        title_text = "⚔️ قاعة الأبطال الذكور — فرسان الإمبراطورية" if category == "male" else "🔮 قاعة الأبطال الإناث — سيدات الحرب والسحر"
        embed = discord.Embed(
            title=title_text,
            description="اختر البطـل من القائمة المنسدلة الثانية لعرض **القصة والأسطورة** وكامل **المعدلات القتالية**!",
            color=discord.Color.blue() if category == "male" else discord.Color.magenta()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class HeroesHubView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HeroCategorySelect())

@bot.tree.command(name="الابطال", description="🏰 استعراض أبطال الإمبراطورية الأساطير (5 ذكور و 5 إناث)")
async def heroes_command(interaction: discord.Interaction):
    if not is_user_registered(interaction.user.id):
        return await interaction.response.send_message("❌ يجب التسجيل أولاً عبر أمر `/تسجيل`!", ephemeral=True)

    embed = discord.Embed(
        title="🏛️ قاعة أساطير الإمبراطورية — Heroes Sanctuary",
        description="أهلاً بك في قاعة الأبطال الأساطير!\n\n"
                    "• ⚔️ **5 أبطال ذكور:** يمثلون القوة الساحقة، التنانين والظلال.\n"
                    "• 🔮 **5 أبطال إناث:** يمثلن سحر الفراغ، العواصف، والضوء السماوي.\n\n"
                    "اختر الفئة التي تريد استعراضها من القائمة أسفله:",
        color=discord.Color.dark_gold()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, view=HeroesHubView(), ephemeral=False)
