@bot.tree.command(name="مسح_جميع_الاوامر", description="⚠️ حذف جميع أوامر السلاش المسجلة في ديسكورد")
async def clear_all_commands(ctx: discord.Interaction):
    if not is_dev(ctx.user.id):
        await ctx.response.send_message("❌ هذا الأمر مقتصر على المطورين فقط!", ephemeral=True)
        return
    
    # 1. مسح جميع الأوامر المسجلة محلياً في البوت
    bot.tree.clear_commands(guild=None)
    
    # 2. إرسال الشجرة الفارغة إلى ديسكورد لحذفها من السيرفرات
    await bot.tree.sync()
    
    await ctx.response.send_message("🗑️ **تم مسح جميع أوامر السلاش من ديسكورد بنجاح!**", ephemeral=True)
