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
        print("✅ تم مزامنة جميع الأنظمة بنجاح!")

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

# ================== المتاجر والقوائم ==================
class ShopSpecificSelect(discord.ui.Select):
    def __init__(self, items_pool, shop_type, category, page=0):
        self.items_pool = items_pool
        self.shop_type = shop_type
        self.category = category
        self.page = page
        
        start = page * 25
        end = start + 25
        current_items = items_pool[start:end]
        
        options = [
            discord.SelectOption(
                label=f"{item['name']} [{item['tier']}]", 
                value=item["id"], 
                description=f"السعر: {item['price']} | {item['stats']}"
            ) for item in current_items
        ]
        super().__init__(placeholder=f"اختر قطعة من قسم {category} (صفحة {page+1})...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        item_id = self.values[0]
        item = next((it for it in self.items_pool if it["id"] == item_id), None)
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}

        if self.shop_type == "normal":
            if user_data.get("balance", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك العادي غير كافٍ! تحتاج `{item['price']}` 🪙.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -item["price"]}, "$push": {"inventory": item}}, upsert=True)
        else:
            if user_data.get("diamonds", 0) < item["price"]:
                return await interaction.followup.send(f"❌ رصيدك من الألماس غير كافٍ! تحتاج `💎 {item['price']}`.", ephemeral=True)
            users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -item["price"]}, "$push": {"inventory": item}}, upsert=True)

        await interaction.followup.send(f"🎉 **تم الشراء بنجاح!** حصلت على **{item['name']}** `[{item['tier']}]`", ephemeral=True)

class ShopPageButton(discord.ui.Button):
    def __init__(self, items_pool, shop_type, category, author_id, target_page, label, disabled):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=disabled)
        self.items_pool = items_pool
        self.shop_type = shop_type
        self.category = category
        self.author_id = author_id
        self.target_page = target_page

    async def callback(self, interaction: discord.Interaction):
        view = ShopPaginationView(self.items_pool, self.shop_type, self.category, self.author_id, page=self.target_page)
        await interaction.response.edit_message(content=f"🛒 تتصفح قسم: **{self.category}** (الصفحة {self.target_page + 1})", view=view)

class ShopPaginationView(discord.ui.View):
    def __init__(self, items_pool, shop_type, category, author_id, page=0):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(ShopSpecificSelect(items_pool, shop_type, category, page))
        if len(items_pool) > 25:
            self.add_item(ShopPageButton(items_pool, shop_type, category, author_id, 0, label="الصفحة 1", disabled=(page == 0)))
            self.add_item(ShopPageButton(items_pool, shop_type, category, author_id, 1, label="الصفحة 2", disabled=(page == 1)))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

class ShopCategorySelect(discord.ui.Select):
    def __init__(self, shop_type):
        self.shop_type = shop_type
        options = [
            discord.SelectOption(label="خوذة", value="خوذة", emoji="🪖"),
            discord.SelectOption(label="درع", value="درع", emoji="🛡️"),
            discord.SelectOption(label="بنطال", value="بنطال", emoji="👖"),
            discord.SelectOption(label="حذاء", value="حذاء", emoji="🥾"),
            discord.SelectOption(label="سيف", value="سيف", emoji="⚔️"),
            discord.SelectOption(label="مطرقة", value="مطرقة", emoji="🔨"),
            discord.SelectOption(label="خنجر", value="خنجر", emoji="🗡️"),
            discord.SelectOption(label="عصا سحرية", value="عصا سحرية", emoji="🪄")
        ]
        super().__init__(placeholder="اختر فئة العتاد...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        items_pool = NORMAL_SHOP_ITEMS.get(category, []) if self.shop_type == "normal" else DARK_SHOP_ITEMS.get(category, [])
        view = ShopPaginationView(items_pool, self.shop_type, category, interaction.user.id, page=0)
        await interaction.response.edit_message(content=f"🛒 تتصفح قسم: **{category}**", view=view)

class ShopView(discord.ui.View):
    def __init__(self, author_id, shop_type):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(ShopCategorySelect(shop_type))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="المتجر_العادي", description="تصفح متجر العتاد العادي")
async def normal_shop(interaction: discord.Interaction):
    await interaction.response.send_message("🏬 **متجر العتاد العادي**\nاختر القسم:", view=ShopView(interaction.user.id, "normal"), ephemeral=True)

@bot.tree.command(name="المتجر_المظلم", description="تصفح المتجر المظلم")
async def dark_shop(interaction: discord.Interaction):
    await interaction.response.send_message("🌌 **المتجر المظلم**\nاختر القسم:", view=ShopView(interaction.user.id, "dark"), ephemeral=True)

# ================== الطوابق والزعماء ==================
class FloorInputModal(discord.ui.Modal, title='🏰 غزو الأبراج (من 1 إلى 500)'):
    floor_number = discord.ui.TextInput(label='رقم الطابق', placeholder='من 1 إلى 500', required=True, min_length=1, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not self.floor_number.value.isdigit():
            return await interaction.followup.send("❌ أدخل رقماً صحيحاً!", ephemeral=True)
        
        floor_num = int(self.floor_number.value)
        if not (1 <= floor_num <= 500):
            return await interaction.followup.send("❌ النطاق من 1 إلى 500 فقط!", ephemeral=True)

        user_id = str(interaction.user.id)
        boss_name = f"زعيم الطابق {floor_num}"
        won = random.random() < max(0.15, 0.95 - (floor_num * 0.0016))

        if not won:
            return await interaction.followup.send(f"💀 هزيمة أمام **{boss_name}**!", ephemeral=True)

        earned_coins = floor_num * 120
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": earned_coins}}, upsert=True)
        await interaction.followup.send(f"🎉 انتصرت في الطابق {floor_num} وكسبت `{earned_coins}` 🪙!", ephemeral=True)

# ================== المعارك ==================
class JoinPvPButton(discord.ui.Button):
    def __init__(self, host_id, mode):
        super().__init__(style=discord.ButtonStyle.success, label="انضمام للقتال ⚔️")
        self.host_id = host_id
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.host_id:
            return await interaction.response.send_message("❌ لا يمكنك الانضمام لمعركتك الخاصة!", ephemeral=True)
        
        channel = interaction.channel
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await interaction.response.edit_message(content=f"⚔️ **اكتملت المعركة بين <@{self.host_id}> و <@{interaction.user.id}>!**", view=None)

class BattleSelect(discord.ui.Select):
    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            discord.SelectOption(label="معركة 1v1", value="1v1", emoji="⚔️"),
            discord.SelectOption(label="معركة 2v2", value="2v2", emoji="🛡️"),
            discord.SelectOption(label="معركة 3v3", value="3v3", emoji="⚡"),
            discord.SelectOption(label="الطوابق (500 طابق)", value="floors", emoji="🗼"),
            discord.SelectOption(label="الحقيبة", value="inventory", emoji="🎒")
        ]
        super().__init__(placeholder="اختر وجهتك...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        
        if choice == "floors":
            return await interaction.response.send_modal(FloorInputModal())

        # تأجيل الاستجابة لمنع خطأ الـ 3 ثوانٍ وتفريغ التعليق
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}
        guild = interaction.guild

        if choice in ["1v1", "2v2", "3v3"]:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel_name = f"معركة-{choice}-{interaction.user.name}".lower().replace(" ", "-")
                room = await guild.create_text_channel(channel_name, overwrites=overwrites)
                
                view = discord.ui.View(timeout=None)
                view.add_item(JoinPvPButton(interaction.user.id, choice))
                
                embed = discord.Embed(title=f"⚔️ ساحة تحدي ({choice})", description=f"المستضيف: <@{interaction.user.id}>\n⏳ في انتظار الخصم...", color=discord.Color.red())
                await room.send(embed=embed, view=view)
                await interaction.followup.send(f"✅ تم إنشاء روم المعركة بنجاح: {room.mention}", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ البوت لا يمتلك صلاحية `Manage Channels` لإنشاء روم المعركة!", ephemeral=True)

        elif choice == "inventory":
            inventory = user_data.get("inventory", [])
            inv_list = "\n".join([f"• {item['name']} `[{item['tier']}]`" for item in inventory]) if inventory else "الحقيبة فارغة."
            embed = discord.Embed(title="🎒 حقيبتك", description=inv_list, color=discord.Color.blue())
            await interaction.followup.send(embed=embed, ephemeral=True)

class BattleView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(BattleSelect(author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="معارك", description="فتح ساحة المعارك الكبرى")
async def battle_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🏟️ ساحة المعارك", description="اختر نوع التحدي:", color=discord.Color.dark_gold())
    await interaction.response.send_message(embed=embed, view=BattleView(interaction.user.id), ephemeral=True)

# ================== الملف الشخصي ==================
class ProfileEditModal(discord.ui.Modal, title='تعديل اللقب 👑'):
    new_title = discord.ui.TextInput(label='اللقب الجديد', required=True, max_length=35)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$set": {"custom_title": self.new_title.value}}, upsert=True)
        await interaction.response.send_message(f"✨ تم تحديث لقبك إلى: `{self.new_title.value}`", ephemeral=True)

class ProfileView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id

    @discord.ui.button(label="تعديل اللقب", style=discord.ButtonStyle.blurple, emoji="👑")
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfileEditModal())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ ليست لك!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="الملف", description="عرض الملف الأسطوري")
async def profile_command(interaction: discord.Interaction):
    # استخدام defer لمنع خطأ الـ 3 ثواني
    await interaction.response.defer(ephemeral=True)
    
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "مقاتل مستجد")
    inventory = user_data.get("inventory", [])
    
    embed = discord.Embed(title="📜 الملف الشخصي للمقاتل", description=f"⚡ **اللقب:** `{custom_title}`", color=discord.Color.dark_gold())
    embed.add_field(name="الرصيد", value=f"`{balance:,}` 🪙 | `💎 {diamonds:,}`", inline=False)
    embed.add_field(name="العتاد", value=f"إجمالي القطع: `{len(inventory)}`", inline=False)
    
    await interaction.followup.send(embed=embed, view=ProfileView(interaction.user.id), ephemeral=True)

# ================== البنك ==================
@bot.tree.command(name="بنك", description="فتح الحساب البنكي")
async def bank_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    
    bal = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    
    embed = discord.Embed(title="🏦 البنك المركزي", description=f"رصيدك الحالي: `{bal}` 🪙\nالألماس: `{diamonds}` 💎", color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)

bot.run(DISCORD_TOKEN)
