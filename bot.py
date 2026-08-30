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

# ================== نظام فحص ومنح الألقاب تلقائياً ==================
def check_and_update_titles(user_id):
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        return ["المبتدئ"]
    
    unlocked = user_data.get("unlocked_titles", [])
    if "المبتدئ" not in unlocked:
        unlocked.append("المبتدئ")
        
    max_floor = user_data.get("max_floor", 0)
    if max_floor >= 100 and "الامبراطور" not in unlocked:
        unlocked.append("الامبراطور")
    if max_floor >= 500 and "الملك" not in unlocked:
        unlocked.append("الملك")
        
    kills = user_data.get("kills", 0)
    if kills >= 20 and "القاتل" not in unlocked:
        unlocked.append("القاتل")
    if kills >= 50 and "السفاح" not in unlocked:
        unlocked.append("السفاح")
        
    battles_played = user_data.get("battles_played", 0)
    if battles_played >= 20 and "اسطورة القتال" not in unlocked:
        unlocked.append("اسطورة القتال")
        
    top_rich = list(users_col.find().sort("balance", -1).limit(1))
    if top_rich and top_rich[0]["user_id"] == user_id:
        if "الغني" not in unlocked:
            unlocked.append("الغني")
    
    top_power = list(users_col.find().sort("power", -1).limit(1))
    if top_power and top_power[0]["user_id"] == user_id:
        if "اقوى الاقوياء" not in unlocked:
            unlocked.append("اقوى الاقوياء")
            
    users_col.update_one({"user_id": user_id}, {"$set": {"unlocked_titles": unlocked}})
    return unlocked

# ================== قاعدة بيانات الأبطال الأسطوريين ==================
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
    }
}

class HeroSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=data["name"], description=f"الجنس: {data['gender']} | القوة: {data['power'][:35]}...", emoji=data["emoji"], value=key)
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

# ================== بقية الأوامر والتشغيل ==================
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
        "inventory": []
    }
    users_col.insert_one(new_user)
    await interaction.response.send_message("🎉 **تم تسجيلك بنجاح!** حصلت على لقب `المبتدئ` ورصيدك الأولي.", ephemeral=True)

@bot.tree.command(name="الملف", description="عرض الملف الشخصي الأسطوري للعامة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    unlocked_titles = check_and_update_titles(user_id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    selected_hero = user_data.get("selected_hero", "لم يتم اختيار بطل بعد")
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        color=discord.Color.gold()
    )
    embed.add_field(name="👑 اللقب الحالي", value=custom_title, inline=True)
    embed.add_field(name="🦸‍♂️ البطل المختار", value=selected_hero, inline=True)
    embed.add_field(name="💰 الرصيد", value=f"{balance:,} 🪙", inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=False)

bot.run(DISCORD_TOKEN)
