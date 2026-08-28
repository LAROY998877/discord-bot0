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
                    "guilds": data.get("guilds", {}),
                    "devs": set(data.get("devs", []))
                }
        except Exception as e:
            print(f"❌ خطأ أثناء قراءة ملف الحفظ: {e}")
    return {"economy": {}, "stats": {}, "equipped": {}, "users": {}, "guilds": {}, "devs": set()}

def save_database():
    data = {
        "economy": {str(k): v for k, v in USER_ECONOMY.items()},
        "stats": {str(k): v for k, v in USER_STATS.items()},
        "equipped": {str(k): v for k, v in USER_EQUIPPED.items()},
        "users": {str(k): v for k, v in REGISTERED_USERS.items()},
        "guilds": GUILDS_DATA,
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
GUILDS_DATA = db["guilds"]
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

# ==================== تعريف الشخصيات ====================
CHARACTERS = {
    "فالكيريا الظلال": {
        "gender": "أنثى",
        "story": "فتاة نشأت بين أنقاض حرب مدمرة، تعلمت القتال تحت ضوء القمر وأقسمت على حماية المظلومين.",
        "skills": "سرعة فائقة، التخفي في الظلام، طعنة الخنجر القاتلة",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=800"
    },
    "لونا القوية": {
        "gender": "أنثى",
        "story": "أميرة سابقة سقطت مملكتها، فاستبدلت الحرير بدرع حديدي لتستعيد عرشها بقوة.",
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
        "story": "محارب ضخم بنيت عضلاته من صراع الوحوش البرية، لا يخشى الموت وهدفه الوحيد إثبات تفوقه.",
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
        "story": "صياد ماهر يستطيع إصابة الهدف من مسافات خيالية، عيناه لا تخطئان الفرصة مهما كانت.",
        "skills": "رمية السهم الخارق، الرؤية الليلية، القنص السريع",
        "image": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800"
    },
    "السفاح": {
        "gender": "ذكر (خاص بالمطور)",
        "story": "كيان أسطوري مرعب لا يعرف الرحمة، وُلد من رحم الظلمات المطلقة ليكون الحاكم المطلق.",
        "skills": "الموت الفوري، التحكم بالأبعاد، درع العدم الأبدي",
        "image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800"
    }
}

# ==================== نظام التسجيل عبر نافذة (Modal) ====================

class CharacterSelectAfterModal(discord.ui.View):
    def __init__(self, name, age, gender):
        super().__init__(timeout=60)
        self.name = name
        self.age = age
        self.gender = gender
        
        options = []
        for char_name, data in CHARACTERS.items():
            if char_name == "السفاح":
                continue
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


class RegisterModal(discord.ui.Modal, title="📝 نافذة التسجيل في اللعبة"):
    name_input = discord.ui.TextInput(label="الاسم في اللعبة", placeholder="اكتب اسمك...", max_length=50)
    age_input = discord.ui.TextInput(label="العمر", placeholder="اكتب عمرك بالأرقام (مثال: 20)...", max_length=3)
    gender_input = discord.ui.TextInput(label="الجنس", placeholder="اكتب (ذكر) أو (أنثى)...", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value
        try:
            age = int(self.age_input.value)
        except ValueError:
            await interaction.response.send_message("❌ العمر يجب أن يكون رقماً صحيحاً!", ephemeral=True)
            return
            
        gender = self.gender_input.value.strip()
        if gender not in ["ذكر", "أنثى"]:
            await interaction.response.send_message("❌ الجنس يجب أن يكون إما (ذكر) أو (أنثى) فقط!", ephemeral=True)
            return

        # إذا كان المطور
        if interaction.user.id == DEVELOPER_ID or interaction.user.id in EXTRA_DEVS:
            REGISTERED_USERS[interaction.user.id] = {
                "name": name,
                "age": age,
                "gender": gender,
                "character": "السفاح"
            }
            save_database()
            embed = discord.Embed(title=f"👑 أهلاً بك أيها المطور العظيم {name}", description=f"تم تسجيلك تلقائياً بشخصية المطور الحصرية: **السفاح** 🖤\n\n📜 **القصة:** {CHARACTERS['السفاح']['story']}\n\n⚡ **المهارات:** {CHARACTERS['السفاح']['skills']}", color=0x992d22)
            embed.set_image(url=CHARACTERS['السفاح']['image'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        view = CharacterSelectAfterModal(name, age, gender)
        embed = discord.Embed(title="✨ مرحباً بك في عالم المغامرات", description=f"الاسم: **{name}** | العمر: **{age}** | الجنس: **{gender}**\n\nاختر شخصيتك المناسبة من القائمة أدناه:", color=0x3498DB)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="تسجيل", description="فتح قائمة التسجيل التفاعلية (Modal) لإدخال الاسم، العمر، والجنس")
async def register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


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
    view = CharacterSelectAfterModal(user_data["name"], user_data["age"], الجنس.value)
    
    embed = discord.Embed(title="🔄 تغيير الشخصية", description="تم خصم 500 عملة بنجاح. اختر شخصيتك الجديدة:", color=0xE67E22)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==================== نظام النقابات (Guilds) ====================

@bot.tree.command(name="انشاء_نقابة", description="إنشاء نقابة جديدة مقابل 299 عملة")
@app_commands.describe(اسم_الننقابة="اسم النقابة الفريد")
async def create_guild(interaction: discord.Interaction, اسم_الننقابة: str):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً باستخدام `/تسجيل`!", ephemeral=True)
        return
        
    for g_name, g_data in GUILDS_DATA.items():
        if g_data["leader_id"] == interaction.user.id:
            await interaction.response.send_message("❌ أنت تمتلك نقابة بالفعل ولا يمكنك إنشاء أخرى!", ephemeral=True)
            return
        if g_name == اسم_الننقابة:
            await interaction.response.send_message("❌ اسم النقابة هذا موجود مسبقاً، اختر اسمًا آخر!", ephemeral=True)
            return

    eco = get_user_economy(interaction.user.id)
    if eco["coins"] < 299:
        await interaction.response.send_message("❌ رصيدك غير كافي! تحتاج إلى `299` عملة لإنشاء نقابة.", ephemeral=True)
        return

    eco["coins"] -= 299
    
    GUILDS_DATA[اسم_الننقابة] = {
        "leader_id": interaction.user.id,
        "level": 1,
        "exp": 0,
        "treasury_coins": 0,
        "treasury_items": {},
        "members": [interaction.user.id]
    }
    save_database()

    embed = discord.Embed(title="🏰 تم إنشاء النقابة بنجاح!", description=f"اسم النقابة: **{اسم_الننقابة}**\nالقائد: {interaction.user.mention}\nالمستوى الحالي: `1` (الحد الأقصى 500)", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="تبرع_للنقابة", description="التبرع بالعملات أو العتاد لنقابتك لرفع مستواها (أقصى لفل 500)")
@app_commands.choices(نوع_التبرع=[
    app_commands.Choice(name="💰 عملات معدنية", value="coins"),
    app_commands.Choice(name="🛡️ عتاد / معدات", value="item")
])
@app_commands.describe(نوع_التبرع="اختر نوع التبرع", الكمية_أو_اسم_العتاد="اكتب عدد العملات أو اسم العتاد الذي تملكه في حقيبتك")
async def donate_guild(interaction: discord.Interaction, نوع_التبرع: app_commands.Choice[str], الكمية_أو_اسم_العتاد: str):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
        return

    # ابحث عن النقابة التي ينتمي لها المستخدم
    user_guild = None
    for g_name, g_data in GUILDS_DATA.items():
        if interaction.user.id in g_data["members"]:
            user_guild = g_name
            break

    if not user_guild:
        await interaction.response.send_message("❌ أنت لست عضواً في أي نقابة!", ephemeral=True)
        return

    guild = GUILDS_DATA[user_guild]
    
    if guild["level"] >= 500:
        await interaction.response.send_message("🎉 لقد وصلت نقابتكم إلى الحد الأقصى للمستوى (`500`) بالفعل!", ephemeral=True)
        return

    exp_gained = 0

    if نوع_التبرع.value == "coins":
        try:
            amount = int(الكمية_أو_اسم_العتاد)
        except ValueError:
            await interaction.response.send_message("❌ يجيب كتابة رقم صحيح للعملات المتبرع بها!", ephemeral=True)
            return

        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < amount:
            await interaction.response.send_message(f"❌ لا تملك هذا العدد من العملات في رصيدك! (`{eco['coins']}` متاح)", ephemeral=True)
            return

        eco["coins"] -= amount
        guild["treasury_coins"] += amount
        exp_gained = amount // 10  # كل 10 عملات تعطي 1 خبرة للنقابة
    else:
        item_name = الكمية_أو_اسم_العتاد.strip()
        stats = get_user_stats(interaction.user.id)
        if item_name not in stats or stats[item_name] <= 0:
            await interaction.response.send_message(f"❌ أنت لا تملك قطعة العتاد `{item_name}` في حقيبتك!", ephemeral=True)
            return

        stats[item_name] -= 1
        if stats[item_name] <= 0:
            del stats[item_name]

        if item_name not in guild["treasury_items"]:
            guild["treasury_items"][item_name] = 0
        guild["treasury_items"][item_name] += 1
        exp_gained = 50  # كل قطعة عتاد تمنح 50 نقطة خبرة للنقابة

    # نظام رفع لفل النقابة (كل 500 نقطة خبرة ترفع مستوى النقابة بحد أقصى 500)
    guild["exp"] += exp_gained
    required_exp_for_next_level = guild["level"] * 500
    
    level_ups = 0
    while guild["exp"] >= required_exp_for_next_level and guild["level"] < 500:
        guild["exp"] -= required_exp_for_next_level
        guild["level"] += 1
        level_ups += 1
        required_exp_for_next_level = guild["level"] * 500

    save_database()

    msg = f"✅ تم التبرع بنجاح لنقابة **{user_guild}**!\n📈 اكتسبة النقابة `{exp_gained}` نقطة خبرة."
    if level_ups > 0:
        msg += f"\n🎉 **مبروك! ارتفع مستوى النقابة وأصبحت في المستوى `{guild['level']}`!**"
        
    await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="معلومات_الننقابة", description="عرض تفاصيل ومستوى نقابتك وخزنتها")
async def guild_info(interaction: discord.Interaction):
    if interaction.user.id not in REGISTERED_USERS:
        await interaction.response.send_message("❌ يجب عليك التسجيل أولاً!", ephemeral=True)
        return

    user_guild = None
    for g_name, g_data in GUILDS_DATA.items():
        if interaction.user.id in g_data["members"]:
            user_guild = g_name
            break

    if not user_guild:
        await interaction.response.send_message("❌ أنت لست منضماً لأي نقابة حالياً!", ephemeral=True)
        return

    g = GUILDS_DATA[user_guild]
    leader = await bot.fetch_user(g["leader_id"])
    
    items_list = "\n".join([f"- {it}: {cnt}" for it, cnt in g["treasury_items"].items()]) if g["treasury_items"] else "خزنة العتاد فارغة."

    embed = discord.Embed(title=f"🏰 معلومات نقابة: {user_guild}", color=0x9B59B6)
    embed.add_field(name="👑 قائد النقابة", value=leader.mention if leader else "غير معروف", inline=True)
    embed.add_field(name="⭐ مستوى النقابة", value=f"`{g['level']}` / 500", inline=True)
    embed.add_field(name="📊 نقاط الخبرة (EXP)", value=f"`{g['exp']}` / {g['level'] * 500}", inline=True)
    embed.add_field(name="💰 عملات الخزنة", value=f"`{g['treasury_coins']}` عملة", inline=True)
    embed.add_field(name="👥 عدد الأعضاء", value=f"`{len(g['members'])}` أعضاء", inline=True)
    embed.add_field(name="🛡️ عتاد الخزنة", value=items_list, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== الأوامر الأساسية ====================

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

bot.run(os.getenv('TOKEN'))
