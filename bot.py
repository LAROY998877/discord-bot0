import os
import random
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

class BotClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ تم مزامنة الأوامر ونظام الألقاب بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل باسم: {bot.user}")

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

# ================== قاعدة بيانات الأسئلة ==================
TRIVIA_QUESTIONS = {
    "عادي": [
        "ما هو لون السماء في الأيام الصافية؟", "كم عدد أيام السنة الميلادية؟", "ما هو الحيوان المعروف بملك الغابة؟", "في أي قارة تقع مصر؟", "ما هو عاصمة المملكة العربية السعودية؟",
        "كم عدد ساعات اليوم الواحد؟", "ما هو أسرع حيوان بري في العالم؟", "ما هو العنصر الكيميائي للماء؟", "كم عدد الألوان في قوس المطر؟", "ما هي عاصمة فرنسا؟"
    ],
    "متوسط": [
        "ما هي عاصمة أستراليا؟", "من هو القائد المسلم الذي فتح قسطنطينية؟", "في أي عام قامت الحرب العالمية الأولى؟", "ما هو أكبر أقيانوس في العالم؟", "من هو مكتشف قانون الجاذبية الأرضية؟",
        "ما هي الدولة التي تُلقب ببلاد الـ 1000 بحيرة؟", "ما هو أعمق أخدود في العالم؟", "من هو مؤلف رواية البؤساء؟", "ما هي أصغر دولة مستقلة في العالم مساحة؟", "ما هو غاز الحياة الذي تنتجه النباتات؟"
    ],
    "جريئ جدا": [
        "ما هو أكثر شيء تندم عليه بجدية في حياتك الماضية؟", "لو اضطررت لسرقة شيء واحد للنجاة بحياتك، ماذا ستسرق ومن أين؟", "من هو الشخص في هذا السيرفر الذي تتمنى لو لم تقابله أبداً؟", "ما هو أكبر سر تحافظ عليه بشدة وتخافه أن ينكشف لعائلتك؟", "هل سبق لك أن كذبت كذبة كبيرة ونجحت فيها تماماً دون أن يعلم أحد؟ ما هي؟",
        "لو أتيحت لك الفرصة لمسح شخص واحد من ذاكرتك للأبد، من سيكون؟", "ما هو أغبى مبلغ مال دفعته على شيء تافه وندمت عليه لاحقاً؟", "هل تشعر بالغيرة من أحد أصدقائك المقربين؟ من ولماذا؟",
        "ما هو الموقف الأكثر إحراجاً الذي تعرضت له أمام شخص تعجب به؟", "ما هي أقصى عقوبة تعرضت لها في طفولتك وبقيت محفورة بذاكرتك؟"
    ]
}

# ================== نظام الألعاب وغرفة الانتظار (ظاهر للكل) ==================
class TriviaQuestionView(discord.ui.View):
    def __init__(self, difficulty, questions_list, author_id, players):
        super().__init__(timeout=300)
        self.difficulty = difficulty
        self.questions_list = questions_list
        self.author_id = author_id
        self.players = players
        self.current_q = random.choice(questions_list)

    @discord.ui.button(label="سؤال جديد 🎲", style=discord.ButtonStyle.primary)
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.players:
            return await interaction.response.send_message("❌ أنت لست مشاركاً في هذه اللعبة!", ephemeral=True)
        
        self.current_q = random.choice(self.questions_list)
        players_mention = ", ".join([f"<@{p}>" for p in self.players])
        embed = discord.Embed(
            title=f"🧠 لعبة الأسئلة الجماعية (مستوى: {self.difficulty})",
            description=f"**اللاعبون المشاركون:** {players_mention}\n\n**السؤال:**\n{self.current_q}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="إيقاف اللعبة 🛑", style=discord.ButtonStyle.danger)
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id and interaction.user.id not in self.players:
            return await interaction.response.send_message("❌ ليس لديك صلاحية لإيقاف هذه اللعبة!", ephemeral=True)
        self.stop()
        embed = discord.Embed(title="🛑 تم إيقاف اللعبة", description=f"تم إنهاء جلسة اللعبة بواسطة <@{interaction.user.id}>.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

class TriviaLobbyView(discord.ui.View):
    def __init__(self, difficulty, author_id):
        super().__init__(timeout=300)
        self.difficulty = difficulty
        self.author_id = author_id
        self.players = [author_id]

    @discord.ui.button(label="انضمام للعبة 🎮", style=discord.ButtonStyle.green)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            return await interaction.response.send_message("❌ أنت منضم بالفعل في هذه اللعبة!", ephemeral=True)
        self.players.append(interaction.user.id)
        
        players_mention = ", ".join([f"<@{p}>" for p in self.players])
        embed = discord.Embed(
            title=f"🎮 غرفة انتظار لعبة الأسئلة (مستوى: {self.difficulty})",
            description=f"اضغط على زر **انضمام للعبة** للمشاركة! (يتطلب شخصين على الأقل لبدء اللعبة).\n\n**اللاعبون المسجلون ({len(self.players)}):**\n{players_mention}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="بدء اللعبة ▶️", style=discord.ButtonStyle.primary)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ فقط منشئ اللعبة يمكنه بدءها!", ephemeral=True)
        if len(self.players) < 2:
            return await interaction.response.send_message("❌ لا يمكن بدء اللعبة إلا إذا انضم أكثر من شخص (شخصين على الأقل)!", ephemeral=True)
        
        q_list = TRIVIA_QUESTIONS.get(self.difficulty, TRIVIA_QUESTIONS["عادي"])
        view = TriviaQuestionView(self.difficulty, q_list, self.author_id, self.players)
        selected_q = random.choice(q_list)
        players_mention = ", ".join([f"<@{p}>" for p in self.players])

        embed = discord.Embed(
            title=f"🧠 لعبة الأسئلة الجماعية (مستوى: {self.difficulty})",
            description=f"**اللاعبون المشاركون:** {players_mention}\n\n**السؤال:**\n{selected_q}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="إيقاف اللعبة 🛑", style=discord.ButtonStyle.danger)
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ فقط منشئ اللعبة يمكنه إيقافها!", ephemeral=True)
        self.stop()
        embed = discord.Embed(title="🛑 تم إيقاف اللعبة", description="تم إلغاء غرفة الانتظار بواسطة المنشئ.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

class TriviaDifficultySelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="عادي", description="أسئلة عامة وبسيطة", emoji="🟢", value="عادي"),
            discord.SelectOption(label="متوسط", description="أسئلة ثقافية وتاريخية", emoji="🟡", value="متوسط"),
            discord.SelectOption(label="جريئ جدا", description="أسئلة صريحة وتحديات شخصية", emoji="🔴", value="جريئ جدا")
        ]
        super().__init__(placeholder="اختر مستوى صعوبة الأسئلة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        level = self.values[0]
        embed = discord.Embed(
            title=f"🎮 غرفة انتظار لعبة الأسئلة (مستوى: {level})",
            description=f"اضغط على زر **انضمام للعبة** للمشاركة! (يتطلب شخصين على الأقل لبدء اللعبة).\n\n**اللاعبون المسجلون (1):**\n<@{self.author_id}>",
            color=discord.Color.blue()
        )
        view = TriviaLobbyView(level, self.author_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class GamesMenuView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.add_item(TriviaDifficultySelect(author_id))

@bot.tree.command(name="العاب", description="قائمة الألعاب الترفيهية الجماعية في السيرفر")
async def games_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قاعة الألعاب الترفيهية",
        description="اختر مستوى الصعوبة لبدء غرفة الانتظار:",
        color=discord.Color.dark_magenta()
    )
    view = GamesMenuView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ================== نظام التسجيل وبقية الأوامر ==================
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

class TitleSelect(discord.ui.Select):
    def __init__(self, unlocked_titles):
        title_emojis = {
            "المبتدئ": "🟢", "الامبراطور": "👑", "الملك": "🔱", "الغني": "💰",
            "القاتل": "🗡️", "السفاح": "🩸", "اسطورة القتال": "⚡", "اقوى الاقوياء": "🔥"
        }
        options = [discord.SelectOption(label=t, value=t, emoji=title_emojis.get(t, "✨")) for t in unlocked_titles]
        super().__init__(placeholder="اختر لقباً من ألقابك المتاحة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_title = self.values[0]
        users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"custom_title": selected_title}})
        await interaction.response.edit_message(content=f"✨ **تم تفعيل لقبك الجديد بنجاح:** `{selected_title}`", view=None)

class ProfileView(discord.ui.View):
    def __init__(self, author_id, unlocked_titles):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.unlocked_titles = unlocked_titles

    @discord.ui.button(label="اختر اللقب", style=discord.ButtonStyle.blurple, emoji="👑")
    async def change_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        view.add_item(TitleSelect(self.unlocked_titles))
        await interaction.response.send_message("📌 الألقاب المتاحة لك بناءً على إنجازاتك:", view=view, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="الملف", description="عرض الملف الشخصي والإنجازات والألقاب")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    
    unlocked_titles = check_and_update_titles(user_id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    kills = user_data.get("kills", 0)
    battles = user_data.get("battles_played", 0)
    
    embed = discord.Embed(title="📜 الملف الشخصي للمقاتل", color=discord.Color.dark_gold())
    embed.add_field(name="اللقب الحالي", value=f"`{custom_title}`", inline=False)
    embed.add_field(name="الأرصدة", value=f"`{balance:,}` 🪙 | `💎 {diamonds:,}`", inline=False)
    embed.add_field(name="الإحصائيات", value=f"🗼 أعلى طابق: `{max_floor}`\n⚔️ المعارك: `{battles}`\n💀 القتلات: `{kills}`", inline=False)
    embed.add_field(name="الألقاب المتاحة", value=", ".join([f"`{t}`" for t in unlocked_titles]), inline=False)
    
    view = ProfileView(interaction.user.id, unlocked_titles)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="بنك", description="فتح الحساب البنكي")
async def bank_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    bal = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    
    embed = discord.Embed(title="🏦 البنك المركزي", description=f"رصيدك الحالي: `{bal:,}` 🪙\nالألماس: `{diamonds:,}` 💎", color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى")
async def battle_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not users_col.find_one({"user_id": user_id}):
        return await interaction.response.send_message("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    embed = discord.Embed(title="🏟️ ساحة المعارك", description="اختر نوع التحدي من القائمة:", color=discord.Color.dark_gold())
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(DISCORD_TOKEN)
