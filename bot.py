# ================== نظام اختيار الأبطال الأسطوريين ==================

# قاعدة بيانات الأبطال (القصة والقوة والتفاصيل)
HEROES_DATA = {
    "zeal": {
        "name": "زيل - كاسر الظلال (Zeal)",
        "gender": "ذكر",
        "emoji": "⚡",
        "power": "سرعة البرق الخاطفة والتحكم في طاقة البلازما المدمرة",
        "story": "محارب وُلِد في قلب العواصف الرعدية الكونية. استطاع دمج روحه بطاقة البرق، ليصبح شبحاً لا يطال، يظهر ويهزم أعداءه قبل أن ترمش أعينهم."
    },
    "draven": {
        "name": "دريفان - سيد الجحيم (Draven)",
        "gender": "ذكر",
        "emoji": "🔥",
        "power": "استدعاء نيران التنانين الأسطورية وتصلب الجلد البركاني",
        "story": "قائد عسكري سابق لجيوش الحمم المظلمة. بعد خيانة إمبراطوريته، عاهد نفسه على حرق كل ظالم بسيفه المصنوع من صهارة النجوم الملتهبة."
    },
    "kaelen": {
        "name": "كايلين - حارس الأبعاد (Kaelen)",
        "gender": "ذكر",
        "emoji": "🌌",
        "power": "التلاعب بالزمن والقدرة على فتح ثواني للقفز بين الأبعاد",
        "story": "حكيم كوني أمضى آلاف السنين يدرس أسرار الكون والفضاء السحيق. يستطيع إبطاء الزمن حول أعدائه وجعل ضرباتهم تمر عبر جسده كأنها هواء."
    },
    "lyra": {
        "name": "ليرا - ملكة الصقيع (Lyra)",
        "gender": "أنثى",
        "emoji": "❄️",
        "power": "تجميد جزيئات الهواء المطلق وصنع أسلحة من الجليد الصلب",
        "story": "أميرة قطبية أُمطرت مدينتها بلعنة النار الأبدية، فتحولت إلى عاصفة حية لا تقهر، تنشر البرد القارس لتجميد قلوب وجيوش الطغاة."
    },
    "vortexa": {
        "name": "فورتيكسا - ساحرة الثقوب السوداء (Vortexa)",
        "gender": "أنثى",
        "emoji": "🌀",
        "power": "امتصاص ضربات الخصوم وإطلاقها كطاقة جاذبية مميتة",
        "story": "مقاتلة استثنائية استدمجت طاقة الثقوب السوداء في جسدها. تستطيع جذب أي عدو إليها وسحقه بقوة جاذبية تفوق تخриل البشر."
    },
    "valeria": {
        "name": "فاليريا - فارسة الفجر الذهبي (Valeria)",
        "gender": "أنثى",
        "emoji": "☀️",
        "power": "الشفاء السريع، القوة البدنية المطلقة، وهالة النور المقدس",
        "story": "قائدة حرس الفجر الأسطوريون. تحمل درعاً مقدساً لا ينكسر وسيفاً يضيء بنور الشمس الأولى، تطهر الأراضي من الوحوش والظلام."
    }
}

class HeroSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=data["name"], description=f"المجال: {data['gender']} | القوة: {data['power'][:40]}...", emoji=data["emoji"], value=key)
            for key, data in HEROES_DATA.items()
        ]
        super().__init__(placeholder="اختر بطلك الأسطوري لتستعرض قصته وقوته...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        hero_key = self.values[0]
        hero = HEROES_DATA[hero_key]
        
        embed = discord.Embed(
            title=f"{hero['emoji']} تفاصيل البطل الأسطوري: {hero['name']}",
            description=f"**الجنس:** `{hero['gender']}`\n\n🛡️ **القدرة الخارقة:**\n{hero['power']}\n\n📜 **القصة الملحمية:**\n*{hero['story']}*",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        embed.set_footer(text=f"تم اختيار البطل بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        # يمكنك هنا حفظ البطل المختار في قاعدة البيانات إذا أردت ربطه بملفه الشخصي
        users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"selected_hero": hero['name']}}, upsert=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HeroSelect())

@bot.tree.command(name="أبطال", description="استعراض قائمة الأبطال الأسطوريين واختيار بطلك المفضل لرحلة القتال")
async def heroes_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة اختيار الأبطال الأسطوريين 🛡️",
        description="«اختر بطلك بحكمة، فالقصة والقوة التي ستختارها سترافقك في جميع المعارك والأبراج القتالية القادمة.»\n\nاختر من القائمة المنسدلة أدناه لاستعراض تفاصيل أي بطل:",
        color=discord.Color.gold()
    )
    view = HeroSelectView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
