@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح: {bot.user}")
    
    # مسح كامل للأوامر العالمية والخاصة بالسيرفر
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    
    bot.tree.clear_commands(guild=MY_GUILD_ID)
    await bot.tree.sync(guild=MY_GUILD_ID)
    
    # تسجيل الأمر مباشرة في سيرفرك حصراً بشكل فوري
    bot.tree.copy_global_to(guild=MY_GUILD_ID)
    synced = await bot.tree.sync(guild=MY_GUILD_ID)
    print(f"تم مزامنة {len(synced)} أمر بنجاح في سيرفرك!")
