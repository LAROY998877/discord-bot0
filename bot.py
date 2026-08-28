DEVELOPER_ID = 1103985971638325269  # الآيدي الخاص بك

@bot.tree.command(name="المطور_اضافة_امر", description="أمر خاص بالمطور فقط لإضافة خصائص برمجية للمستقبل")
@app_commands.describe(الكود_أو_الميزة="اكتب وصف الميزة أو الأمر البرمجي المراد إضافته")
async def dev_only_command(interaction: discord.Interaction, الكود_أو_الميزة: str):
    # 1. التحقق أولاً وقبل كل شيء وبدون أي استجابة مسبقة
    if interaction.user.id != DEVELOPER_ID:
        await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص **لمطور البوت فقط** ولا يحق لك استخدامه!", ephemeral=True)
        return
    
    # 2. الاستجابة المؤقتة للمطور فقط إذا كان هو صاحب الحساب
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🛠️ لوحة تحكم المطورين",
        description=f"تم استقبال الميزة أو الكود الجديد بنجاح وإضافته للنظام الآلي:\n\n> `{الكود_أو_الميزة}`",
        color=discord.Color.dark_embed()
    )
    embed.set_footer(text="لوحة المطور السيادية 🔒")
    await interaction.followup.send(embed=embed, ephemeral=True)

# تشغيل البوت
bot.run(os.getenv('TOKEN'))
