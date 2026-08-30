import os
import random
import re
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# ==========================================
# إعداد البوت
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://botuser:bot12345@laroy998877.makaovo.mongodb.net/discord_bot_db?retryWrites=true&w=majority&authSource=admin"
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
# نظام المتاجر
# ==========================================
class ShopPaginationView(discord.ui.View):
    def __init__(self, user_id, shop_type, category, page=0):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.shop_type = shop_type
        self.category = category
        self.page = page

        items_source = NORMAL_SHOP_ITEMS if shop_type == "normal" else DARK_SHOP_ITEMS
        self.items = items_source.get(category, [])
        self.total_pages = (len(self.items) + 24) // 25

        self.update_components()

    def build_embed(self):
        title_text = "المتجر العادي" if self.shop_type == "normal" else "متجر الظلام"
        color = 0x3498db if self.shop_type == "normal" else 0x111111

        embed = discord.Embed(
            title=f"🛒 {title_text} - قسم ({self.category})",
            description=(
                f"استعرض العتاد الفانتازي "
                f"(صفحة {self.page + 1} من {self.total_pages}):"
            ),
            color=color
        )

        return embed

    def update_components(self):
        self.clear_items()

        start_idx = self.page * 25
        end_idx = min(start_idx + 25, len(self.items))
        current_items = self.items[start_idx:end_idx]

        select = discord.ui.Select(
            placeholder=f"اختر قطعة (صفحة {self.page + 1}/{self.total_pages})...",
            min_values=1,
            max_values=1
        )

        emoji_map_normal = {
            "شائع": "⚪",
            "نادر": "🟢",
            "ملحمي": "🟣",
            "أسطوري": "🟡",
            "فريد": "🟠",
            "مقدس": "✨"
        }

        emoji_map_dark = {
            "شائع": "⚪",
            "نادر": "🟢",
            "ملحمي": "🔵",
            "أسطوري": "🟣",
            "السفاح": "🗡️",
            "الجحيم": "🔥",
            "الشيطان": "👑"
        }

        e_map = emoji_map_normal if self.shop_type == "normal" else emoji_map_dark

        for item in current_items:
            emo = e_map.get(item["tier"], "⚔️")
            currency_name = "عملة" if self.shop_type == "normal" else "ألماس"

            select.add_option(
                label=item["name"][:100],
                description=(
                    f"الرتبة: {item['tier']} | "
                    f"قوة: +{item['power']} | "
                    f"السعر: {item['price']} {currency_name}"
                ),
                emoji=emo,
                value=item["id"]
            )

        select.callback = self.select_callback
        self.add_item(select)

        if self.total_pages > 1:
            prev_btn = discord.ui.Button(
                label="⬅️ السابقة",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page == 0)
            )
            prev_btn.callback = self.prev_page_callback
            self.add_item(prev_btn)

            next_btn = discord.ui.Button(
                label="التالية ➡️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page >= self.total_pages - 1)
            )
            next_btn.callback = self.next_page_callback
            self.add_item(next_btn)

    async def prev_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return

        if self.page > 0:
            self.page -= 1
            self.update_components()

            await interaction.response.edit_message(
                embed=self.build_embed(),
                view=self
            )

    async def next_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return

        if self.page < self.total_pages - 1:
            self.page += 1
            self.update_components()

            await interaction.response.edit_message(
                embed=self.build_embed(),
                view=self
            )

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return

        selected_id = interaction.data["values"][0]
        chosen_item = None

        items_source = NORMAL_SHOP_ITEMS if self.shop_type == "normal" else DARK_SHOP_ITEMS

        for items in items_source.values():
            for it in items:
                if it["id"] == selected_id:
                    chosen_item = it
                    break
            if chosen_item:
                break

        if not chosen_item:
            await interaction.response.send_message(
                "❌ القطعة غير موجودة!",
                ephemeral=True
            )
            return

        user_id_str = str(interaction.user.id)
        user = users_col.find_one({"user_id": user_id_str})

        if not user:
            await interaction.response.send_message(
                "❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`",
                ephemeral=True
            )
            return

        price = chosen_item["price"]
        inventory = user.get("inventory", [])

        if self.shop_type == "normal":
            balance = user.get("balance", 0)

            if balance < price:
                await interaction.response.send_message(
                    f"❌ رصيدك غير كافي! تحتاج إلى {price} عملة "
                    f"بينما رصيدك هو {balance} عملة.",
                    ephemeral=True
                )
                return

            new_balance = balance - price
            inventory.append(
                f"{chosen_item['name']} (قوة: +{chosen_item['power']})"
            )

            users_col.update_one(
                {"user_id": user_id_str},
                {
                    "$set": {
                        "balance": new_balance,
                        "inventory": inventory
                    }
                }
            )

            embed = discord.Embed(
                title="🛒 تم الشراء بنجاح من المتجر العادي!",
                description=(
                    f"لقد قمت بشراء **{chosen_item['name']}**!\n\n"
                    f"🛡️ **الرتبة:** {chosen_item['tier']}\n"
                    f"⚡ **القوة:** +{chosen_item['power']}\n"
                    f"💰 **السعر:** {price} عملة\n"
                    f"💰 **رصيدك المتبقي:** {new_balance} عملة"
                ),
                color=0x2ecc71
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        else:
            diamonds = user.get("diamonds", 0)

            if diamonds < price:
                await interaction.response.send_message(
                    f"❌ رصيدك من الألماس غير كافي! تحتاج إلى {price} ألماسة "
                    f"بينما رصيدك هو {diamonds} ألماسة.",
                    ephemeral=True
                )
                return

            new_diamonds = diamonds - price
            inventory.append(
                f"{chosen_item['name']} (قوة: +{chosen_item['power']})"
            )

            users_col.update_one(
                {"user_id": user_id_str},
                {
                    "$set": {
                        "diamonds": new_diamonds,
                        "inventory": inventory
                    }
                }
            )

            embed = discord.Embed(
                title="🛒 تم الشراء بنجاح من متجر الظلام!",
                description=(
                    f"لقد قمت بشراء **{chosen_item['name']}**!\n\n"
                    f"👑 **الرتبة:** {chosen_item['tier']}\n"
                    f"⚡ **القوة:** +{chosen_item['power']}\n"
                    f"💎 **السعر:** {price} ألماسة\n"
                    f"💎 **رصيدك المتبقي:** {new_diamonds} ألماسة"
                ),
                color=0x111111
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )


class NormalShopCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر قسماً من أقسام المتجر العادي...",
        options=[
            discord.SelectOption(label="خناجر", description="500 قطعة عتاد فانتازي", emoji="🗡️"),
            discord.SelectOption(label="سيوف", description="500 قطعة عتاد فانتازي", emoji="⚔️"),
            discord.SelectOption(label="مطرقات", description="500 قطعة عتاد فانتازي", emoji="🔨"),
            discord.SelectOption(label="خوذ", description="500 قطعة عتاد فانتازي", emoji="🪖"),
            discord.SelectOption(label="دروع", description="500 قطعة عتاد فانتازي", emoji="🛡️"),
            discord.SelectOption(label="ساق", description="500 قطعة عتاد فانتازي", emoji="🦵"),
            discord.SelectOption(label="حذاء", description="500 قطعة عتاد فانتازي", emoji="👢")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat = select.values[0]

        embed = discord.Embed(
            title=f"🛒 المتجر العادي - قسم ({cat})",
            description=(
                f"استعرض عتاد قسم **{cat}** الفانتازي "
                f"(متاح 500 قطعة بتدرج رتب وقوة مناسبة):"
            ),
            color=0x3498db
        )
        await interaction.response.send_message(
            embed=embed,
            view=ShopPaginationView(
                interaction.user.id,
                "normal",
                cat,
                page=0
            ),
            ephemeral=True
        )


class DarkShopCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر قسماً من أقسام متجر الظلام...",
        options=[
            discord.SelectOption(label="خناجر", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="🗡️"),
            discord.SelectOption(label="سيوف", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="⚔️"),
            discord.SelectOption(label="مطرقات", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="🔨"),
            discord.SelectOption(label="خوذ", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="🪖"),
            discord.SelectOption(label="دروع", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="🛡️"),
            discord.SelectOption(label="ساق", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="🦵"),
            discord.SelectOption(label="حذاء", description="500 قطعة عتاد مظلم (يعمل بالألماس)", emoji="👢")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat = select.values[0]

        embed = discord.Embed(
            title=f"🌑 متجر الظلام - قسم ({cat})",
            description=(
                f"استعرض عتاد قسم **{cat}** المظلم "
                f"(500 قطعة | أعلى ثلاث رتب: السفاح، الجحيم، الشيطان | "
                f"العملة: الألماس):"
            ),
            color=0x111111
        )
        await interaction.response.send_message(
            embed=embed,
            view=ShopPaginationView(
                interaction.user.id,
                "dark",
                cat,
                page=0
            ),
            ephemeral=True
        )


# ==========================================
# كلاسات اللعبة التفاعلية
# ==========================================
class ActiveQuestionsGame(discord.ui.View):
    def __init__(self, players, questions_list, level_name):
        super().__init__(timeout=None)
        self.players = players
        self.questions_list = questions_list
        self.level_name = level_name
        self.current_turn = 0

    @discord.ui.button(
        label="السؤال التالي 🎲",
        style=discord.ButtonStyle.primary,
        custom_id="next_q_btn"
    )
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message(
                "❌ أنت لست مشاركاً في هذه اللعبة النشطة!",
                ephemeral=True
            )
            return

        self.current_turn = (self.current_turn + 1) % len(self.players)
        current_player = self.players[self.current_turn]
        question = random.choice(self.questions_list)

        embed = discord.Embed(
            title=f"🎯 لعبة الأسئلة والصراحة - مستوى ({self.level_name})",
            description=(
                f"👤 **الدور الآن على:** {current_player.mention}\n\n"
                f"💬 **السؤال:**\n`{question}`"
            ),
            color=0xe74c3c
        )
        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="إيقاف اللعبة 🛑",
        style=discord.ButtonStyle.danger,
        custom_id="stop_q_btn"
    )
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message(
                "❌ المشاركون فقط في اللعبة يمكنهم إيقافها!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🛑 تم إيقاف اللعبة",
            description=(
                f"تم إنهاء جلسة اللعب بواسطة {interaction.user.mention}.\n"
                f"شكراً لكل من شارك وتفاعل!"
            ),
            color=0x2c3e50
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


class GameLobby(discord.ui.View):
    def __init__(self, host, questions_list, level_name):
        super().__init__(timeout=None)
        self.host = host
        self.questions_list = questions_list
        self.level_name = level_name
        self.players = [host]

    def generate_embed(self):
        players_mentions = "\n".join(
            [f"👤 {p.mention}" for p in self.players]
        )

        return discord.Embed(
            title=f"⏳ غرفة انتظار لعبة الأسئلة ({self.level_name})",
            description=(
                f"المستضيف: {self.host.mention}\n\n"
                f"**اللاعبون المنضمون ({len(self.players)}):**\n"
                f"{players_mentions}\n\n"
                f"*(الحد الأدنى للبدء: لاعبان فأكثر)*"
            ),
            color=0x3498db
        )

    @discord.ui.button(
        label="مشاركة ✋",
        style=discord.ButtonStyle.success,
        custom_id="join_lobby_btn"
    )
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message(
                "❌ أنت منضم بالفعل في هذه الغرفة!",
                ephemeral=True
            )
            return

        self.players.append(interaction.user)
        await interaction.response.edit_message(
            embed=self.generate_embed(),
            view=self
        )

    @discord.ui.button(
        label="بدء اللعبة ▶️",
        style=discord.ButtonStyle.primary,
        custom_id="start_lobby_btn"
    )
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message(
                "❌ المستضيف وحده هو من يمكنه بدء اللعبة!",
                ephemeral=True
            )
            return

        if len(self.players) < 2:
            await interaction.response.send_message(
                "❌ يجب أن يكون هناك لاعبان على الأقل في الغرفة لبدء اللعبة!",
                ephemeral=True
            )
            return

        question = random.choice(self.questions_list)
        first_player = self.players[0]

        embed = discord.Embed(
            title=f"🎯 بدأت اللعبة - مستوى ({self.level_name})",
            description=(
                f"👤 **الدور الأول على:** {first_player.mention}\n\n"
                f"💬 **السؤال:**\n`{question}`"
            ),
            color=0xe74c3c
        )

        active_view = ActiveQuestionsGame(
            self.players,
            self.questions_list,
            self.level_name
        )

        await interaction.response.edit_message(
            embed=embed,
            view=active_view
        )


class DifficultySelection(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=None)
        self.host = host

    @discord.ui.button(
        label="عادي 🟢",
        style=discord.ButtonStyle.success
    )
    async def normal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return

        lobby = GameLobby(
            self.host,
            NORMAL_QUESTIONS,
            "عادي"
        )

        await interaction.channel.send(
            embed=lobby.generate_embed(),
            view=lobby
        )

        await interaction.response.edit_message(
            content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!",
            embed=None,
            view=None
        )

    @discord.ui.button(
        label="متوسط 🟡",
        style=discord.ButtonStyle.secondary
    )
    async def medium_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return

        lobby = GameLobby(
            self.host,
            MEDIUM_QUESTIONS,
            "متوسط"
        )

        await interaction.channel.send(
            embed=lobby.generate_embed(),
            view=lobby
        )

        await interaction.response.edit_message(
            content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!",
            embed=None,
            view=None
        )

    @discord.ui.button(
        label="جريء جداً وخصوصي 🔥",
        style=discord.ButtonStyle.danger
    )
    async def bold_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return

        lobby = GameLobby(
            self.host,
            BOLD_QUESTIONS,
            "جريء جداً وخصوصي"
        )

        await interaction.channel.send(
            embed=lobby.generate_embed(),
            view=lobby
        )

        await interaction.response.edit_message(
            content="✅ تم إنشاء غرفة اللعبة في الشات العام بنجاح!",
            embed=None,
            view=None
        )


class GamesMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر لعبة من المنيو لتشغيلها...",
        options=[
            discord.SelectOption(
                label="لعبة الأسئلة والصراحة",
                description="أسئلة تفاعلية بـ 3 مستويات",
                emoji="🎯"
            ),
            discord.SelectOption(
                label="لعبة لو خيروك",
                description="تخيير اللاعبين بين خيارين صعبين ومضحكين!",
                emoji="🆚"
            ),
            discord.SelectOption(
                label="لعبة روليت الملكي",
                description="أدار الروليت الملكي واحصل على كنز الملك أو عقوبته!",
                emoji="👑"
            )
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

            await interaction.response.send_message(
                embed=embed,
                view=DifficultySelection(interaction.user),
                ephemeral=True
            )

        elif "لو خيروك" in choice:
            options_list = [
                "🆚 تخسر كل أموالك أم تنسى أصدقائك المقربين للأبد؟",
                "🆚 تعيش بدون إنترنت لمدة سنة أم بدون هاتف محمول لمدة شهرين؟",
                "🆚 تتكلم لغة الحيوانات أم تقرأ أفكار الناس؟",
                "🆚 تطير في الهواء أم تغوص في أعماق البحار؟",
                "🆚 تأكل طعاماً حاراً جداً طوال حياتك أم طعاماً بلا صوص أبداً؟"
            ]

            await interaction.channel.send(
                f"**لعبة لو خيروك لـ {interaction.user.mention}:**\n"
                f"`{random.choice(options_list)}`"
            )

            await interaction.response.send_message(
                "✅ تم إرسال لعبة لو خيروك في الشات العام!",
                ephemeral=True
            )

        elif "روليت الملكي" in choice:
            outcomes = [
                "👑 **حظ الملك:** لقد منحك الملك خزينة القلعة! ربحت 50 عملة ذهبية و 5 ألماس.",
                "👑 **غضب الملك:** أمر الملك بمصادرة جزء من أموالك! خسرت 20 عملة.",
                "👑 **عفو ملكي:** لم يحدث شيء، خرجت سالماً من قصر الملك دون خسارة أو ربح!",
                "👑 **وليمة القلعة:** أقام لك الملك وليمة فاخرة وكافأك بـ 30 عملة و 3 ألماس!"
            ]

            result = random.choice(outcomes)
            user_id = str(interaction.user.id)
            user = users_col.find_one({"user_id": user_id})

            if user:
                current_balance = user.get("balance", 0)
                current_diamonds = user.get("diamonds", 0)

                if "ربحت 50" in result:
                    users_col.update_one(
                        {"user_id": user_id},
                        {
                            "$set": {
                                "balance": current_balance + 50,
                                "diamonds": current_diamonds + 5
                            }
                        }
                    )

                    result += (
                        f"\n💰 رصيدك الجديد: {current_balance + 50} عملة"
                        f" | 💎 الألماس: {current_diamonds + 5}"
                    )

                elif "خسرت 20" in result:
                    new_b = max(0, current_balance - 20)

                    users_col.update_one(
                        {"user_id": user_id},
                        {"$set": {"balance": new_b}}
                    )

                    result += f"\n💰 رصيدك الحالي: {new_b} عملة"

                elif "كافأك بـ 30" in result:
                    users_col.update_one(
                        {"user_id": user_id},
                        {
                            "$set": {
                                "balance": current_balance + 30,
                                "diamonds": current_diamonds + 3
                            }
                        }
                    )

                    result += (
                        f"\n💰 رصيدك الجديد: {current_balance + 30} عملة"
                        f" | 💎 الألماس: {current_diamonds + 3}"
                    )

            await interaction.channel.send(
                f"{interaction.user.mention} 🎲\n{result}"
            )

            await interaction.response.send_message(
                "✅ تم تدوير الروليت الملكي في الشات العام!",
                ephemeral=True
            )


# ==========================================
# البنك الإمبراطوري - تحويلات، رواتب، وقروض
# ==========================================
from datetime import datetime, timedelta, timezone

DAILY_SALARY = 100
LOAN_INTEREST = 0.10
MAX_LOAN = 10000


def utc_now():
    return datetime.now(timezone.utc)


def get_user(user_id):
    return users_col.find_one({"user_id": str(user_id)})


def money(value):
    return f"{int(value):,}"


def sell_inventory_for_loan(inventory):
    """تقدير قيمة بيع العتاد الموجود بالنظام الحالي."""
    total = 0
    for item in inventory:
        try:
            power_text = item.split("قوة: +", 1)[1].split(")", 1)[0]
            power = int(power_text)
            total += max(10, power * 5)
        except (ValueError, IndexError):
            total += 10
    return total


class TransferModal(discord.ui.Modal, title="💱 تحويل العملات"):
    target = discord.ui.TextInput(
        label="منشن الشخص المستلم",
        placeholder="مثال: @الشخص أو <@123456789>",
        required=True,
        max_length=100
    )
    amount = discord.ui.TextInput(
        label="المبلغ",
        placeholder="مثال: 500",
        required=True,
        max_length=15
    )

    async def on_submit(self, interaction: discord.Interaction):
        sender_id = str(interaction.user.id)
        sender = get_user(sender_id)
        if not sender:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`.", ephemeral=True)
            return

        try:
            amount = int(str(self.amount.value).replace(",", "").strip())
        except ValueError:
            await interaction.response.send_message("❌ المبلغ يجب أن يكون رقماً صحيحاً.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من صفر.", ephemeral=True)
            return

        match = re.search(r"<@!?(\d+)>", str(self.target.value).strip())
        if not match:
            await interaction.response.send_message("❌ منشن الشخص غير صحيح. استخدم منشن دسكورد حقيقي.", ephemeral=True)
            return

        target_id = match.group(1)
        if target_id == sender_id:
            await interaction.response.send_message("❌ لا يمكنك تحويل العملات إلى نفسك.", ephemeral=True)
            return

        receiver = get_user(target_id)
        if not receiver:
            await interaction.response.send_message("❌ الشخص غير مسجل في النظام. يجب عليه استخدام `/تسجيل` أولاً.", ephemeral=True)
            return

        balance = sender.get("balance", 0)
        if balance < amount:
            await interaction.response.send_message(
                f"❌ رصيدك غير كافٍ. رصيدك: **{money(balance)}** عملة.", ephemeral=True
            )
            return

        users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount}})
        users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount}})

        embed = discord.Embed(
            title="💱 تم التحويل بنجاح",
            description=(
                f"🏛️ **البنك الإمبراطوري**\n\n"
                f"👤 المرسل: {interaction.user.mention}\n"
                f"👤 المستلم: <@{target_id}>\n"
                f"💰 المبلغ: **{money(amount)}** عملة\n\n"
                f"💰 رصيدك الجديد: **{money(balance - amount)}** عملة"
            ),
            color=0xD4AF37
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LoanModal(discord.ui.Modal, title="🏦 طلب قرض إمبراطوري"):
    amount = discord.ui.TextInput(
        label="مبلغ القرض",
        placeholder=f"من 100 إلى {MAX_LOAN}",
        required=True,
        max_length=15
    )
    days = discord.ui.TextInput(
        label="مدة السداد بالأيام",
        placeholder="مثال: 7",
        required=True,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user = get_user(user_id)
        if not user:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`.", ephemeral=True)
            return

        if user.get("loan", {}).get("active", False):
            await interaction.response.send_message("❌ لديك قرض قائم بالفعل. سدده أولاً قبل طلب قرض جديد.", ephemeral=True)
            return

        try:
            amount = int(str(self.amount.value).replace(",", "").strip())
            days = int(str(self.days.value).strip())
        except ValueError:
            await interaction.response.send_message("❌ أدخل أرقاماً صحيحة للمبلغ والمدة.", ephemeral=True)
            return

        if amount < 100 or amount > MAX_LOAN:
            await interaction.response.send_message(f"❌ مبلغ القرض يجب أن يكون بين 100 و {money(MAX_LOAN)} عملة.", ephemeral=True)
            return
        if days < 1 or days > 30:
            await interaction.response.send_message("❌ مدة القرض يجب أن تكون بين يوم واحد و30 يوماً.", ephemeral=True)
            return

        total_due = int(amount * (1 + LOAN_INTEREST))
        due_at = utc_now() + timedelta(days=days)
        loan = {
            "active": True,
            "principal": amount,
            "total_due": total_due,
            "remaining": total_due,
            "due_at": due_at,
            "created_at": utc_now()
        }

        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}, "$set": {"loan": loan}}
        )

        embed = discord.Embed(
            title="🏦 تمت الموافقة على القرض",
            description=(
                f"👑 **البنك الإمبراطوري**\n\n"
                f"💰 مبلغ القرض: **{money(amount)}** عملة\n"
                f"📈 الفائدة: **10%**\n"
                f"💳 إجمالي المطلوب: **{money(total_due)}** عملة\n"
                f"⏳ مدة السداد: **{days} يوم**\n"
                f"📅 موعد السداد: <t:{int(due_at.timestamp())}:F>\n\n"
                f"⚠️ عند انتهاء المهلة دون السداد، يقوم البنك ببيع **جميع مقتنياتك** تلقائياً لتسوية الدين."
            ),
            color=0xD4AF37
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LoanRepayModal(discord.ui.Modal, title="💳 سداد القرض"):
    amount = discord.ui.TextInput(
        label="المبلغ المراد سداده",
        placeholder="مثال: 500 أو اكتب كامل",
        required=True,
        max_length=15
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user = get_user(user_id)
        loan = user.get("loan", {}) if user else {}

        if not user or not loan.get("active", False):
            await interaction.response.send_message("❌ لا يوجد لديك قرض قائم.", ephemeral=True)
            return

        remaining = int(loan.get("remaining", loan.get("total_due", 0)))
        balance = int(user.get("balance", 0))
        raw = str(self.amount.value).strip().lower()

        if raw in ("كامل", "all", "full"):
            amount = remaining
        else:
            try:
                amount = int(raw.replace(",", ""))
            except ValueError:
                await interaction.response.send_message("❌ أدخل مبلغاً صحيحاً أو اكتب `كامل`.", ephemeral=True)
                return

        if amount <= 0:
            await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من صفر.", ephemeral=True)
            return
        if amount > remaining:
            amount = remaining
        if balance < amount:
            await interaction.response.send_message(
                f"❌ رصيدك غير كافٍ. تحتاج **{money(amount)}** ولديك **{money(balance)}**.", ephemeral=True
            )
            return

        new_remaining = remaining - amount
        if new_remaining == 0:
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": -amount}, "$set": {"loan": {"active": False, "paid_at": utc_now()}}}
            )
            text = "🎉 تم سداد القرض بالكامل وإغلاقه بنجاح."
        else:
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": -amount}, "$set": {"loan.remaining": new_remaining}}
            )
            text = f"💳 تم سداد **{money(amount)}**. المتبقي: **{money(new_remaining)}** عملة."

        embed = discord.Embed(
            title="🏦 عملية سداد ناجحة",
            description=f"{text}\n\n👑 البنك الإمبراطوري يشكرك على الالتزام بالسداد.",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ImperialBankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        placeholder="🏛️ اختر خدمة من البنك الإمبراطوري...",
        options=[
            discord.SelectOption(label="تحويل العملات", description="حوّل العملات إلى شخص آخر بالمنشن", emoji="💱"),
            discord.SelectOption(label="الراتب اليومي", description=f"استلم راتبك اليومي ({DAILY_SALARY} عملة)", emoji="💰"),
            discord.SelectOption(label="القروض", description="طلب قرض أو متابعة وسداد القرض الحالي", emoji="🏦")
        ]
    )
    async def bank_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        user_id = str(interaction.user.id)
        user = get_user(user_id)

        if not user:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل`.", ephemeral=True)
            return

        if choice == "تحويل العملات":
            await interaction.response.send_modal(TransferModal())
            return

        if choice == "الراتب اليومي":
            now = utc_now()
            last = user.get("last_salary")
            if last:
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                next_claim = last + timedelta(hours=24)
                if now < next_claim:
                    await interaction.response.send_message(
                        f"⏳ راتبك استلمته مسبقاً. يمكنك استلامه مجدداً <t:{int(next_claim.timestamp())}:R>.",
                        ephemeral=True
                    )
                    return

            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": DAILY_SALARY}, "$set": {"last_salary": now}}
            )
            new_balance = user.get("balance", 0) + DAILY_SALARY
            embed = discord.Embed(
                title="💰 تم صرف الراتب اليومي",
                description=(
                    "👑 **البنك الإمبراطوري**\n\n"
                    f"💵 الراتب: **{money(DAILY_SALARY)}** عملة\n"
                    f"💰 رصيدك الجديد: **{money(new_balance)}** عملة\n\n"
                    "⏰ عد بعد 24 ساعة لاستلام الراتب القادم."
                ),
                color=0xD4AF37
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if choice == "القروض":
            loan = user.get("loan", {})
            embed = discord.Embed(
                title="🏦 القروض الإمبراطورية",
                description=(
                    "اختر العملية المطلوبة من القائمة بالأسفل.\n\n"
                    "📈 فائدة القرض: **10%**\n"
                    f"💰 الحد الأعلى: **{money(MAX_LOAN)}** عملة\n"
                    "⏳ مدة القرض: من يوم إلى 30 يوماً\n"
                    "⚠️ عند التأخر، تُباع جميع مقتنياتك تلقائياً."
                ),
                color=0xD4AF37
            )
            view = LoanActionsView(has_loan=loan.get("active", False))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class LoanActionsView(discord.ui.View):
    def __init__(self, has_loan=False):
        super().__init__(timeout=180)
        self.has_loan = has_loan

    @discord.ui.select(
        placeholder="🏦 اختر عملية القرض...",
        options=[
            discord.SelectOption(label="طلب قرض جديد", description="احصل على قرض جديد وفق شروط البنك", emoji="💰"),
            discord.SelectOption(label="سداد القرض", description="ادفع جزءاً من القرض أو سدده بالكامل", emoji="💳"),
            discord.SelectOption(label="تفاصيل القرض", description="عرض المبلغ المتبقي وموعد السداد", emoji="📜")
        ]
    )
    async def loan_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        user_id = str(interaction.user.id)
        user = get_user(user_id)
        if not user:
            await interaction.response.send_message("❌ يجب عليك التسجيل أولاً.", ephemeral=True)
            return

        choice = select.values[0]
        loan = user.get("loan", {})

        if choice == "طلب قرض جديد":
            if loan.get("active", False):
                await interaction.response.send_message("❌ لديك قرض قائم بالفعل. سدده أولاً.", ephemeral=True)
            else:
                await interaction.response.send_modal(LoanModal())

        elif choice == "سداد القرض":
            if not loan.get("active", False):
                await interaction.response.send_message("❌ لا يوجد قرض قائم للسداد.", ephemeral=True)
            else:
                await interaction.response.send_modal(LoanRepayModal())

        elif choice == "تفاصيل القرض":
            if not loan.get("active", False):
                await interaction.response.send_message("✅ لا يوجد عليك قرض حالياً.", ephemeral=True)
                return
            due = loan.get("due_at")
            embed = discord.Embed(
                title="📜 تفاصيل القرض الإمبراطوري",
                description=(
                    f"💰 أصل القرض: **{money(loan.get('principal', 0))}**\n"
                    f"💳 المتبقي: **{money(loan.get('remaining', 0))}**\n"
                    f"📅 موعد السداد: <t:{int(due.timestamp())}:F>\n\n"
                    "⚠️ عدم السداد قبل الموعد يؤدي إلى بيع جميع مقتنياتك تلقائياً."
                ),
                color=0xD4AF37
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def process_overdue_loans():
    """فحص القروض المتأخرة وبيع المقتنيات تلقائياً لتسوية الدين."""
    now = utc_now()

    for user in users_col.find({"loan.active": True}):
        user_id = user.get("user_id")
        loan = user.get("loan", {})
        due_at = loan.get("due_at")

        if not user_id or not due_at:
            continue

        # MongoDB قد يعيد التاريخ بدون timezone، لذلك نوحّده قبل المقارنة.
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)

        if due_at > now:
            continue

        remaining = max(0, int(loan.get("remaining", loan.get("total_due", 0))))
        inventory = user.get("inventory", []) or []

        if remaining <= 0:
            users_col.update_one(
                {"user_id": user_id},
                {"$set": {
                    "loan.active": False,
                    "loan.paid_at": now
                }}
            )
            continue

        # عند انتهاء المهلة يتم بيع كل المقتنيات الموجودة.
        sale_value = sell_inventory_for_loan(inventory) if inventory else 0
        amount_paid_from_items = min(sale_value, remaining)
        new_remaining = remaining - amount_paid_from_items

        update_data = {
            "inventory": [],
            "loan.last_collection_at": now,
            "loan.sold_inventory_value": sale_value,
            "loan.active": new_remaining > 0
        }

        if new_remaining > 0:
            update_data["loan.remaining"] = new_remaining
        else:
            update_data["loan.remaining"] = 0
            update_data["loan.paid_at"] = now
            update_data["loan.settled_by_inventory"] = True

        users_col.update_one(
            {"user_id": user_id, "loan.active": True},
            {"$set": update_data}
        )


class LoanCollectionLoop:
    """حلقة آمنة لفحص القروض المتأخرة كل دقيقة."""
    def __init__(self):
        self.task = None

    async def start(self):
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await process_overdue_loans()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"⚠️ خطأ في فحص القروض: {e}")
            await asyncio.sleep(60)


# مهم: يجب إنشاء الكائن بعد تعريف الكلاس، وليس قبل ذلك.
loan_collection_loop = LoanCollectionLoop()


# ==========================================
# الأحداث والأوامر الأساسية للبوت
# ==========================================
@bot.event
async def on_ready():
    if loan_collection_loop.task is None or loan_collection_loop.task.done():
        loan_collection_loop.task = asyncio.create_task(loan_collection_loop.start())
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)

    print(f"✅ البوت {bot.user} جاهز ويعمل بكفاءة عالية!")


@bot.tree.command(
    name="تسجيل",
    description="تسجيل حساب جديد في النظام والحصول على الهدية"
)
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if users_col.find_one({"user_id": user_id}):
        await interaction.response.send_message(
          
