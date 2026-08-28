import os
import json
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DEVELOPER_ID = 1103985971638325269
DB_FILE = "database.json"

def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "economy": {int(k): v for k, v in data.get("economy", {}).items()},
                    "stats": {int(k): v for k, v in data.get("stats", {}).items()},
                    "equipped": {int(k): v for k, v in data.get("equipped", {}).items()},
                    "users": {int(k): v for k, v in data.get("users", {}).items()},
                    "devs": set(data.get("devs", []))
                }
        except Exception as e:
            print(f"❌ خطأ أثناء قراءة ملف الحفظ: {e}")
    return {"economy": {}, "stats": {}, "equipped": {}, "users": {}, "devs": set()}

def save_database():
    data = {
        "economy": {str(k): v for k, v in USER_ECONOMY.items()},
        "stats": {str(k): v for k, v in USER_STATS.items()},
        "equipped": {str(k): v for k, v in USER_EQUIPPED.items()},
        "users": {str(k): v for k, v in REGISTERED_USERS.items()},
        "devs": list(EXTRA_DEVS)
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ البيانات: {e}")

db = load_database()
USER_ECONOMY = db["economy"]
USER_STATS = db["stats"]
USER_EQUIPPED = db["equipped"]
REGISTERED_USERS = db["users"]
EXTRA_DEVS = db["devs"]

def get_user_economy(user_id):
    if user_id not in USER_ECONOMY:
        USER_ECONOMY[user_id] = {"coins": 5000}
        save_database()
    return USER_ECONOMY[user_id]

def get_user_stats(user_id):
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {}
        save_database()
    return USER_STATS[user_id]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🟢 تم تسجيل {len(synced)} أمر بنجاح والبوت يعمل الآن باسم: {bot.user}")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

# ==================== تعريف الشخصيات (3 إناث، 3 ذكور، السفاح للمطور) ====================
CHARACTERS = {
    "فالكيريا الظلال": {
        "gender": "أنثى",
        "story": "فتاة نشأت بين أنقاض حرب مدمرة، تعلمت القتال تحت ضوء القمر وأقسمت على حماية المظلومين بضربات خفية كالشبح.",
        "skills": "سرعة فائقة، التخفي في الظلام، طعنة الخنجر القاتلة",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=800"
    },
    "لونا القوية": {
        "gender": "أنثى",
        "story": "أميرة سابقة سقطت مملكتها، فاستبدلت الحرير بدرع حديدي لتستعيد عرشها بقوة وعزيمة لا تكسر.",
        "skills": "درع لا يقفد، هجوم السيف المزدوج، قيادة الجيوش",
        "image": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800"
    },
    "سيرا ساحرة النيران": {
        "gender": "أنثى",
        "story": "ولدت في فوهة بركان نشط، ترويض اللهب ورثته عن أجدادها لتتحول إلى جحيم يمشي على الأرض.",
        "skills": "عواصف نارية، كرة الحمم البركانية، درع اللهب الحارق",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800"
    },
    "ثور الهائج": {
        "gender": "ذكر",
        "story": "محارب ضخم بنيت عضلاته من صراع الوحوش البرية، لا يخشى الموت وهدفه الوحيد إثبات تفوقه في الحلبة.",
        "skills": "ضربة المطرقة المدمرة، قدرة تحمل عالية، صرخة الرعب",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800"
    },
    "زين الحكيم": {
        "gender": "ذكر",
        "story": "مقاتل تكتيكي درس فنون القتال الشرقية، يقرأ تحركات خصومه بدقة قبل أن يوجه لهم ركلة خاطفة.",
        "skills": "تفادي الضربات، الركلة الدائرية الخاطفة، التركيز الذهني",
        "image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800"
    },
    "راين القناص": {
        "gender": "ذكر",
        "story": "صياد ماهر يستطيع إصابة الهدف من مسافات خيالية، عيناه لا تخطئان الفرصة مهما كانت الظروف.",
        "skills": "رمية السهم الخارق، الرؤية الليلية، القنص السريع",
        "image": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800"
    },
    "السفاح": {
        "gender": "ذكر (خاص بالمطور)",
        "story": "كيان أسطوري مرعب لا يعرف الرحمة، وُلد من رحم الظلمات المطلقة ليكون الحاكم المطلق والمدافع عن أسرار المطورين.",
        "skills": "الموت الفوري، التحكم بالأبعاد، درع العدم الأبدي",
        "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800"
    }
}

ITEMS_DATA = {
    "سيف حديدي بسيط": {"price": 100, "type": "عادي", "char_image": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800", "desc": "سيف تقليدي حاد."},
    "درع خشبي متين": {"price": 150, "type": "عادي", "char_image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800", "desc": "درع لحماية أساسية."},
    "خنجر الصياد السريع": {"price": 200, "type": "عادي", "char_image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=800", "desc": "خنجر للطعنات السريعة."},
    "نصل الجحيم المحرق": {"price": 1200, "type": "🔥 رتبة الجحيم", "char_image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800", "desc": "سيف مشتعل بالحمم."},
    "صولجان الخراب المظلم": {"price": 3500, "type": "🖤 رتبة الشيطان", "char_image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800", "desc": "سلاح الدمار الشامل."}
}

# ==================== نظام التسجيل واختيار الشخصية ====================

class CharacterSelectView(discord.ui.View):
    def __init__(self, name, age, gender):
        super().__init__(timeout=60)
        self.name = name
        self.age = age
        self.gender = gender
        
        # تصفية الشخصيات حسب الجنس المطلوب أو إذا كان مطوراً
        options = []
        for char_name, data in CHARACTERS.items():
            if char_name == "السفاح":
                continue # شخصية السفاح تمنح تلقائياً للمطور حصراً
            if gender == "أنثى" and data["gender"] == "أنثى":
                options.append(discord.SelectOption(label=char_name, description=data["story"][:80], value=char_name))
            elif gender == "ذكر" and data["gender"] == "ذكر":
                options.append(discord.SelectOption(label=char_name, description=data["story"][:80], value=char_name))
                
        if not options:
            options.append(discord.SelectOption(label="فالكيريا الظلال", description="شخصية افتراضية", value="فالكيريا الظلال"))
            
        self.select_menu.options = options

    @discord.ui.select(placeholder="⚔️ اختر شخصيتك الأسطورية لبدء المغامرة...")
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        char_name = select.values[0]
        char_info = CHARACTERS[char_name]
        
        REGISTERED_USERS[interaction.user.id] = {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "character": char_name
        }
        save_database()
        
        embed = discord.Embed(title=f"🎉 تم التسجيل بنجاح يا {self.name}!", description=f"**شخصيتك المختارة:** {char_name}\n\n📜 **القصة:** {char_info['story']}\n\n⚡ **المهارات:** {char_info['skills']}", color=0x2ECC71)
        embed.set_image(url=char_info["image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="تسجيل", description="سجل بياناتك (الاسم، العمر، الجنس) لاختيار شخصيتك وبدء اللعب")
@app_commands.choices(الجنس=[
    app_commands.Choice(name="ذكر", value="ذكر"),
    app_commands.Choice(name="أنثى", value="أنثى")
])
@app_commands.describe(الاسم="اسمك في اللعبة", العمر="عمرك", الجنس="اختر جنسك")
async def register(interaction: discord.Interaction, الاسم: str, العمر: int, الجنس: app_commands.Choice[str]):
    gender_val = الجنس.value
    
    # إذا كان المستخدم مطوراً، يمكنه الحصول على شخصية السفاح مباشرة أو اختيار شخصية أخرى
    if interaction.user.id == DEVELOPER_ID or interaction.user.id in EXTRA_DEVS:
        REGISTERED_USERS[interaction.user.id] = {
            "name": الاسم,
            "age": العمر,
            "gender": gender_val,
            "character": "السفاح"
        }
        save_database()
        embed = discord.Embed(title=f"👑 أهلاً بك أيها المطور العظيم {الاسم}", description=f"تم تسجيلك تلقائياً بشخصية المطور الحصرية: **السفاح** 🖤\n\n📜 **القصة:** {CHARACTERS['السفاح']['story']}\n\n⚡ **المهارات:** {CHARACTERS['السفاح']['skills']}", color=0x992d22)
        embed.set_image(url=CHARACTERS['السفاح']['image'])
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # للمستخدمين العاديين، إظهار قائمة اختيار الشخصيات حسب الجنس
    view = CharacterSelectView(الاسم, العمر, gender_val)
    embed = discord.Embed(title="✨ مرحباً بك في عالم المغامرات", description="يرجى اختيار شخصيتك المناسبة من القائمة أدناه:", color=0x3498DB)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="تغيير_الشخصية", description="تغيير شخصيتك الحالية مقابل 500 عملة")
@app_commands.choices(الجنس=[
    app_commands.Choice(name="ذكر", value="ذكر"),
    app_commands.Choice(name="أنثى", value="أنثى")
])
@app_commands.describe(الجنس="اختر جنس الشخصية الجديدة")
async def change_character(interaction: discord.Interaction, الجنس: app_commands.Choice[str]):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ أنت غير مسجل! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        return
        
    eco = get_user_economy(interaction.user.id)
    if eco["coins"] < 500:
        await interaction.response.send_message("❌ رصيدك غير كافي لتغيير الشخصية! تحتاج إلى `500` عملة.", ephemeral=True)
        return
        
    eco["coins"] -= 500
    save_database()
    
    user_data = REGISTERED_USERS[interaction.user.id]
    view = CharacterSelectView(user_data["name"], user_data["age"], الجنس.value)
    
    embed = discord.Embed(title="🔄 تغيير الشخصية", description="تم خصم 500 عملة بنجاح. اختر شخصيتك الجديدة:", color=0xE67E22)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==================== الأوامر الأساسية (مشروطة بالتسجيل) ====================

@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وشخصيتك والمهارات والعتاد")
async def profile(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل` !", ephemeral=True)
        return
        
    user_data = REGISTERED_USERS[interaction.user.id]
    char_name = user_data["character"]
    char_info = CHARACTERS.get(char_name, CHARACTERS["فالكيريا الظلال"])
    
    eco = get_user_economy(interaction.user.id)
    equipped = USER_EQUIPPED.get(interaction.user.id, "لا يوجد سلاح مركب حالياً")
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {user_data['name']}", color=0xE67E22)
    embed.set_image(url=char_info["image"])
    
    embed.add_field(name="👤 البيانات:", value=f"العمر: `{user_data['age']}` | الجنس: `{user_data['gender']}`", inline=False)
    embed.add_field(name="⚔️ الشخصية الأسطورية:", value=f"**{char_name}**\n📜 {char_info['story']}\n⚡ المهارات: {char_info['skills']}", inline=False)
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="🛡️ العتاد المُركب:", value=f"`{equipped}`", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="الحقيبة", description="عرض حقيبتك وتركيب المعدات")
async def inventory(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب التسجيل أولاً باستخدام أمر `/تسجيل` !", ephemeral=True)
        return
        
    target = interaction.user
    stats = get_user_stats(target.id)
    equipped = USER_EQUIPPED.get(target.id, "لا يوجد سلاح مركب حالياً")
    
    embed = discord.Embed(title=f"🎒 حقيبة المغامر | {target.display_name}", color=0xD4AF37)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="⚔️ العتاد النشط:", value=f"`{equipped}`", inline=False)
    
    gear_text = "\n".join([f"🔹 **{gear}** (العدد: {count})" for gear, count in stats.items()]) if stats else "حقيبتك فارغة تماماً!"
    embed.add_field(name="📦 المعدات المملوكة:", value=gear_text, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== نظام حلبة المعارك (1v1, 2v2, 3v3) ====================

class BattleAcceptView(discord.ui.View):
    def __init__(self, challenger, opponents, mode, bet):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponents = opponents
        self.mode = mode
        self.bet = bet
        self.accepted_users = set()

    @discord.ui.button(label="⚔️ قبول التحدي ودخول المعركة", style=discord.ButtonStyle.green)
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.opponents:
            await interaction.response.send_message("❌ أنت لست مقصوداً بهذا التحدي!", ephemeral=True)
            return
            
        if interaction.user in self.accepted_users:
            await interaction.response.send_message("⚠️ لقد وافقت مسبقاً!", ephemeral=True)
            return
            
        if self.bet > 0:
            eco = get_user_economy(interaction.user.id)
            if eco["coins"] < self.bet:
                await interaction.response.send_message(f"❌ رصيدك غير كافي لدفع الرهان ({self.bet} عملة)!", ephemeral=True)
                return

        self.accepted_users.add(interaction.user)
        
        if len(self.accepted_users) == len(self.opponents):
            winning_team = random.choice([1, 2])
            total_pot = self.bet * (len(self.opponents) + 1) if self.bet > 0 else 0
            
            if winning_team == 1:
                winner_text = f"👑 الفائز: **{self.challenger.display_name}** وفريقه!"
                if self.bet > 0:
                    get_user_economy(self.challenger.id)["coins"] += total_pot
                    save_database()
                result_embed = discord.Embed(title=f"🏟️ نتائج معركة الحلبة ({self.mode})", description=f"🔥 انتصار ساحق للبطل!\n\n{winner_text}\n💰 الجائزة: `{total_pot}` عملة", color=0xE74C3C)
            else:
                winner_text = f"👑 الفائزون: **الخصوم** بقيادة {', '.join([u.display_name for u in self.opponents])}"
                if self.bet > 0:
                    for op in self.opponents:
                        get_user_economy(op.id)["coins"] += (total_pot // len(self.opponents))
                    save_database()
                result_embed = discord.Embed(title=f"🏟️ نتائج معركة الحلبة ({self.mode})", description=f"🔥 معركة دموية انتهت بفوز الخصوم!\n\n{winner_text}", color=0xE74C3C)
                
            result_embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800")
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=result_embed, view=self)
            self.stop()
        else:
            await interaction.response.send_message(f"✅ تم تسجيل موافقة **{interaction.user.display_name}**.", ephemeral=True)


@bot.tree.command(name="المعارك", description="حلبة المعارك الأسطورية (1v1, 2v2, 3v3) مع الرهانات")
@app_commands.choices(النمط=[
    app_commands.Choice(name="⚔️ مبارزة فردية (1 ضد 1)", value="1v1"),
    app_commands.Choice(name="🛡️ معركة ثنائية (2 ضد 2)", value="2v2"),
    app_commands.Choice(name="🔥 حرب ثلاثية (3 ضد 3)", value="3v3")
])
@app_commands.describe(النمط="اختر النمط", الخصم_الأول="الخصم الأول", الخصم_الثاني="الخصم الثاني", الخصم_الثالث="الخصم الثالث", الرهان="قيمة الرهان بالعملات")
async def battles(
    interaction: discord.Interaction, 
    النمط: app_commands.Choice[str], 
    الخصم_الأول: discord.Member, 
    الخصم_الثاني: discord.Member = None, 
    الخصم_الثالث: discord.Member = None,
    الرهان: int = 0
):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام أمر `/تسجيل` !", ephemeral=True)
        return

    mode = النمط.value
    opponents = []
    
    if mode == "1v1":
        opponents = [الخصم_الأول]
    elif mode == "2v2":
        if not الخصم_الثاني:
            await interaction.response.send_message("❌ نظام 2v2 يتطلب خصمين!", ephemeral=True)
            return
        opponents = [الخصم_الأول, الخصم_الثاني]
    elif mode == "3v3":
        if not الخصم_الثاني or not الخصم_الثالث:
            await interaction.response.send_message("❌ نظام 3v3 يتطلب ثلاثة خصوم!", ephemeral=True)
            return
        opponents = [الخصم_الأول, الخصم_الثاني, الخصم_الثالث]
        
    if interaction.user in opponents or interaction.user == الخصم_الأول:
        await interaction.response.send_message("❌ لا يمكنك تحدي نفسك!", ephemeral=True)
        return

    if الرهان > 0:
        challenger_eco = get_user_economy(interaction.user.id)
        if challenger_eco["coins"] < الرهان:
            await interaction.response.send_message(f"❌ رصيدك غير كافي لدخول المعركة بهذا الرهان (`{الرهان}` عملة).", ephemeral=True)
            return
        challenger_eco["coins"] -= الرهان
        save_database()

    opponents_mention = ", ".join([op.mention for op in opponents])
    embed = discord.Embed(
        title=f"🏟️ تحدي حلبة المعارك | {mode}",
        description=f"المتحدي: {interaction.user.mention}\n ضد: {opponents_mention}\n\n💰 الرهان: `{الرهان}` عملة\n\n*(أمام الخصوم 30 ثانية للقبول)*",
        color=0xE67E22
    )
    embed.set_image(url="https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800")
    
    view = BattleAcceptView(interaction.user, opponents, mode, الرهان)
    await interaction.response.send_message(content=opponents_mention, embed=embed, view=view)

bot.run(os.getenv('TOKEN'))
