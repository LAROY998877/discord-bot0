import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient

# --- الاتصال بقاعدة البيانات ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]
devs_col = db["devs"]

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

OWNER_ID = 1103985971638325269

def is_developer(user_id):
    if user_id == OWNER_ID:
        return True
    return devs_col.find_one({"user_id": str(user_id)}) is not None

# ================== قاعدة بيانات الأبطال والطوابق ==================
HEROES_DATA = {
    "zeal": {"name": "زيل - كاسر الظلال (Zeal)", "emoji": "⚡", "power_boost": 500},
    "draven": {"name": "دريفان - سيد الجحيم (Draven)", "emoji": "🔥", "power_boost": 600},
    "kaelen": {"name": "كايلين - حارس الأبعاد (Kaelen)", "emoji": "🌌", "power_boost": 750},
    "lyra": {"name": "ليرا - ملكة الصقيع (Lyra)", "emoji": "❄️", "power_boost": 550},
    "vortexa": {"name": "فورتيكسا - ساحرة الثقوب السوداء (Vortexa)", "emoji": "🌀", "power_boost": 800},
    "valeria": {"name": "فاليريا - فارسة الفجر الذهبي (Valeria)", "emoji": "☀️", "power_boost": 650},
    "assassin_dev": {"name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)", "emoji": "🩸", "power_boost": 999999}
}

# ================== نظام البنك والتحويل ==================

class BankDepositModal(discord.ui.Modal, title="إيداع أموال في خزينة البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد إيداعه", placeholder="مثال: 100000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            val = int(self.amount.value)
            user_id = str(interaction.user.id)
            user_data = users_col.find_one({"user_id": user_id})
            wallet = user_data.get("balance", 0)
            if wallet < val or val <= 0:
                return await interaction.followup.send("❌ رصيدك النقدي لا يكفي أو المبلغ غير صالح!", ephemeral=True)
            
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -val, "bank": val}})
            await interaction.followup.send(f"✅ تم تأمين وتخزين `{val:,}` 🪙 في خزينة البنك السيادية بنجاح!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class BankWithdrawModal(discord.ui.Modal, title="سحب أموال من خزينة البنك"):
    amount = discord.ui.TextInput(label="المبلغ المراد سحبه للمحفظة", placeholder="مثال: 50000", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            val = int(self.amount.value)
            user_id = str(interaction.user.id)
            user_data = users_col.find_one({"user_id": user_id})
            bank = user_data.get("bank", 0)
            if bank < val or val <= 0:
                return await interaction.followup.send("❌ لا يملك البنك هذا المبلغ في رصيدك أو القيمة غير صالحة!", ephemeral=True)
            
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": val, "bank": -val}})
            await interaction.followup.send(f"✅ تم سحب `{val:,}` 🪙 وإضافتها إلى محفظتك الخاصة!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class TransferModal(discord.ui.Modal, title="تحويل أموال لشخص آخر"):
    amount = discord.ui.TextInput(label="المبلغ المراد تحويله", placeholder="مثال: 5000", required=True)

    def __init__(self, receiver: discord.Member):
        super().__init__()
        self.receiver = receiver

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            val = int(self.amount.value)
            sender_id = str(interaction.user.id)
            receiver_id = str(self.receiver.id)

            if sender_id == receiver_id:
                return await interaction.followup.send("❌ لا يمكنك تحويل الأموال لنفسك!", ephemeral=True)
            if val <= 0:
                return await interaction.followup.send("❌ يرجى إدخال مبلغ صحيح أكبر من الصفر!", ephemeral=True)

            sender_data = users_col.find_one({"user_id": sender_id})
            if not sender_data or sender_data.get("balance", 0) < val:
                return await interaction.followup.send("❌ رصيدك النقدي لا يكفي لإتمام هذا التحويل!", ephemeral=True)

            receiver_data = users_col.find_one({"user_id": receiver_id})
            if not receiver_data:
                return await interaction.followup.send("❌ عذراً، هذا الشخص غير مسجل في نظام اللعبة!", ephemeral=True)

            users_col.update_one({"user_id": sender_id}, {"$inc": {"balance": -val}})
            users_col.update_one({"user_id": receiver_id}, {"$inc": {"balance": val}})

            embed = discord.Embed(
                title="💸 عملية تحويل مالية ناجحة",
                description=f"تم تحويل مبلغ `{val:,}` 🪙 بنجاح إلى العضو {self.receiver.mention}!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class TransferUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="👥 اختر العضو المراد تحويل العملات له...", min_values=1, max_values=1)
        async def select_callback(inter: discord.Interaction, select: discord.ui.UserSelect):
            chosen_member = select.values[0]
            await inter.response.send_modal(TransferModal(receiver=chosen_member))
        self.add_item(select_callback)

class BankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="عرض الحساب المالي الشامل", description="الاطلاع على رصيد المحفظة والخزينة السيادية", emoji="💼", value="view"),
            discord.SelectOption(label="إيداع نقدي في البنك", description="نقل الأموال من المحفظة إلى الخزينة الآمنة", emoji="📥", value="deposit"),
            discord.SelectOption(label="سحب نقدي من البنك", description="استخراج السيولة المالية وإنفاقها بالمعارك", emoji="📤", value="withdraw"),
            discord.SelectOption(label="تحويل عملات لعضو (تبرع)", description="اختر الشخص بالمنشن وحول له المبلغ مباشرة من البنك", emoji="💸", value="transfer")
        ]
        super().__init__(placeholder="🌟 اختر المعاملة المصرفية المطلوبة من القائمة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ أنت غير مسجل! استخدم `/تسجيل` أولاً.", ephemeral=True)
        
        wallet = user_data.get("balance", 0)
        bank = user_data.get("bank", 0)
        
        if self.values[0] == "view":
            embed = discord.Embed(
                title=f"🏛️ البنك المركزي الإمبراطوري - {interaction.user.display_name}",
                description=f"💵 **السيولة النقدية (المحفظة):** `{wallet:,}` 🪙\n"
                            f"🔐 **الودائع الملكية (البنك):** `{bank:,}` 🪙\n"
                            f"👑 **إجمالي الثروة الكلية:** `{wallet + bank:,}` 🪙",
                color=discord.Color.dark_gold()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.values[0] == "deposit":
            await interaction.response.send_modal(BankDepositModal())
        elif self.values[0] == "withdraw":
            await interaction.response.send_modal(BankWithdrawModal())
        elif self.values[0] == "transfer":
            view = TransferUserSelectView()
            await interaction.followup.send("💸 يرجى اختيار العضو الذي ترغب بالتحويل له من القائمة أدناه:", view=view, ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(BankSelect())

@bot.tree.command(name="البنك", description="فتح البوابة المصرفية الإمبراطورية لإدارة ثروتك")
async def bank_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ القاعة المركزية للبنك الإمبراطوري ✨",
        description="مرحباً بك في أقدم وأعظم مؤسسة مالية في الأبعاد. استخدم القائمة المنسدلة أدناه للتحكم بأموالك:",
        color=discord.Color.from_rgb(218, 165, 32)
    )
    await interaction.response.send_message(embed=embed, view=BankView(), ephemeral=True)


# ================== نظام الطوابق الكامل ==================

class TowerSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الطوابق العادية (1 - 50)", description="معارك تدريجية ضد حراس الأبعاد الأوائل", emoji="🏢", value="normal_tower"),
            discord.SelectOption(label="طوابق الزعماء الأسطوريين", description="مواجهة حامية ضد زعماء العوالم المظلمة", emoji="👹", value="boss_tower"),
            discord.SelectOption(label="هاوية اللانهائية (Endless)", description="صعد بلا حدود واختبر قوتك المطلقة ضد أعداء لا تهزم", emoji="🌌", value="endless_tower"),
            discord.SelectOption(label="متجر وحلبة الغنائم", description="استعراض طوابقك المفتوحة وجمع غنائم المعارك", emoji="🎁", value="tower_rewards")
        ]
        super().__init__(placeholder="🗼 اختر فئة الطوابق والبرج القتالي...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            return await interaction.followup.send("❌ أنت غير مسجل في اللعبة! استخدم `/تسجيل` أولاً.", ephemeral=True)
        
        choice = self.values[0]
        max_floor = user_data.get("max_floor", 0)

        if choice == "normal_tower":
            embed = discord.Embed(
                title="🏢 برج الطوابق العادية (المستويات 1 إلى 50)",
                description=f"أنت الآن في رحلة الصعود الكبرى.\n📈 **أعلى طابق وصلته:** `{max_floor}`\n\nاختر الطابق الذي تريد اقتحامه ومقاتلة وحوشه!",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif choice == "boss_tower":
            embed = discord.Embed(
                title="👹 برج زعماء الأبعاد الكبرى",
                description="«هنا تقف وجهاً لوجه أمام عمالقة الشر المطلق.»\n\nكل زعيم تحطمه يمنحك ألقاباً نادرة ومكافآت ضخمة!",
                color=discord.Color.dark_red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif choice == "endless_tower":
            embed = discord.Embed(
                title="🌌 هاوية الطوابق اللانهائية (Endless Abyss)",
                description="طابق بلا نهاية ولا رحم... كلما صعدت خطوة زادت قوة الخصوم بشكل جنوني.",
                color=discord.Color.purple()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif choice == "tower_rewards":
            embed = discord.Embed(
                title="🎁 صندوق غنائم الطوابق والأبراج",
                description=f"إنجازاتك الحالية:\n🏆 **الطابق الأقصى:** `{max_floor}`\n💎 **مكافآت جاهزة للاستلام!**",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class TowerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(TowerSelect())

@bot.tree.command(name="الطوابق", description="فتح بوابة الأبراج القتالية العلوية ومعارك الصعود الأسطورية")
async def tower_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🗼 قمة برج الأبعاد والكواكب العظمى",
        description="مرحباً بك في ساحة التجارب واختبار القوة الكونية. استعمل القائمة أدناه لاختيار مسار الصعود والتحدي:",
        color=discord.Color.teal()
    )
    await interaction.response.send_message(embed=embed, view=TowerView(), ephemeral=True)


# ================== لوحة المطور ==================

class DevGiftModal(discord.ui.Modal, title="إهداء عتاد لعضو"):
    gear_name = discord.ui.TextInput(label="اسم قطعة العتاد أو السلاح", placeholder="مثال: سيف التنين الاسطوري", required=True)

    def __init__(self, receiver: discord.Member):
        super().__init__()
        self.receiver = receiver

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        users_col.update_one({"user_id": str(self.receiver.id)}, {"$push": {"inventory": self.gear_name.value}}, upsert=True)
        await interaction.followup.send(f"🎁 **تم إرسال العتاد بنجاح!** حصل المستخدم {self.receiver.mention} على القطعة: `{self.gear_name.value}` ⚔️")

class DevAddBalanceModal(discord.ui.Modal, title="إضافة رصيد لعضو"):
    amount = discord.ui.TextInput(label="المبلغ المراد إضافته", placeholder="مثال: 500000", required=True)

    def __init__(self, receiver: discord.Member):
        super().__init__()
        self.receiver = receiver

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            val = int(self.amount.value)
            users_col.update_one({"user_id": str(self.receiver.id)}, {"$inc": {"balance": val}}, upsert=True)
            await interaction.followup.send(f"✅ تم إضافة `{val:,}` 🪙 إلى محفظة المستخدم {self.receiver.mention} بنجاح!", ephemeral=True)
        except:
            await interaction.followup.send("❌ يرجى إدخال رقم صحيح!", ephemeral=True)

class DevGiftUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🎁 اختر العضو لإهداء العتاد له...", min_values=1, max_values=1)
        async def select_callback(inter: discord.Interaction, select: discord.ui.UserSelect):
            chosen_member = select.values[0]
            await inter.response.send_modal(DevGiftModal(receiver=chosen_member))
        self.add_item(select_callback)

class DevBalanceUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🪙 اختر العضو لإضافة الرصيد له...", min_values=1, max_values=1)
        async def select_callback(inter: discord.Interaction, select: discord.ui.UserSelect):
            chosen_member = select.values[0]
            await inter.response.send_modal(DevAddBalanceModal(receiver=chosen_member))
        self.add_item(select_callback)

class DevAddUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🛠️ اختر العضو لترقيته لمطور...", min_values=1, max_values=1)
        async def select_callback(inter: discord.Interaction, select: discord.ui.UserSelect):
            chosen_member = select.values[0]
            devs_col.update_one({"user_id": str(chosen_member.id)}, {"$set": {"user_id": str(chosen_member.id)}}, upsert=True)
            await inter.response.send_message(f"🛠️ **تمت الترقية بنجاح!** أصبح العضو {chosen_member.mention} مطوراً معتمداً في النظام الإمبراطوري.", ephemeral=True)
        self.add_item(select_callback)

class DevSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="تفعيل شخصية 'السفاح' المطلقة", description="رفع إحصائياتك وقوتك للحد الأقصى المدمر", emoji="🩸", value="assassin"),
            discord.SelectOption(label="الحصول على الثروات اللاانهائية", description="ضخ بلايين العملات العادية والنادرة لمحفظتك", emoji="💎", value="wealth"),
            discord.SelectOption(label="تطوير العتاد والمعدلات لأقصى حد", description="رفع كافة معدلاتك القتالية والعتاد للقمة بلا حدود", emoji="⚡", value="max_gear"),
            discord.SelectOption(label="إهداء عتاد لعضو", description="اختر العضو من القائمة واكتب اسم العتاد لإرساله له", emoji="🎁", value="dev_gift"),
            discord.SelectOption(label="إضافة رصيد عملات لعضو", description="اختر العضو من القائمة وحدد المبلغ المالي لإضافته", emoji="🪙", value="dev_bal"),
            discord.SelectOption(label="إضافة مطور جديد", description="اختر العضو من القائمة لمنحه صلاحية المطورين", emoji="🛠️", value="dev_add")
        ]
        super().__init__(placeholder="⚡ اختر صلاحية المطور المطلقة للتنفيذ...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        choice = self.values[0]
        
        if choice == "assassin":
            assassin = HEROES_DATA["assassin_dev"]
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "selected_hero": assassin['name'],
                        "power": assassin['power_boost'],
                        "max_floor": 999,
                        "kills": 99999,
                        "custom_title": "💀 حاكم الأبعاد ومالك السفاح"
                    }
                },
                upsert=True
            )
            await interaction.followup.send("🩸 **تم تفعيل طاقة السفاح المطلقة وإحصائياتك المرعبة بنجاح!**", ephemeral=True)
            
        elif choice == "wealth":
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": 999999999, "diamonds": 999999999}},
                upsert=True
            )
            await interaction.followup.send("💎 **تم ضخ الثروات اللانهائية!** حصلت على عملات عادية والنادرة بلا حدود في خزنتك.", ephemeral=True)
            
        elif choice == "max_gear":
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "aim": 9999999999, "evasion": 9999999999,
                        "attack": 9999999999, "accuracy": 9999999999,
                        "defense": 9999999999, "critical": 9999999999,
                        "magic": 9999999999, "intelligence": 9999999999
                    }
                },
                upsert=True
            )
            await interaction.followup.send("⚡ **تمت ترقية كافة المعدلات والعتاد للأقصى المطلق!**", ephemeral=True)
            
        elif choice == "dev_gift":
            view = DevGiftUserSelectView()
            await interaction.followup.send("🎁 يرجى اختيار العضو المراد إهداء العتاد له من القائمة:", view=view, ephemeral=True)
        elif choice == "dev_bal":
            view = DevBalanceUserSelectView()
            await interaction.followup.send("🪙 يرجى اختيار العضو المراد إضافة الرصيد له من القائمة:", view=view, ephemeral=True)
        elif choice == "dev_add":
            view = DevAddUserSelectView()
            await interaction.followup.send("🛠️ يرجى اختيار العضو لترقيته لمطور من القائمة:", view=view, ephemeral=True)

class DevControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(DevSelect())

@bot.tree.command(name="المطور", description="لوحة السيطرة والتحكم العليا للمطورين")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذه اللوحة محصورة للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة السيطرة والتحكم العليا للمطورين",
        description="أهلاً بك أيها الحاكم المطلق. استخدم القائمة المنسدلة أدناه لتنفيذ الأوامر الخارقة:",
        color=discord.Color.dark_embed()
    )
    await interaction.response.send_message(embed=embed, view=DevControlView(), ephemeral=True)


# ================== أمر الملف والتسجيل ==================
@bot.tree.command(name="الملف", description="عرض السجل الأسطوري والمعدلات القتالية الشاملة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    selected_hero = user_data.get("selected_hero", "لم يتم اختيار بطل بعد")
    power = user_data.get("power", 100)
    kills = user_data.get("kills", 0)
    
    aim = user_data.get("aim", 10)
    evasion = user_data.get("evasion", 10)
    attack = user_data.get("attack", 10)
    accuracy = user_data.get("accuracy", 10)
    defense = user_data.get("defense", 10)
    critical = user_data.get("critical", 10)
    magic = user_data.get("magic", 10)
    intelligence = user_data.get("intelligence", 10)
    
    embed_color = discord.Color.dark_red() if "السفاح" in selected_hero else discord.Color.gold()
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=embed_color
    )
    embed.add_field(name="👑 اللقب الحالي", value=custom_title, inline=True)
    embed.add_field(name="🦸‍♂️ البطل المختار", value=selected_hero, inline=True)
    embed.add_field(name="⚡ طاقة القتال", value=f"{power:,}", inline=True)
    
    stats_text = (
        f"🎯 **التصويب:** `{aim:,}` | 💨 **المراوغة:** `{evasion:,}`\n"
        f"🗡️ **الهجوم:** `{attack:,}` | 👁️ **الدقة:** `{accuracy:,}`\n"
        f"🛡️ **الدفاع:** `{defense:,}` | 💥 **القاتلة:** `{critical:,}`\n"
        f"🔮 **السحر:** `{magic:,}` | 🧠 **الذكاء:** `{intelligence:,}`"
    )
    embed.add_field(name="📊 ترسانة المعدلات القتالية المطلقة", value=stats_text, inline=False)
    
    embed.add_field(name="🏢 أعلى طابق متجاوز", value=str(max_floor), inline=True)
    embed.add_field(name="💀 الخصوم المقضي عليهم", value=str(kills), inline=True)
    embed.add_field(name="💰 المحفظة والبنك", value=f"{balance:,} 🪙 | 💳 {bank:,} 🪙", inline=False)
    embed.add_field(name="💎 الألماس والنقاد", value=f"{diamonds:,} 💎", inline=True)

    embed.set_footer(text=f"معرف المستخدم: {user_id}", icon_url=interaction.user.display_avatar.url)
    await interaction.followup.send(embed=embed, ephemeral=False)

@bot.tree.command(name="تسجيل", description="التسجيل في نظام اللعبة والحصول على لقب المبتدئ")
async def register_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    existing_user = users_col.find_one({"user_id": user_id})
    if existing_user:
        return await interaction.response.send_message("❌ أنت مسجل بالفعل في قاعدة البيانات!", ephemeral=True)
    
    new_user = {
        "user_id": user_id,
        "balance": 1000,
        "bank": 0,
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "battles_played": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "unlocked_titles": ["المبتدئ"],
        "selected_hero": "لم يتم اختيار بطل بعد",
        "inventory": [],
        "aim": 10, "evasion": 10, "attack": 10, "accuracy": 10,
        "defense": 10, "critical": 10, "magic": 10, "intelligence": 10
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

bot.run(DISCORD_TOKEN)
