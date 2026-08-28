import os
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DEVELOPER_ID = 1103985971638325269

# ملف الحفظ التلقائي للبيانات
DB_FILE = "database.json"

# تحميل البيانات عند بدء البوت
def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # تحويل مفاتيح الأيدي من نص إلى أرقام صحيحة
                return {
                    "economy": {int(k): v for k, v in data.get("economy", {}).items()},
                    "stats": {int(k): v for k, v in data.get("stats", {}).items()},
                    "equipped": {int(k): v for k, v in data.get("equipped", {}).items()},
                    "devs": set(data.get("devs", []))
                }
        except Exception as e:
            print(f"❌ خطأ أثناء قراءة ملف الحفظ: {e}")
    return {"economy": {}, "stats": {}, "equipped": {}, "devs": set()}

# حفظ البيانات مباشرة في الملف
def save_database():
    data = {
        "economy": {str(k): v for k, v in USER_ECONOMY.items()},
        "stats": {str(k): v for k, v in USER_STATS.items()},
        "equipped": {str(k): v for k, v in USER_EQUIPPED.items()},
        "devs": list(EXTRA_DEVS)
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ البيانات: {e}")

# استيراد البيانات الحالية
db = load_database()
USER_ECONOMY = db["economy"]
USER_STATS = db["stats"]
USER_EQUIPPED = db["equipped"]
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

# ==================== بيانات المعدات وشخصيات المحاربين ====================
ITEMS_DATA = {
    "سيف حديدي بسيط": {
        "price": 100, "type": "عادي", 
        "char_image": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800", 
        "desc": "سيف تقليدي حاد ومناسب للمبتدئين."
    },
    "درع خشبي متين": {
        "price": 150, "type": "عادي", 
        "char_image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800", 
        "desc": "درع من الخشب المقوى لحماية أساسية."
    },
    "خنجر الصياد السريع": {
        "price": 200, "type": "عادي", 
        "char_image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=800", 
        "desc": "خنجر خفيف للطعنات السريعة."
    },
    "قوس الخشب القديم": {
        "price": 250, "type": "عادي", 
        "char_image": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800", 
        "desc": "قوس بدائي للهجوم عن بعد."
    },
    "رمح الحراس": {
        "price": 300, "type": "عادي", 
        "char_image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800", 
        "desc": "رمح طويل يحافظ على مسافة آمنة."
    },
    "نصل الجحيم المحرق": {
        "price": 1200, "type": "🔥 رتبة الجحيم", 
        "char_image": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800", 
        "desc": "سيف أسطوري مشتعل بنيران الحمم البركانية الحارقة."
    },
    "مطرقة الجحيم العملاقة": {
        "price": 2000, "type": "🔥 رتبة الجحيم", 
        "char_image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800", 
        "desc": "مطرقة جحيمية ثقيلة تحطم أي درع بضربة واحدة."
    },
    "خنجر الشيطان الدموي": {
        "price": 1600, "type": "🖤 رتبة الشيطان", 
        "char_image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=800", 
        "desc": "خنجر شيطاني مسكون بلعنة الظلام وسرعة مرعبة."
    },
    "سيف الشيطان الأبدي": {
        "price": 2800, "type": "🖤 رتبة الشيطان", 
        "char_image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800", 
        "desc": "سيف مرعب وفخم للغاية ينبض بطاقة الشيطان."
    },
    "صولجان الخراب المظلم": {
        "price": 3500, "type": "🖤 رتبة الشيطان", 
        "char_image": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800", 
        "desc": "سلاح الدمار الشامل لسيطرة مطلقة على العوالم."
    },
}

# ==================== المتجر والحقيبة ====================

class NormalShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🛒 اختر السلاح العادي لعرض شخصيته وشرائه...",
        options=[discord.SelectOption(label=name, description=f"السعر: {data['price']} عملة | النوع: {data['type']}", value=name) for name, data in list(ITEMS_DATA.items())[:5]]
    )
    async def select_item(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_name = select.values[0]
        item = ITEMS_DATA[item_name]
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item["price"]:
            await interaction.response.send_message(f"❌ رصيدك غير كافي! تحتاج إلى `{item['price']}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item["price"]
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        save_database()
        
        embed = discord.Embed(title=f"✅ تم شراء ({item_name}) بنجاح!", description=item["desc"], color=0x3498DB)
        embed.set_image(url=item["char_image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DarkShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="🌑 اختر معدات الجحيم لعرض المحارب المرعب وشرائه...",
        options=[discord.SelectOption(label=name, description=f"السعر: {data['price']} | {data['type']}", value=name) for name, data in list(ITEMS_DATA.items())[5:]]
    )
    async def select_dark_item(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_name = select.values[0]
        item = ITEMS_DATA[item_name]
        
        eco = get_user_economy(interaction.user.id)
        if eco["coins"] < item["price"]:
            await interaction.response.send_message(f"❌ رصيدك لا يكفي لشراء عتاد ({item['type']})! تحتاج إلى `{item['price']}` عملة.", ephemeral=True)
            return
            
        eco["coins"] -= item["price"]
        stats = get_user_stats(interaction.user.id)
        stats[item_name] = stats.get(item_name, 0) + 1
        save_database()
        
        embed = discord.Embed(title=f"🔥 تم اقتناء ({item_name}) بنجاح!", description=f"**الرتبة:** {item['type']}\n{item['desc']}", color=0x8E44AD)
        embed.set_image(url=item["char_image"])
        embed.add_field(name="💰 رصيدك الباقي:", value=f"`{eco['coins']}` عملة")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class InventoryEquipView(discord.ui.View):
    def __init__(self, user_stats_dict):
        super().__init__(timeout=60)
        self.user_stats_dict = user_stats_dict
        
        options = []
        for gear_name in user_stats_dict.keys():
            if gear_name in ITEMS_DATA:
                item = ITEMS_DATA[gear_name]
                options.append(discord.SelectOption(label=gear_name, description=f"الرتبة: {item['type']} | العدد: {user_stats_dict[gear_name]}", value=gear_name))
        
        if not options:
            options.append(discord.SelectOption(label="حقيبتك فارغة تماماً", description="توجه للمتاجر للتسوق أولاً", value="empty"))
            
        self.select_menu.options = options

    @discord.ui.select(placeholder="🎒 اختر سلاحاً من حقيبتك لتركيبه وتجهيزه لشخصيتك...")
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        gear_name = select.values[0]
        if gear_name == "empty":
            await interaction.response.send_message("❌ حقيبتك فارغة! لا توجد معدات لتركيبها.", ephemeral=True)
            return
            
        USER_EQUIPPED[interaction.user.id] = gear_name
        save_database()
        item = ITEMS_DATA[gear_name]
        
        embed = discord.Embed(title="⚔️ تم ارتداء العتاد وتجهيز الشخصية بنجاح!", description=f"لقد ارتدى محاربك **{gear_name}** ({item['type']}). أصبح جاهزاً للقتال!", color=0x2ECC71)
        embed.set_image(url=item["char_image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== نظام حلبة المعارك (1v1, 2v2, 3v3) ====================

class BattleAcceptView(discord.ui.View):
    def __init__(self, challenger, opponents, mode, bet):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponents = opponents # قائمة الخصوم
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
            
        # فحص رصيد الخصم إذا كان هناك رهان
        if self.bet > 0:
            eco = get_user_economy(interaction.user.id)
            if eco["coins"] < self.bet:
                await interaction.response.send_message(f"❌ لا يملك `{interaction.user.display_name}` رصيداً كافياً لتغطية الرهان ({self.bet} عملة)!", ephemeral=True)
                return

        self.accepted_users.add(interaction.user)
        
        if len(self.accepted_users) == len(self.opponents):
            # الجميع وافق، تبدأ المعركة!
            import random
            
            # تحديد الفريق الفائز عشوائياً (الفريق الأول أو الفريق الثاني)
            all_fighters_team1 = [self.challenger] # يمكن توسعتها لاحقاً لفريق
            winning_team = random.choice([1, 2])
            
            total_pot = self.bet * (len(self.opponents) + 1) if self.bet > 0 else 0
            
            if winning_team == 1:
                winner_text = f"👑 الفائز: **{self.challenger.display_name}** وفريقه!"
                if self.bet > 0:
                    get_user_economy(self.challenger.id)["coins"] += total_pot
                    save_database()
                result_embed = discord.Embed(title=f"🏟️ نتائج معركة الحلبة ({self.mode})", description=f"🔥 اشتعلت الحراسة واستطاع البطل حسم النزال ببراعة!\n\n{winner_text}\n💰 الجائزة المكتسبة: `{total_pot}` عملة", color=0xE74C3C)
            else:
                winner_text = f"👑 الفائزون: **الخصوم** بقيادة {', '.join([u.display_name for u in self.opponents])}"
                if self.bet > 0:
                    for op in self.opponents:
                        get_user_economy(op.id)["coins"] += (total_pot // len(self.opponents))
                    save_database()
                result_embed = discord.Embed(title=f"🏟️ نتائج معركة الحلبة ({self.mode})", description=f"🔥 معركة دموية وحامية الوطيس انتهت بانتصار الخصوم!\n\n{winner_text}", color=0xE74C3C)
                
            result_embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800")
            
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=result_embed, view=self)
            self.stop()
        else:
            await interaction.response.send_message(f"✅ تم تسجيل موافقة **{interaction.user.display_name}** بانتظار بقية اللاعبين...", ephemeral=True)


@bot.tree.command(name="المعارك", description="خض معارك حلبة أسطورية بنظام 1v1 أو 2v2 أو 3v3 مع الرهانات")
@app_commands.choices(النمط=[
    app_commands.Choice(name="⚔️ مبارزة فردية (1 ضد 1)", value="1v1"),
    app_commands.Choice(name="🛡️ معركة ثنائية (2 ضد 2)", value="2v2"),
    app_commands.Choice(name="🔥 حرب ثلاثية (3 ضد 3)", value="3v3")
])
@app_commands.describe(
    النمط="اختر نمط المعركة",
    الخصم_الأول="الخصم الأساسي أو الأول",
    الخصم_الثاني="الخصم الثاني (مطلوب لـ 2v2 و 3v3)",
    الخصم_الثالث="الخصم الثالث (مطلوب لـ 3v3 فقط)",
    الرهان="العملات المرەنة عليها (اختياري)"
)
async def battles(
    interaction: discord.Interaction, 
    النمط: app_commands.Choice[str], 
    الخصم_الأول: discord.Member, 
    الخصم_الثاني: discord.Member = None, 
    الخصم_الثالث: discord.Member = None,
    الرهان: int = 0
):
    mode = النمط.value
    opponents = []
    
    # التحقق من صحة اختيار الخصوم حسب النمط
    if mode == "1v1":
        opponents = [الخصم_الأول]
    elif mode == "2v2":
        if not الخصم_الثاني:
            await interaction.response.send_message("❌ نظام 2v2 يتطلب تحديد (الخصم الأول) و (الخصم الثاني)!", ephemeral=True)
            return
        opponents = [الخصم_الأول, الخصم_الثاني]
    elif mode == "3v3":
        if not الخصم_الثاني or not الخصم_الثالث:
            await interaction.response.send_message("❌ نظام 3v3 يتطلب تحديد ثلاثة خصوم!", ephemeral=True)
            return
        opponents = [الخصم_الأول, الخصم_الثاني, الخصم_الثالث]
        
    if interaction.user in opponents or interaction.user == الخصم_الأول:
        await interaction.response.send_message("❌ لا يمكنك تحدي نفسك في الحلبة!", ephemeral=True)
        return

    # فحص رصيد المُتحدي
    if الرهان > 0:
        challenger_eco = get_user_economy(interaction.user.id)
        if challenger_eco["coins"] < الرهان:
            await interaction.response.send_message(f"❌ رصيدك غير كافي لدخول المعركة بهذا الرهان! تحتاج إلى `{الرهان}` عملة.", ephemeral=True)
            return
            
        challenger_eco["coins"] -= الرهان
        save_database()

    opponents_mention = ", ".join([op.mention for op in opponents])
    
    embed = discord.Embed(
        title=f"🏟️ تحدي حلبة المعارك الأسطورية | {mode}",
        description=f"المتحدي البطل: {interaction.user.mention}\n ضد الخصوم: {opponents_mention}\n\n💰 قيمة الرهان لكل مشارك: `{الرهان}` عملة\n\n*(أمامه 30 ثانية للضغط على زر القبول ودخول المعركة!)*",
        color=0xE67E22
    )
    embed.set_image(url="https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800")
    
    view = BattleAcceptView(interaction.user, opponents, mode, الرهان)
    await interaction.response.send_message(content=opponents_mention, embed=embed, view=view)


# ==================== الأوامر الأساسية ====================

@bot.tree.command(name="المتجر_العادي", description="استعرض المتجر العادي وتصفح شخصيات المحاربين بضغطة زر")
async def normal_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر العادي للمعدات", description="اختر من القائمة أدناه لتظهر لك صورة المحارب الذي يرتدي العتاد:", color=0x3498DB)
    embed.set_image(url="https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=NormalShopView(), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="متجر أسلحة ودروع الجحيم والشيطان السرّية الخارقة")
async def dark_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🌑 المتجر المظلم الأسطوري", description="محاربو رتبتي **الجحيم** و **الشيطان** بانتظارك. اختر بحذر:", color=0x8E44AD)
    embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800")
    await interaction.response.send_message(embed=embed, view=DarkShopView(), ephemeral=True)

@bot.tree.command(name="الحقيبة", description="عرض حقيبتك الشخصية وتركيب المعدات لمحاربك")
async def inventory(interaction: discord.Interaction):
    target = interaction.user
    stats = get_user_stats(target.id)
    equipped = USER_EQUIPPED.get(target.id, "لا يوجد سلاح مركب حالياً")
    
    embed = discord.Embed(title=f"🎒 حقيبة المغامر | {target.display_name}", color=0xD4AF37)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="⚔️ العتاد النشط (المُركب على المحارب):", value=f"`{equipped}`", inline=False)
    
    if stats:
        gear_text = "\n".join([f"🔹 **{gear}** (العدد: {count})" for gear, count in stats.items()])
    else:
        gear_text = "حقيبتك فارغة تماماً!"
        
    embed.add_field(name="📦 جميع المعدات المملوكة:", value=gear_text, inline=False)
    
    if stats:
        await interaction.response.send_message(embed=embed, view=InventoryEquipView(stats), ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="الملف", description="عرض ملفك الشخصي وشخصيتك بملابس الدروع والأسلحة المُركبة")
async def profile(interaction: discord.Interaction):
    target = interaction.user
    eco = get_user_economy(target.id)
    equipped = USER_EQUIPPED.get(target.id, None)
    
    embed = discord.Embed(title=f"👑 الملف الشخصي | {target.display_name}", color=0xE67E22)
    
    if equipped and equipped in ITEMS_DATA:
        item = ITEMS_DATA[equipped]
        embed.set_image(url=item["char_image"])
        equipped_text = f"🛡️ **{equipped}** ({item['type']})"
    else:
        equipped_text = "لا يوجد سلاح مركب حالياً (توجه للحقيبة للتركيب)"
        embed.set_thumbnail(url=target.display_avatar.url)
        
    embed.add_field(name="💰 رصيد العملات:", value=f"`{eco['coins']}` عملة", inline=False)
    embed.add_field(name="⚔️ شخصية المحارب (العتاد المُرتدى):", value=equipped_text, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# لوحة المطور
class DevGearSelect(discord.ui.View):
    def __init__(self, target_member):
        super().__init__(timeout=60)
        self.target_member = target_member

    @discord.ui.select(
        placeholder="⚔️ اختر القطعة المراد إهداؤها...",
        options=[discord.SelectOption(label=name, description=f"النوع: {data['type']} | السعر: {data['price']}", value=name) for name, data in ITEMS_DATA.items()]
    )
    async def select_dev_gear(self, interaction: discord.Interaction, select: discord.ui.Select):
        gear_name = select.values[0]
        stats = get_user_stats(self.target_member.id)
        stats[gear_name] = stats.get(gear_name, 0) + 1
        save_database()
        
        item = ITEMS_DATA[gear_name]
        embed = discord.Embed(title="🛠️ تم إهداء العتاد بواسطة المطور", description=f"تم منح **{gear_name}** إلى العضو {self.target_member.mention} بنجاح!", color=0x2b2d31)
        embed.set_image(url=item["char_image"])
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="لوحة_المطور", description="لوحة تحكم المطورين الحصرية")
@app_commands.choices(العملية=[
    app_commands.Choice(name="💰 بنك العملات (إضافة رصيد)", value="bank_add"),
    app_commands.Choice(name="⚔️ إهداء عتاد (من القائمة)", value="give_gear"),
    app_commands.Choice(name="👥 إضافة مطور جديد", value="add_dev")
])
@app_commands.describe(العملية="اختر العملية", العضو="العضو المستهدف", كمية_العملات="اكتب عدد العملات (للбанк فقط)")
async def developer_panel(interaction: discord.Interaction, العملية: app_commands.Choice[str], العضو: discord.Member, كمية_العملات: int = 0):
    if interaction.user.id != DEVELOPER_ID and interaction.user.id not in EXTRA_DEVS:
        await interaction.response.send_message("❌ عذراً، هذه اللوحة مخصصة للمطورين فقط!", ephemeral=True)
        return
    
    op_val = العملية.value
    if op_val == "bank_add":
        eco = get_user_economy(العضو.id)
        eco["coins"] += كمية_العملات
        save_database()
        await interaction.response.send_message(f"✅ تمت إضافة `{كمية_العملات}` عملة لـ {العضو.mention}.\n💰 رصيده الجديد: `{eco['coins']}`", ephemeral=True)
    elif op_val == "give_gear":
        await interaction.response.send_message(f"🛠️ اختر العتاد لإهدائه إلى {العضو.mention}:", view=DevGearSelect(العضو), ephemeral=True)
    elif op_val == "add_dev":
        EXTRA_DEVS.add(العضو.id)
        save_database()
        await interaction.response.send_message(f"🛡️ تم منح {العضو.mention} صلاحيات المطور بنجاح.", ephemeral=True)

bot.run(os.getenv('TOKEN'))
