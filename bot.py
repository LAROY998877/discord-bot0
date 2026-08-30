class ProfileEditModal(discord.ui.Modal, title='تعديل اللقب الأسطوري 👑'):
    new_title = discord.ui.TextInput(
        label='اكتب لقبك الجديد',
        placeholder='مثال: فارس الظلام الأبدي، سيد الساحات...',
        required=True,
        max_length=35
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        users_col.update_one({"user_id": user_id}, {"$set": {"custom_title": self.new_title.value}}, upsert=True)
        await interaction.response.send_message(f"✨ **تم نقش لقبك الجديد في السجلات الأسطورية بنجاح!**\nلقبك الحالي أصبح: `{self.new_title.value}`", ephemeral=True)

class ProfileView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id

    @discord.ui.button(label="تعديل الألقاب", style=discord.ButtonStyle.blurple, emoji="👑")
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProfileEditModal())

    @discord.ui.button(label="إخفاء/إظهار الحالة", style=discord.ButtonStyle.grey, emoji="👁️‍🗨️")
    async def toggle_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        user_data = users_col.find_one({"user_id": user_id}) or {}
        current_hidden = user_data.get("status_hidden", False)
        new_status = not current_hidden
        
        users_col.update_one({"user_id": user_id}, {"$set": {"status_hidden": new_status}}, upsert=True)
        status_text = "مخفية عن أعين الحاقدين 🔒" else "بارزة وساطعة في الأفق ✨"
        status_text = "مخفية عن الأعين 🔒" if new_status else "نشطة وظاهرة للجميع ✨"
        
        await interaction.response.send_message(f"🛡️ **تم تحديث درع الخصوصية!**\nحالتك الملكية الآن أصبحت: **{status_text}**", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ عذراً، هذه اللوحة الملكية تخص صاحب السجل وحده!", ephemeral=True)
            return False
        return True

@bot.tree.command(name="الملف", description="استعراض السجل الأرشيفي والملف الأسطوري الفخم للمقاتل")
async def profile_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = users_col.find_one({"user_id": user_id}) or {}
    
    # جلب بيانات المستخدم من قاعدة البيانات
    balance = user_data.get("balance", 0)
    diamonds = user_data.get("diamonds", 0)
    custom_title = user_data.get("custom_title", "مقاتل مستجد في عتبة الأبراج")
    status_hidden = user_data.get("status_hidden", False)
    status_display = "مخفية عن الأعين 🔒" if status_hidden else "نشط ومرئي للجميع 🟢"
    inventory = user_data.get("inventory", [])
    items_count = len(inventory)
    
    # تصميم واجهة الـ Embed بشكل فخم ورهيب
    embed = discord.Embed(
        title="📜 ─── [ السجل الأرشيفي الملكي للمقاتل ] ─── 📜",
        description=(
            f"مرحباً بك أيها البطل في أرشيف المجد والخلود الخاص بعالم المعارك والظلمات.\n"
            f"يوثق هذا السجل هيبتك، ممتلكاتك، ومكانتك بين عظماء الساحة.\n\n"
            f"⚡ **اللقب الأسطوري:** `{custom_title}`\n"
            f"🛡️ **حالة الحضور:** `{status_display}`"
        ),
        color=discord.Color.dark_gold()
    )
    
    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)
        
    embed.add_field(name="💳 خزينة الثروة والأرصدة", value=f"• العملات العادية: `{balance:,}` 🪙\n• العملات النادرة: `{diamonds:,}` 💎", inline=True)
    embed.add_field(name="🎒 مستودع الترسانة", value=f"• إجمالي القطع المقتناة: `{items_count}` قطعة حربية مسجلة.", inline=True)
    
    recent_items = "، ".join([item['name'] for item in inventory[-3:]]) if inventory else "لا توجد قطع مسجلة في حقيبتك حتى الآن."
    embed.add_field(name="⚔️ آخر مقتنيات العتاد", value=f"*{recent_items}*", inline=False)
    
    embed.set_footer(text=f"معرف الهوية الأسطورية: {user_id} • نظام السجلات المؤمّن", icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None)
    
    view = ProfileView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
