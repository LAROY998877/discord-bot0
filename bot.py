import os
import re
import random
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
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
        print("✅ تم مزامنة نظام الـ 500 طابق والزعماء بنجاح!")

bot = BotClient()

@bot.event
async def on_ready():
    print(f"🤖 البوت يعمل الآن باسم: {bot.user}")

# ================== مولد الـ 50 قطعة تلقائياً لكل فئة ==================
def generate_50_items(shop_type):
    categories_data = {
        "خوذة": {"prefix_n": "خوذة", "prefix_d": "خوذة", "stat_base": "الدرع: +", "stat_extra": " | الصحة: +"},
        "درع": {"prefix_n": "درع", "prefix_d": "درع", "stat_base": "الدرع: +", "stat_extra": " | خفة الحركة: +"},
        "بنطال": {"prefix_n": "بنطال", "prefix_d": "بنطال", "stat_base": "الدرع: +", "stat_extra": " | السرعة: +"},
        "حذاء": {"prefix_n": "حذاء", "prefix_d": "حذاء", "stat_base": "السرعة: +", "stat_extra": " | الدرع: +"},
        "سيف": {"prefix_n": "سيف", "prefix_d": "نصل", "stat_base": "الهجوم: +", "stat_extra": " | كريتيكال: +"},
        "مطرقة": {"prefix_n": "مطرقة", "prefix_d": "مطرقة", "stat_base": "الهجوم: +", "stat_extra": " | السرعة: "},
        "خنجر": {"prefix_n": "خنجر", "prefix_d": "ناب", "stat_base": "الهجوم: +", "stat_extra": " | السم: +"},
        "عصا سحرية": {"prefix_n": "عصا", "prefix_d": "صولجان", "stat_base": "السحر: +", "stat_extra": " | المانا: +"}
    }
    
    tiers_normal = ["شائع", "غير مألوف", "نادر", "متطور", "ممتاز"]
    tiers_dark = ["ملعون", "السفاح", "الجحيم", "الشيطان", "أبدي"]
    
    items_dict = {}
    for cat, info in categories_data.items():
        cat_items = []
        for i in range(1, 51):
            if shop_type == "normal":
                item_id = f"n_{cat}_{i}"
                tier = tiers_normal[(i - 1) // 10]
                price = 200 + (i * 60)
                stat1 = i * 8
                stat2 = i * 4
                name = f"{info['prefix_n']} متطورة #{i}"
                stats = f"{info['stat_base']}{stat1}{info['stat_extra']}{stat2}"
            else:
                item_id = f"d_{cat}_{i}"
                tier = tiers_dark[(i - 1) // 10]
                price = 20 + (i * 8)
                stat1 = i * 25
                stat2 = i * 12
                name = f"{info['prefix_d']} الظلام الأسطورية #{i}"
                stats = f"{info['stat_base']}{stat1}{info['stat_extra']}{stat2}"
            
            cat_items.append({
                "id": item_id,
                "name": name,
                "tier": tier,
                "stats": stats,
                "price": price,
                "stock": 1000
            })
        items_dict[cat] = cat_items
    return items_dict

NORMAL_SHOP_ITEMS = generate_50_items("normal")
DARK_SHOP_ITEMS = generate_50_items("dark")

# ================== نظام الـ 500 طابق والزعماء (Modal & Logic) ==================
class FloorInputModal(discord.ui.Modal, title='🏰 غزو الأبراج (من 1 إلى 500)'):
    floor_number = discord.ui.TextInput(
        label='اختر رقم الطابق المراد غزوه',
        placeholder='أدخل رقماً بين 1 و 500 (مثال: 154)',
        required=True,
        min_length=1,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not self.floor_number.value.isdigit():
            return await interaction.followup.send("❌ يرجى إدخال رقم صحيح للطابق بالأرقام فقط!", ephemeral=True)
        
        floor_num = int(self.floor_number.value)
        if floor_num < 1 or floor_num > 500:
            return await interaction.followup.send("❌ النطاق المسموح للطوابق هو من **1 إلى 500** فقط!", ephemeral=True)

        user_id = str(interaction.user.id)
        
        # أسماء زعماء عشوائية بناءً على تقدم الطابق
        boss_titles = ["حارس الجحيم", "سيد الظلال", "عملاق الفوضى", "ملك الموتى", "شيطان الهلاك", "حارس الأبراج الأسطوري", "مدمر الأكوان"]
        boss_name = f"زعيم الطابق {floor_num}: {random.choice(boss_titles)}"
        
        # نسبة الفوز تتدرج في الصعوبة (تتناقص مع كل طابق، لكنها لا تقل أبداً عن 15% كحد أدنى لمن يمتلك عتاداً قوياً)
        win_probability = max(0.15, 0.95 - (floor_num * 0.0016))
        won = random.random() < win_probability

        if not won:
            return await interaction.followup.send(
                f"💀 **هزيمة نكراء!** في الطابق `{floor_num}`, واجهت الـ **{boss_name}** ولكنه كان أقوى منك بكثير وسحقك تماماً! قوّ عتادك وحاول مجدداً.",
                ephemeral=True
            )

        # حساب المكافآت العشوائية حسب مستوى الطابق
        base_coins = floor_num * 120
        earned_coins = random.randint(base_coins, base_coins + (floor_num * 40))
        
        # نسبة العملات النادرة (الألماس) ضعيفة ومرتبطة بتقدم الطابق (تبدأ من ~6% وتزيد ببطء شديد)
        diamond_chance = min(0.18, 0.05 + (floor_num * 0.0003))
        earned_diamonds = random.randint(1, max(1, floor_num // 80)) if random.random() < diamond_chance else 0

        # نسبة الحصول على عتاد عادي (عشوائية ~25%)
        won_normal_item = None
        if random.random() < 0.25:
            random_cat = random.choice(list(NORMAL_SHOP_ITEMS.keys()))
            won_normal_item = random.choice(NORMAL_SHOP_ITEMS[random_cat])

        # نسبة الحصول على عتاد الظلام الأسطوري (ضعيفة جداً ونادرة، تبدأ من 1% وتصل بحد أقصى إلى 3%)
        dark_item_chance = min(0.03, 0.01 + (floor_num * 0.00004))
        won_dark_item = None
        if random.random() < dark_item_chance:
            random_dark_cat = random.choice(list(DARK_SHOP_ITEMS.keys()))
            won_dark_item = random.choice(DARK_SHOP_ITEMS[random_dark_cat])

        # تحديث قاعدة البيانات
        update_query = {"$inc": {"balance": earned_coins}}
        if earned_diamonds > 0:
            update_query.setdefault("$inc", {})["diamonds"] = earned_diamonds
        
        items_to_push = []
        if won_normal_item:
            items_to_push.append(won_normal_item)
        if won_dark_item:
            items_to_push.append(won_dark_item)

        if items_to_push:
            update_query["$push"] = {"inventory": {"$each": items_to_push}}

        users_col.update_one({"user_id": user_id}, update_query, upsert=True)

        # صياغة رسالة الغنائم العشوائية
        reward_desc = f"🪙 **عملات عادية:** `+{earned_coins}`"
        if earned_diamonds > 0:
            reward_desc += f"\n💎 **عملات نادرة (ألماس):** `+{earned_diamonds}` *(حظ نادر جداً!)*"
        if won_normal_item:
            reward_desc += f"\n🛡️ **قطعة عتاد عادي:** `{won_normal_item['name']}` `[{won_normal_item['tier']}]`"
        if won_dark_item:
            reward_desc += f"\n🌌 **قطعة عتاد مظلم أسطورية (نادرة جداً!):** `{won_dark_item['name']}` `[{won_dark_item['tier']}]`"

        embed = discord.Embed(
            title=f"🎉 انتصار أسطوري في الطابق {floor_num}!",
            description=f"لقد تغلبت على **{boss_name}** باقتدار بعد معركة ضارية!\n\n**غنائم الطابق العشوائية:**\n{reward_desc}",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# ================== نظام القوائم والمعارك الأساسية ==================
class JoinPvPButton(discord.ui.Button):
    def __init__(self, host_id, mode):
        super().__init__(style=discord.ButtonStyle.success, label="انضمام للقتال ⚔️", emoji="🔥")
        self.host_id = host_id
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.host_id:
            return await interaction.response.send_message("❌ لا يمكنك الانضمام لمعركتك الخاصة كخصم!", ephemeral=True)
        
        channel = interaction.channel
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        embed = discord.Embed(
            title=f"⚔️ اكتمل طرفا المعركة! ({self.mode})",
            description=f"المستضيف: <@{self.host_id}>\nالخصم: <@{interaction.user.id}>\n\n🔥 **بدأت المعركة بين الأبطال! استخدموا مهاراتكم بحذر.**",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await channel.send(f"🎮 **انطلاق النزال!** <@{self.host_id}> ضد <@{interaction.user.id}>. المشاهدون يمكنكم متابعة الحماس بصمت!")

class BattleSelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="معركة 1v1", value="1v1", description="تحدي فردي وجهاً لوجه", emoji="⚔️"),
            discord.SelectOption(label="معركة 2v2", value="2v2", description="معركة جماعية ثنائية", emoji="🛡️"),
            discord.SelectOption(label="معركة 3v3", value="3v3", description="حرب الفرق الثلاثية", emoji="⚡"),
            discord.SelectOption(label="الطوابق (500 طابق)", value="floors", description="غزو الأبراج وقتال زعماء الـ 500 طابق", emoji="🗼"),
            discord.SelectOption(label="المتجر", value="shop", description="الانتقال السريع لأسواق العتاد", emoji="🛒"),
            discord.SelectOption(label="تطوير عتادك", value="upgrade", description="رفع مستوى قطعك الحالية", emoji="⚒️"),
            discord.SelectOption(label="حقيبتك", value="inventory", description="استعراض مقتنياتك وأسلحتك", emoji="🎒")
        ]
        super().__init__(placeholder="اختر وجهتك في عالم المعارك...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        choice = self.values[0]
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}
        guild = interaction.guild

        if choice in ["1v1", "2v2", "3v3"]:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel_name = f"معركة-{choice}-{interaction.user.name}".lower().replace(" ", "-")
            room = await guild.create_text_channel(channel_name, overwrites=overwrites)
            
            view = discord.ui.View(timeout=None)
            view.add_item(JoinPvPButton(interaction.user.id, choice))
            
            embed = discord.Embed(
                title=f"⚔️ ساحة تحدي ({choice})",
                description=f"المستضيف: <@{interaction.user.id}>\n\n⏳ **في انتظار انضمام الخصم...**\n*ملاحظة: هذا الروم مخصص للنزال، المشاهدون بإمكانهم المتابعة بصمت تام.*",
                color=discord.Color.red()
            )
            await room.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ تم إنشاء روم المعركة الخاص بك بنجاح: {room.mention}!", ephemeral=True)

        elif choice == "floors":
            # فتح نافذة إدخال رقم الطابق من 1 إلى 500
            await interaction.client.loop.create_task(interaction.followup.send_modal(FloorInputModal()))

        elif choice == "shop":
            view = ShopView(interaction.user.id, "normal")
            await interaction.followup.send("🏬 **المتاجر السريعة:** اختر القسم من القائمة أدناه:", view=view, ephemeral=True)

        elif choice == "upgrade":
            await interaction.followup.send("⚒️ **منطقة التطوير:** قريباً يمكنك دمج وتطوير قطع عتادك لزيادة قوتها!", ephemeral=True)

        elif choice == "inventory":
            inventory = user_data.get("inventory", [])
            inv_list = "\n".join([f"• {item['name']} `[{item['tier']}]` - `{item['stats']}`" for item in inventory]) if inventory else "الحقيبة فارغة تماماً."
            embed = discord.Embed(title="🎒 حقيبة العتاد الخاصة بك", description=inv_list, color=discord.Color.blue())
            await interaction.followup.send(embed=embed, ephemeral=True)

class BattleView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(BattleSelect(author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ عذراً، هذه القائمة خاصة بصاحب الأمر فقط!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="معارك", description="فتح لوحة نظام المعارك والساحات الشاملة")
async def battle_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏟️ ساحة المعارك الكبرى",
        description="أهلاً بك أيها المقاتل في نظام النزالات الأسطوري.\nاختر وجهتك أو نوع التحدي من القائمة أدناه:",
        color=discord.Color.dark_gold()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3211/3211183.png")
    embed.set_footer(text="اختر بوعي واستعد للنزال القادم")
    
    view = BattleView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
