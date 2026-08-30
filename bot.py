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
devs_col = db["devs"] # مجموعة قاعدة بيانات المطورين

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

# الأيدي الأساسي الخاص بك كمالك للبوت
OWNER_ID = 1103985971638325269

def is_developer(user_id):
    if user_id == OWNER_ID:
        return True
    return devs_col.find_one({"user_id": str(user_id)}) is not None

# دالة مساعدة لاستخراج الآيدي الصافي من المنشن أو النص
def extract_user_id(text):
    clean = text.strip().replace("<@", "").replace(">", "").replace("!", "")
    return str(int(clean))

# ================== قاعدة بيانات الأبطال (العاديين والمطور) ==================
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
        "story": "مقاتلة استثنائية استدمجت طاقة الثقوب السوداء في جسدها. تستطيع جذب أي عدو إليها وسحقه بقوة جاذبية تفوق تخيل البشر."
    },
    "valeria": {
        "name": "فاليريا - فارسة الفجر الذهبي (Valeria)",
        "gender": "أنثى",
        "emoji": "☀️",
        "power": "الشفاء السريع، القوة البدنية المطلقة، وهالة النور المقدس",
        "story": "قائدة حرس الفجر الأسطوريون. تحمل درعاً مقدساً لا ينكسر وسيفاً يضيء بنور الشمس الأولى، تطهر الأراضي من الوحوش والظلام."
    },
    # 💀 شخصية السفاح الحصرية للمطور فقط
    "assassin_dev": {
        "name": "💀 السفاح الأبدي - حاصد الأرواح (The Executioner)",
        "gender": "مطور مطلق",
        "emoji": "🩸",
        "power": "طمس الوجود، التحكم المطلق في الأكوان، ومحو أي كائن بنظرة واحدة (قوة لا تقهر)",
        "story": "كيان مرعب هبط من الفراغ المطلق، وُجد ليكون اليد القاضية التي لا ترتجف. يغذى طاقته من أرواح العوالم المنهارة، ولا يمكن لأي بطل عادي الوقوف في حضرته دون أن يتلاشى.",
        "stats": {
            "power": 9999999,
            "max_floor": 999,
            "kills": 99999
        }
    }
}

# قائمة الأبطال العامة (للاعبين العاديين)
class HeroSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=data["name"], description=f"الجنس: {data['gender']} | القوة: {data['power'][:35]}...", emoji=data["emoji"], value=key)
            for key, data in HEROES_DATA.items() if key != "assassin_dev" # استثناء شخصية السفاح للعامة
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
        
        users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"selected_hero": hero['name']}}, upsert=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HeroSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HeroSelect())

@bot.tree.command(name="أبطال", description="استعراض قائمة الأبطال الأسطوريين واختيار بطلك المفضل")
async def heroes_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ قاعة اختيار الأبطال الأسطوريين 🛡️",
        description="«اختر بطلك بحكمة، فالقصة والقوة التي ستختارها سترافقك في جميع المعارك.»\n\nاختر من القائمة المنسدلة أدناه:",
        color=discord.Color.gold()
    )
    view = HeroSelectView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


# ================== لوحة المطور وتحكم شخصية السفاح ==================
class DevControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="💀 تفعيل شخصية 'السفاح' المطلقة", style=discord.ButtonStyle.danger, emoji="🩸")
    async def activate_assassin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_developer(interaction.user.id):
            return await interaction.response.send_message("❌ هذا الزر مخصص للمطورين فقط!", ephemeral=True)
        
        assassin = HEROES_DATA["assassin_dev"]
        user_id = str(interaction.user.id)
        
        # منح المطور إحصائيات وقوة السفاح الخارقة في قاعدة البيانات مباشرة
        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "selected_hero": assassin['name'],
                    "power": assassin['stats']['power'],
                    "max_floor": assassin['stats']['max_floor'],
                    "kills": assassin['stats']['kills'],
                    "custom_title": "💀 حاكم الأبعاد ومالك السفاح"
                }
            },
            upsert=True
        )
        
        embed = discord.Embed(
            title="🩸 تم تفعيل طاقة 'السفاح الأبدي' بنجاح!",
            description=f"**القدرة:** {assassin['power']}\n\n**القصة:**\n*{assassin['story']}*\n\n⚡ **تم رفع إحصائياتك إلى الحد الأقصى المطلق في قاعدة البيانات!**",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="المطور", description="لوحة التحكم الخاصة بالمطورين وصلاحياتهم المطلقة")
async def developer_command(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص للمطورين المعتمدين فقط!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة التحكم العليا للمطورين",
        description="أهلاً بك أيها المطور. يمكنك من هنا تفعيل شخصية **السفاح** المرعبة لترسانتك القتالية والسيطرة المطلقة:",
        color=discord.Color.dark_embed()
    )
    view = DevControlView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ================== أمر الملف الشخصي الأسطوري ==================
@bot.tree.command(name="الملف", description="عرض الملف الشخصي الأسطوري للعامة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    selected_hero = user_data.get("selected_hero", "لم يتم اختيار بطل بعد")
    power = user_data.get("power", 100)
    kills = user_data.get("kills", 0)
    
    # تحديد لون الإطار (إذا كان السفاح فهو أحمر داكن دموي، وللآخرين ذهبي)
    embed_color = discord.Color.dark_red() if "السفاح" in selected_hero else discord.Color.gold()
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=embed_color
    )
    embed.add_field(name="👑 اللقب الحالي", value=custom_title, inline=True)
    embed.add_field(name="🦸‍♂️ البطل المختار", value=selected_hero, inline=True)
    embed.add_field(name="⚡ مستوى الطاقة", value=f"{power:,}", inline=True)
    embed.add_field(name="🏢 أعلى طابق", value=str(max_floor), inline=True)
    embed.add_field(name="💀 الخصوم المقضي عليهم", value=str(kills), inline=True)
    embed.add_field(name="💰 الرصيد والجوهرة", value=f"{balance:,} 🪙 | {diamonds:,} 💎", inline=True)
    
    # إذا كان البطل هو السفاح، نضع نبذة عن قصته وقوته المرعبة في الملف مباشرة!
    if "السفاح" in selected_hero:
        embed.add_field(
            name="🩸 حالة الكيان المرعب",
            value="*«كيان مدمر يطمس الأبعاد ولا يرحم أحداً... طاقته تفوق مقاييس الكون.»*",
            inline=False
        )

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
        "diamonds": 10,
        "max_floor": 0,
        "kills": 0,
        "battles_played": 0,
        "power": 100,
        "custom_title": "المبتدئ",
        "unlocked_titles": ["المبتدئ"],
        "selected_hero": "لم يتم اختيار بطل بعد",
        "inventory": []
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

bot.run(DISCORD_TOKEN)
