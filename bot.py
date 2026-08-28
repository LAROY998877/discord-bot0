@bot.command(name="sync")
async def sync_commands(ctx):
    try:
        # 1. مسح جميع الأوامر المحلية المرتبطة بهذا السيرفر تماماً
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        
        # 2. إعادة تسجيل الأوامر الموجودة في الكود الحالي فقط
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        
        await ctx.send(f"✅ تم تنظيف السيرفر وإعادة مزامنة `{len(synced)}` أمر بدقة بدون تكرار!")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء المزامنة: {e}")
