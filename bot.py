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

# ================== نظام الألعاب الجماعية (الأسئلة التلقائية) ==================
class TriviaQuestionView(discord.ui.View):
    def __init__(self, difficulty, questions_list, author_id, players, message=None):
        super().__init__(timeout=300)
        self.difficulty = difficulty
        self.questions_list = questions_list
        self.author_id = author_id
        self.players = players
        self.message = message
        self.is_running = True
        bot.loop.create_task(self.auto_questions_loop())

    async def auto_questions_loop(self):
        try:
            while self.is_running:
                await asyncio.sleep(15)
                if not self.is_running:
                    break
                
                current_q = random.choice(self.questions_list)
                selected_responder = random.choice(self.players)
                players_mention = ", ".join([f"<@{p}>" for p in self.players])
                
                embed = discord.Embed(
                    title=f"🧠 لعبة الأسئلة الجماعية (مستوى: {self.difficulty})",
                    description=f"**اللاعبون المشاركون:** {players_mention}\n\n🎯 **المكلف بالإجابة عشوائياً:** <@{selected_responder}>\n\n**السؤال:**\n{current_q}",
                    color=discord.Color.purple()
                )
                
                if self.message:
                    try:
                        await self.message.edit(embed=embed, view=self)
                    except discord.HTTPException:
                        break
        except asyncio.CancelledError:
            pass

    @discord.ui.button(label="إيقاف اللعبة 🛑", style=discord.ButtonStyle.danger)
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id and interaction.user.id not in self.players:
            return await interaction.response.send_message("❌ ليس لديك صلاحية لإيقاف هذه اللعبة!", ephemeral=True)
        
        self.is_running = False
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
            description=f"اضغط على زر **انضمام للعبة** للمشاركة!\n\n**اللاعبون المسجلون ({len(self.players)}):**\n{players_mention}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="بدء اللعبة ▶️", style=discord.ButtonStyle.primary)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ فقط منشئ اللعبة يمكنه بدءها!", ephemeral=True)
        if len(self.players) < 2:
            return await interaction.response.send_message("❌ لا يمكن بدء اللعبة إلا إذا انضم شخصان على الأقل!", ephemeral=True)
        
        q_list = TRIVIA_QUESTIONS.get(self.difficulty, TRIVIA_QUESTIONS["عادي"])
        selected_q = random.choice(q_list)
        selected_responder = random.choice(self.players)
        
        players_mention = ", ".join([f"<@{p}>" for p in self.players])
        embed = discord.Embed(
            title=f"🧠 لعبة الأسئلة الجماعية (مستوى: {self.difficulty})",
            description=f"**اللاعبون المشاركون:** {players_mention}\n\n🎯 **المكلف بالإجابة عشوائياً:** <@{selected_responder}>\n\n**السؤال:**\n{selected_q}",
            color=discord.Color.purple()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        msg = await interaction.original_response()
        
        view = TriviaQuestionView(self.difficulty, q_list, self.author_id, self.players, message=msg)
        await msg.edit(view=view)

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
            description=f"اضغط على زر **انضمام للعبة** للمشاركة!\n\n**اللاعبون المسجلون (1):**\n<@{self.author_id}>",
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

# ================== نظام معارك اللاعبين ==================
class PvPLobbyView(discord.ui.View):
    def __init__(self, mode, author_id):
        super().__init__(timeout=180)
        self.mode = mode
        self.author_id = author_id
        self.players = [author_id]
        
        if mode == "1v1":
            self.required_players = 2
        elif mode == "2v2":
            self.required_players = 4
        elif mode == "3v3":
            self.required_players = 6
        else:
            self.required_players = 2

    @discord.ui.button(label="انضمام للمعركة ⚔️", style=discord.ButtonStyle.green)
    async def join_pvp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            return await interaction.response.send_message("❌ أنت منضم بالفعل في هذه المعركة!", ephemeral=True)
        
        self.players.append(interaction.user.id)
        players_mention = ", ".join([f"<@{p}>" for p in self.players])
        
        if len(self.players) >= self.required_players:
            self.stop()
            half = len(self.players) // 2
            team1 = self.players[:half]
            team2 = self.players[half:]
            
            t1_str = ", ".join([f"<@{p}>" for p in team1])
            t2_str = ", ".join([f"<@{p}>" for p in team2])
            
            embed = discord.Embed(
                title=f"🔥 اكتمل العدد! انطلاق معركة {self.mode} التلقائية",
                description=f"**الفريق الأول:** {t1_str}\nVS\n**الفريق الثاني:** {t2_str}\n\n⚔️ **تبدأ المعركة تلقائياً الآن... استعدوا!**",
                color=discord.Color.dark_red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            
            msg = interaction.message
            t1_hp, t2_hp = 100, 100
            
            while t1_hp > 0 and t2_hp > 0:
                await asyncio.sleep(3)
                dmg1 = random.randint(15, 30)
                t2_hp = max(0, t2_hp - dmg1)
                
                embed.description = f"**الفريق الأول:** {t1_str} (دمه: {t1_hp})\nVS\n**الفريق الثاني:** {t2_str} (دمه: {t2_hp})\n\n💥 **هجوم الفريق الأول!** أحدث ضرر بقيمة `{dmg1}`."
                await msg.edit(embed=embed)
                
                if t2_hp <= 0:
                    break
                    
                await asyncio.sleep(3)
                dmg2 = random.randint(15, 30)
                t1_hp = max(0, t1_hp - dmg2)
                
                embed.description = f"**الفريق الأول:** {t1_str} (دمه: {t1_hp})\nVS\n**الفريق الثاني:** {t2_str} (دمه: {t2_hp})\n\n💥 **رد الفريق الثاني!** أحدث ضرر بقيمة `{dmg2}`."
                await msg.edit(embed=embed)
            
            winner = "الفريق الأول 🏆" if t2_hp <= 0 else "الفريق الثاني 🏆"
            final_embed = discord.Embed(
                title="🏆 انتهت المعركة التلقائية!",
                description=f"لقد انتهت المواجهة بفوز **{winner}** بعد تبادل الضربات بقوة!\n\n👑 الف مبروك للفائزين!",
                color=discord.Color.gold()
            )
            return await msg.edit(embed=final_embed)

        embed = discord.Embed(
            title=f"🛡️ غرفة انتظار معركة {self.mode}",
            description=f"بانتظار اكتمال اللاعبين ({len(self.players)}/{self.required_players})...\n\n**المشاركون حتى الآن:**\n{players_mention}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)

# ================== نظام معارك الطوابق والقتال التفاعلي ==================
class FloorFightView(discord.ui.View):
    def __init__(self, user_id, target_floor, player_hp, monster_hp, monster_name):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.target_floor = target_floor
        self.player_hp = player_hp
        self.monster_hp = monster_hp
        self.monster_name = monster_name

    @discord.ui.button(label="⚔️ هجوم", style=discord.ButtonStyle.danger)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه المعركة ليست لك!", ephemeral=True)
        
        p_dmg = random.randint(20, 40)
        m_dmg = random.randint(10, 30 + (self.target_floor // 20))
        
        self.monster_hp = max(0, self.monster_hp - p_dmg)
        if self.monster_hp > 0:
            self.player_hp = max(0, self.player_hp - m_dmg)

        if self.monster_hp <= 0:
            users_col.update_one({"user_id": str(self.user_id)}, {"$max": {"max_floor": self.target_floor}, "$inc": {"balance": self.target_floor * 50}})
            embed = discord.Embed(
                title=f"🎉 تم انتصارك في الطابق {self.target_floor}!",
                description=f"🏆 لقد قتلت **{self.monster_name}** بنجاح!\n💰 حصلت على مكافأة مالية وهبطت في السجل برقم طابق أعلى.",
                color=discord.Color.gold()
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        if self.player_hp <= 0:
            embed = discord.Embed(
                title="💀 هزيمة نكراء!",
                description=f"لقد سحقتك قوة **{self.monster_name}** في الطابق {self.target_floor}. حاول تطوير عتادك أولاً!",
                color=discord.Color.dark_red()
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        embed = discord.Embed(
            title=f"🗼 معركة الطابق {self.target_floor} ضد {self.monster_name}",
            description=f"🩸 هجمت وأحدثت ضرر بقيمة `{p_dmg}`!\n🩸 رد الوحش بهجوم وأحدث ضرر بقيمة `{m_dmg}`!\n\n🛡️ **دمك:** `{self.player_hp}/100`\n👹 **دم الوحش:** `{self.monster_hp}`",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)

class FloorLobbyView(discord.ui.View):
    def __init__(self, user_id, current_floor):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.current_floor = current_floor

    @discord.ui.button(label="⚔️ ابدأ المواجهة والصعود", style=discord.ButtonStyle.danger, emoji="🔥")
    async def start_fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
        
        next_floor = min(500, self.current_floor + 1)
        monster_names = ["حارس البوابات الظلامي", "عملاق الحمم البركانية", "تنين الأبراج الأسطوري", "سيد الظلال المرعب"]
        m_name = random.choice(monster_names)
        m_hp = 100 + (next_floor * 5)
        
        embed = discord.Embed(
            title=f"🗼 المعركة المشتعلة - الطابق {next_floor}",
            description=f"👹 ظهر **{m_name}** في وجهك!\n\n🛡️ **دمك:** `100/100`\n👹 **دم الوحش:** `{m_hp}/{m_hp}`\n\nاضغط على **هجوم** لتوجيه ضربتك القاضية!",
            color=discord.Color.dark_red()
        )
        view = FloorFightView(self.user_id, next_floor, 100, m_hp, m_name)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="المتجر 🛒", style=discord.ButtonStyle.secondary)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
        await interaction.response.send_message("🛒 **المتجر العام:** قريباً سيتم توفير الأسلحة والدروع للشراء بالعملات!", ephemeral=True)

    @discord.ui.button(label="تطوير العتاد 🛠️", style=discord.ButtonStyle.secondary)
    async def upgrade_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
        await interaction.response.send_message("🛠️ **منطقة تطوير العتاد:** استخدم أرباحك لترقية سيوفك ودروعك لتتحمل الطوابق العليا!", ephemeral=True)

    @discord.ui.button(label="الحقيبة 🎒", style=discord.ButtonStyle.secondary)
    async def inventory_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
        await interaction.response.send_message("🎒 **حقيبتك:** تحتوي على الألماس والمكتسبات الحالية.", ephemeral=True)

class BattleModeSelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="مبارزة 1v1", description="معركة فردية وجهاً لوجه", emoji="⚔️", value="1v1"),
            discord.SelectOption(label="مبارزة 2v2", description="معركة جماعية ثنائية", emoji="🛡️", value="2v2"),
            discord.SelectOption(label="مبارزة 3v3", description="معركة ثلاثية كبرى", emoji="🔥", value="3v3"),
            discord.SelectOption(label="نظام الطوابق (حتى 500)", description="تصاعد المستويات والأبراج القتالية", emoji="🗼", value="floors")
        ]
        super().__init__(placeholder="اختر نمط المعركة أو الطابق المطلوب...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        
        if choice in ["1v1", "2v2", "3v3"]:
            embed = discord.Embed(
                title=f"🛡️ غرفة انتظار معركة {choice}",
                description=f"فتح المنشئ <@{self.author_id}> غرفة التحدي!\nاضغط على زر **انضمام للمعركة** للمشاركة.\n\n**المشاركون (1):**\n<@{self.author_id}>",
                color=discord.Color.blue()
            )
            view = PvPLobbyView(choice, self.author_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
            
        elif choice == "floors":
            user_id = str(interaction.user.id)
            user_data = users_col.find_one({"user_id": user_id})
            current_floor = user_data.get("max_floor", 0) if user_data else 0
            
            embed = discord.Embed(
                title="🗼 برج المعارك الأسطوري (إلى طابق 500)",
                description=f"أهلاً بك في نظام الطوابق التصاعدي.\nأعلى طابق وصلته حالياً: **{current_floor} / 500**\n\nاختر من الأزرار أدناه للبدء بالمواجهة أو استعراض عتادك والمتجر:",
                color=discord.Color.dark_orange()
            )
            view = FloorLobbyView(interaction.user.id, current_floor)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class BattleMenuView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.add_item(BattleModeSelect(author_id))

@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى وأنماط التحدي والطوابق")
async def battle_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not users_col.find_one({"user_id": user_id}):
        return await interaction.response.send_message("❌ لم تقم بالتسجيل بعد! استخدم أمر `/تسجيل` أولاً.", ephemeral=True)
        
    embed = discord.Embed(
        title="🏟️ ساحة المعارك الكبرى والأبراج",
        description="اختر نمط القتال أو الطوابق المفضلة لديك من القائمة أدناه لتشتعل المنافسة مباشرة في الروم:",
        color=discord.Color.dark_gold()
    )
    view = BattleMenuView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ================== منيو اختيار الألقاب السريعة للمطور ==================
class DevGiveTitleSelect(discord.ui.Select):
    def __init__(self):
        titles = [
            ("المبتدئ", "🟢"), ("الامبراطور", "👑"), ("الملك", "🔱"), 
            ("الغني", "💰"), ("القاتل", "🗡️"), ("السفاح", "🩸"), 
            ("اسطورة القتال", "⚡"), ("اقوى الاقوياء", "🔥")
        ]
        options = [discord.SelectOption(label=t[0], value=t[0], emoji=t[1]) for t in titles]
        super().__init__(placeholder="اختر اللقب الذي تريد فتحه ومنحه لنفسك...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen_title = self.values[0]
        user_id = str(interaction.user.id)
        
        user_data = users_col.find_one({"user_id": user_id})
        if not user_data:
            users_col.insert_one({
                "user_id": user_id, "balance": 1000, "diamonds": 10, 
                "max_floor": 0, "kills": 0, "battles_played": 0, "power": 100, 
                "custom_title": chosen_title, "unlocked_titles": ["المبتدئ", chosen_title], "inventory": []
            })
        else:
            unlocked = user_data.get("unlocked_titles", ["المبتدئ"])
            if chosen_title not in unlocked:
                unlocked.append(chosen_title)
            users_col.update_one({"user_id": user_id}, {"$set": {"custom_title": chosen_title, "unlocked_titles": unlocked}})
            
        await interaction.response.send_message(f"👑 **تم فتح وتفعيل اللقب الأسطوري بنجاح:** `{chosen_title}` في سجلك الشخصي!", ephemeral=True)

class DevGiveTitleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(DevGiveTitleSelect())

# ================== نظام إدارة العتاد الذكي للمطورين ==================
class GearSelect(discord.ui.Select):
    def __init__(self, target_user_id, action_type, shop_type):
        self.target_id = target_user_id
        self.action_type = action_type
        
        # أسلحة المتجر المظلم (الأسطورية)
        if shop_type == "dark":
            options = [
                discord.SelectOption(label="سيف التنين الأسطوري", emoji="🔥", value="سيف التنين الأسطوري"),
                discord.SelectOption(label="درع الظلام", emoji="🌑", value="درع الظلام"),
                discord.SelectOption(label="خنجر السموم", emoji="🐍", value="خنجر السموم"),
                discord.SelectOption(label="فأس الجحيم", emoji="🪓", value="فأس الجحيم")
            ]
        # أسلحة المتجر العادي
        else:
            options = [
                discord.SelectOption(label="سيف حديدي", emoji="⚔️", value="سيف حديدي"),
                discord.SelectOption(label="درع فولاذي", emoji="🛡️", value="درع فولاذي"),
                discord.SelectOption(label="قوس الرماية", emoji="🏹", value="قوس الرماية"),
                discord.SelectOption(label="خوذة الفرسان", emoji="⛑️", value="خوذة الفرسان")
            ]

        super().__init__(placeholder="اختر العتاد أو السلاح من القائمة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        gear = self.values[0]
        user_data = users_col.find_one({"user_id": self.target_id})
        
        if not user_data:
            return await interaction.response.send_message("❌ هذا المستخدم غير مسجل في قاعدة البيانات!", ephemeral=True)
        
        inv = user_data.get("inventory", [])
        
        if self.action_type == "add":
            if gear not in inv:
                inv.append(gear)
            users_col.update_one({"user_id": self.target_id}, {"$set": {"inventory": inv}})
            await interaction.response.edit_message(content=f"⚔️ **تم منح العتاد `{gear}` بنجاح للمقاتل <@{self.target_id}>!**", view=None)
        else:
            if gear in inv:
                inv.remove(gear)
            users_col.update_one({"user_id": self.target_id}, {"$set": {"inventory": inv}})
            await interaction.response.edit_message(content=f"🛡️ **تم سحب العتاد `{gear}` من المقاتل <@{self.target_id}> بنجاح!**", view=None)

class ShopActionView(discord.ui.View):
    def __init__(self, target_user_id):
        super().__init__(timeout=180)
        self.target_id = target_user_id
    
    @discord.ui.button(label="منح عتاد (متجر عادي) ⚔️", style=discord.ButtonStyle.primary, row=0)
    async def add_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        view.add_item(GearSelect(self.target_id, "add", "normal"))
        await interaction.response.edit_message(content="**اختر العتاد العادي المراد إعطائه للاعب:**", view=view)

    @discord.ui.button(label="منح عتاد (متجر مظلم) 🌑", style=discord.ButtonStyle.danger, row=0)
    async def add_dark(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        view.add_item(GearSelect(self.target_id, "add", "dark"))
        await interaction.response.edit_message(content="**اختر العتاد المظلم والأسطوري المراد إعطائه للاعب:**", view=view)
        
    @discord.ui.button(label="سحب عتاد (عادي) 🗑️", style=discord.ButtonStyle.secondary, row=1)
    async def rem_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        view.add_item(GearSelect(self.target_id, "remove", "normal"))
        await interaction.response.edit_message(content="**اختر العتاد العادي المراد سحبه من اللاعب:**", view=view)

    @discord.ui.button(label="سحب عتاد (مظلم) 🗑️", style=discord.ButtonStyle.secondary, row=1)
    async def rem_dark(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()
        view.add_item(GearSelect(self.target_id, "remove", "dark"))
        await interaction.response.edit_message(content="**اختر العتاد المظلم المراد سحبه من اللاعب:**", view=view)

# ================== نظام لوحة المطورين الشاملة والمؤتمتة ==================
class DeveloperControlView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_developer(interaction.user.id):
            await interaction.response.send_message("❌ عذراً، هذه اللوحة مخصصة للمطورين فقط ولا يمكنك العبث بها!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="إضافة عملات لا نهائية 🪙", style=discord.ButtonStyle.success, row=0)
    async def add_infinite_money(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": 999999999}}, upsert=True)
        await interaction.response.send_message("💰 **تم إضافة ثروة طائلة لا نهائية إلى خزنتك بنجاح!**", ephemeral=True)

    @discord.ui.button(label="إضافة ألماس لا نهائي 💎", style=discord.ButtonStyle.success, row=0)
    async def add_infinite_diamonds(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": 999999}}, upsert=True)
        await interaction.response.send_message("💎 **تم إضافة مخزون ضخم من الألماس النادر إلى حسابك!**", ephemeral=True)

    @discord.ui.button(label="الألقاب الأسطورية 👑", style=discord.ButtonStyle.success, row=0)
    async def get_any_title_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 اختيار الألقاب الإمبراطورية الفورية",
            description="اختر من القائمة أدناه أي لقب ترغب في الحصول عليه وتفعيله فوراً في ملفك الشخصي:",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=DevGiveTitleView(), ephemeral=True)

    @discord.ui.button(label="إضافة مطور جديد ⚡", style=discord.ButtonStyle.blurple, row=1)
    async def add_dev_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        class DevModal(discord.ui.Modal, title="إضافة مطور جديد للنظام"):
            target_user = discord.ui.TextInput(label="منشن العضو (أو الأيدي)", placeholder="مثال: @Username", required=True)
            
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    uid = extract_user_id(self.target_user.value)
                    devs_col.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
                    await interaction.response.send_message(f"👑 **تم ترقية العضو <@{uid}> ليصبح مطوراً رسمياً في النظام!** (سيظهر له أمر `/المطور` الآن)", ephemeral=True)
                except Exception:
                    await interaction.response.send_message("❌ الصيغة المدخلة غير صحيحة! تأكد من منشن العضو بشكل صحيح.", ephemeral=True)

        await interaction.response.send_modal(DevModal())

    @discord.ui.button(label="إزالة مطور 🗑️", style=discord.ButtonStyle.danger, row=1)
    async def remove_dev_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        class RemoveDevModal(discord.ui.Modal, title="إزالة مطور من النظام"):
            target_user = discord.ui.TextInput(label="منشن العضو المراد إزالته", placeholder="مثال: @Username", required=True)
            
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    uid = extract_user_id(self.target_user.value)
                    
                    if int(uid) == OWNER_ID:
                        return await interaction.response.send_message("❌ لا يمكنك إزالة المالك الأساسي (أنت) من قائمة المطورين!", ephemeral=True)
                    
                    result = devs_col.delete_one({"user_id": uid})
                    if result.deleted_count > 0:
                        await interaction.response.send_message(f"🗑️ **تمت إزالة العضو <@{uid}> من قائمة المطورين بنجاح!**", ephemeral=True)
                    else:
                        await interaction.response.send_message("❌ هذا المستخدم ليس مدرجاً في قائمة المطورين الإضافيين.", ephemeral=True)
                except Exception:
                    await interaction.response.send_message("❌ الصيغة المدخلة غير صحيحة! تأكد من منشن العضو بشكل صحيح.", ephemeral=True)

        await interaction.response.send_modal(RemoveDevModal())

    @discord.ui.button(label="تحويل عملات لشخص 💸", style=discord.ButtonStyle.blurple, row=2)
    async def transfer_money_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        class TransferModal(discord.ui.Modal, title="تحويل عملات بالمنشن"):
            target = discord.ui.TextInput(label="منشن العضو المراد التحويل له", placeholder="مثال: @Username", required=True)
            amount = discord.ui.TextInput(label="المبلغ المراد تحويله", placeholder="مثال: 50000", required=True)
            
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    raw_target = extract_user_id(self.target.value)
                    amt = int(self.amount.value.strip())
                    
                    target_data = users_col.find_one({"user_id": raw_target})
                    if not target_data:
                        users_col.insert_one({"user_id": raw_target, "balance": amt, "diamonds": 10, "max_floor": 0, "kills": 0, "battles_played": 0, "power": 100, "custom_title": "المبتدئ", "unlocked_titles": ["المبتدئ"], "inventory": []})
                    else:
                        users_col.update_one({"user_id": raw_target}, {"$inc": {"balance": amt}})
                        
                    await interaction.response.send_message(f"💸 **تم تحويل مبلغ `{amt:,}` 🪙 بنجاح إلى حساب العضو <@{raw_target}>!**", ephemeral=True)
                except Exception:
                    await interaction.response.send_message("❌ حدث خطأ في البيانات المدخلة، تأكد من منشن العضو وكتابة رقم صحيح للمبلغ.", ephemeral=True)

        await interaction.response.send_modal(TransferModal())

    @discord.ui.button(label="إدارة عتاد اللاعب ⚔️", style=discord.ButtonStyle.danger, row=2)
    async def manage_gear_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        class TargetUserModal(discord.ui.Modal, title="إدارة عتاد المقاتل"):
            target = discord.ui.TextInput(label="منشن اللاعب المستهدف", placeholder="مثال: @Username", required=True)
            
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    raw_target = extract_user_id(self.target.value)
                    
                    user_data = users_col.find_one({"user_id": raw_target})
                    if not user_data:
                        return await interaction.response.send_message("❌ هذا المستخدم غير مسجل في قاعدة البيانات!", ephemeral=True)
                    
                    view = ShopActionView(raw_target)
                    await interaction.response.send_message(
                        f"⚙️ **إدارة عتاد اللاعب <@{raw_target}>**\nيرجى اختيار المتجر ونوع العملية من الأزرار بالأسفل:", 
                        view=view, 
                        ephemeral=True
                    )
                except Exception:
                    await interaction.response.send_message("❌ حدث خطأ، تأكد من منشن العضو بشكل صحيح.", ephemeral=True)

        await interaction.response.send_modal(TargetUserModal())

# أمر المطور المخفي (لا يظهر في اقتراحات الأوامر العامة نهائياً إلا لك أو للمطورين المضافين)
@bot.tree.command(name="المطور", description="لوحة التحكم الإمبراطورية الخاصة بالمطورين وسلطات النظام العليا")
async def developer_panel(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        return await interaction.response.send_message("❌ هذا الأمر غير موجود.", ephemeral=True)
    
    registered_commands = [cmd.name for cmd in bot.tree.get_commands()]
    commands_list_str = " • ".join([f"`/{c}`" for c in registered_commands])
    
    embed = discord.Embed(
        title="👑 قاعة التحكم العليا وإدارة المطورين ⚡",
        description=(
            "✨ *«أهلاً بك أيها المطور العظيم في قلب النظام المركزي. من هنا تستطيع إدارة كل صغيرة وكبيرة في عالم المقاتلين والأبراج، وتوجيه مقاليد السلطة والثروات بلمسة زر واحدة.»*\n\n"
            "🛡️ **صلاحياتك المطلقة المتاحة في هذه اللوحة:**\n"
            "• ضخ كميات لا نهائية من العملات النقدية والألماس النادر.\n"
            "• اختيار وفتح أي لقب أسطوري فوراً لنفسك عبر منيو الألقاب.\n"
            "• ترقية وإضافة مطورين جدد لدعم إدارة النظام بالمنشن الفوري.\n"
            "• إزالة المطورين غير المرغوب بهم من لوحة التحكم بالمنشن.\n"
            "• تحويل الأموال والأرصدة الفورية لأي مقاتل عبر منشنه.\n"
            "• حقيبة الأسلحة والعتاد: اختيار المتجر المظلم أو العادي لمنح وسحب الأسلحة.\n\n"
            f"📋 **قائمة الأوامر الفعالة والمضافة حديثاً في النظام:**\n{commands_list_str}"
        ),
        color=discord.Color.from_rgb(138, 43, 226)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="نظام الإدارة المركزية • مؤتمت بشكل تلقائي بالكامل", icon_url=bot.user.display_avatar.url)
    
    view = DeveloperControlView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ================== بقية الأوامر الأساسية ==================
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
    def __init__(self, unlocked_titles, author_id):
        self.author_id = author_id
        title_emojis = {
            "المبتدئ": "🟢", "الامبراطور": "👑", "الملك": "🔱", "الغني": "💰",
            "القاتل": "🗡️", "السفاح": "🩸", "اسطورة القتال": "⚡", "اقوى الاقوياء": "🔥"
        }
        options = [discord.SelectOption(label=t, value=t, emoji=title_emojis.get(t, "✨")) for t in unlocked_titles]
        super().__init__(placeholder="اختر لقباً من ألقابك المتاحة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ هذه القائمة ليست لك ولا يمكنك تعديل لقب صاحب الملف!", ephemeral=True)
            
        selected_title = self.values[0]
        users_col.update_one({"user_id": str(interaction.user.id)}, {"$set": {"custom_title": selected_title}})
        await interaction.response.edit_message(content=f"✨ **تم تفعيل لقبك الجديد بنجاح:** `{selected_title}`", view=None)

class ProfileView(discord.ui.View):
    def __init__(self, author_id, unlocked_titles):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.unlocked_titles = unlocked_titles

    @discord.ui.button(label="تغيير اللقب الملكي 👑", style=discord.ButtonStyle.blurple)
    async def change_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ هذه الأزرار خاصة بصاحب الملف فقط! لا يمكنك العبث بها.", ephemeral=True)
            
        view = discord.ui.View()
        view.add_item(TitleSelect(self.unlocked_titles, self.author_id))
        await interaction.response.send_message("📌 الألقاب الأسطورية المتاحة لك بناءً على إنجازاتك الكبرى:", view=view, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ عذراً، هذه القائمة تخص مقاتلاً آخر ولا يمكنك تفاعلك مع أزرارها!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="الملف", description="عرض الملف الشخصي الأسطوري للعامة مع تفاصيل وإحصائيات ضخمة")
async def profile_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    user_id = str(interaction.user.id)
    
    unlocked_titles = check_and_update_titles(user_id)
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        return await interaction.followup.send("❌ لم تقم بالتسجيل بعد في سجلات المقاتلين! استخدم أمر `/تسجيل` أولاً.", ephemeral=False)
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "المبتدئ")
    max_floor = user_data.get("max_floor", 0)
    kills = user_data.get("kills", 0)
    battles = user_data.get("battles_played", 0)
    power = user_data.get("power", 100)
    
    embed = discord.Embed(
        title=f"⚔️ السجل الأسطوري للمقاتل: {interaction.user.display_name} 🛡️",
        description="*«هنا تُدون إنجازات الأبطال، وتُقاس القوى في ساحات الشرف والأبراج المظلمة. هذا السجل يعكس مسيرة مقاتل عظيم سطر اسمه في تاريخ السيرفر بحروف من نور ونار.»*",
        color=discord.Color.from_rgb(212, 175, 55)
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    yaml_box = "```yaml\n" + custom_title + "\n```"
    embed.add_field(
        name="👑 الرتبة واللقب الحالي",
        value=yaml_box,
        inline=False
    )
    embed.add_field(
        name="💰 الخزينة والثروة الإمبراطورية",
        value=f"• **العملات النقدية:** `{balance:,}` 🪙\n• **الألماس النادر:** `{diamonds:,}` 💎\n• **الحالة الاقتصادية:** `مستقرة ومزدهرة`",
        inline=True
    )
    embed.add_field(
        name="⚡ مؤشرات القوة القتالية",
        value=f"• **مستوى الطاقة:** `{power:,}` ⚡\n• **المعارك المحسومة:** `{battles:,}` ⚔️\n• **عدد الخصوم المقضي عليهم:** `{kills:,}` 💀",
        inline=True
    )
    embed.add_field(
        name="🗼 إنجازات برج المعارك الأسطوري",
        value=f"• **أعلى طابق تم اجتيازه:** `{max_floor} / 500` طابق 🗼\n• **نسبة الإنجاز في الأبراج:** `{(max_floor / 500) * 100:.1f}%` 📊",
        inline=False
    )
    
    titles_display = ", ".join([f"`{t}`" for t in unlocked_titles])
    embed.add_field(
        name="✨ الألقاب الأسطورية المفتوحة في سجلك",
        value=f"{titles_display}\n*استمر في خوض التحديات الكبرى وصعود الطوابق لفتح المزيد من الألقاب السرية الفخمة!*",
        inline=False
    )
    
    embed.set_footer(text=f"طلب بواسطة البطل: {interaction.user.name} • نظام السجلات الموحد", icon_url=interaction.client.user.display_avatar.url)
    
    view = ProfileView(interaction.user.id, unlocked_titles)
    await interaction.followup.send(embed=embed, view=view, ephemeral=False)

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

bot.run(DISCORD_TOKEN)
