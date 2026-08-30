import random
import discord
from discord.ext import commands

class ShopSystem:
    # الفئات الأساسية للعتاد
    CATEGORIES = ["خوذة", "سيف", "درع", "حذاء", "قفازات"]
    
    # مسببات الخصائص الفريدة
    STAT_POOL = [
        "قوة هجوم إضافية", "نسبة الضربات الحرجة", 
        "مقاومة الضرر", "سرعة الحركة", "امتصاص الدماء"
    ]

    @classmethod
    def generate_items(cls, store_type: str) -> dict:
        """توليد 50 قطعة فريدة لكل فئة بناءً على نوع المتجر (عادي أو مظلم)"""
        inventory = {}
        is_dark = (store_type == "مظلم")
        base_price = 1000 if not is_dark else 5000
        price_multiplier = 150 if not is_dark else 600

        for category in cls.CATEGORIES:
            category_items = []
            for i in range(1, 51):
                price = base_price + (i * price_multiplier)
                stat_name = random.choice(cls.STAT_POOL)
                stat_val = random.randint(5, 25) if not is_dark else random.randint(30, 90)
                
                item = {
                    "id": f"{category}_{i}",
                    "name": f"{'مظلمة' if is_dark else 'عادية'} {category} #{i}",
                    "price": price,
                    "effect": f"+{stat_val}% {stat_name}",
                    "rarity": "أبدي / نادرة جداً" if is_dark else "شائع / متطور"
                }
                category_items.append(item)
            
            inventory[category] = category_items
            
        return inventory

# إعداد الأوامر الخاصة بالمتاجر داخل البوت
class StoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # تخزين مؤقت للسلع المولدة
        self.normal_shop = ShopSystem.generate_items("عادي")
        self.dark_shop = ShopSystem.generate_items("مظلم")

    @commands.command(name="متجر")
    async def normal_store_command(self, ctx, category: str = None):
        """عرض المتجر العادي مع الـ 50 قطعة لكل فئة"""
        if not category or category not in ShopSystem.CATEGORIES:
            categories_list = ", ".join(ShopSystem.CATEGORIES)
            await ctx.send(f"الرجاء اختيار فئة صحيحة من الفئات التالية: {categories_list}\nمثال: `!متجر سيف`")
            return

        items = self.normal_shop.get(category, [])
        embed = discord.Embed(title=f"🛒 المتجر العادي - قسم ({category})", color=discord.Color.blue())
        
        # عرض عينة أو أول 10 قطع لتجنب تجاوز حدود رسائل ديسكورد، ويمكن ربطه بقوائم منسدلة لاحقاً
        description = "\n".join([f"**{item['name']}** | السعر: {item['price']} 🪙 | الميزة: {item['effect']}" for item in items[:10]])
        embed.description = description + "\n\n*(يتم عرض أول 10 قطع من أصل 50 قطعة متوفرة في النظام)*"
        
        await ctx.send(embed=embed)

    @commands.command(name="متجر_مظلم")
    async def dark_store_command(self, ctx, category: str = None):
        """عرض المتجر المظلم مع الـ 50 قطعة الفريدة"""
        if not category or category not in ShopSystem.CATEGORIES:
            categories_list = ", ".join(ShopSystem.CATEGORIES)
            await ctx.send(f"الرجاء اختيار فئة صحيحة: {categories_list}\nمثال: `!متجر_مظلم خوذة`")
            return

        items = self.dark_shop.get(category, [])
        embed = discord.Embed(title=f"🏴‍☠️ المتجر المظلم - قسم ({category})", color=discord.Color.dark_theme())
        
        description = "\n".join([f"**{item['name']}** | السعر: {item['price']} 💎 | الميزة: {item['effect']}" for item in items[:10]])
        embed.description = description + "\n\n*(قطع أسطورية فريدة - عرض عينة من أصل 50 قطعة)*"
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StoreCog(bot))
