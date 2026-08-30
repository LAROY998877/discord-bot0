class TriviaQuestionView(discord.ui.View):
    def __init__(self, difficulty, questions_list, author_id, players, message=None):
        super().__init__(timeout=300)
        self.difficulty = difficulty
        self.questions_list = questions_list
        self.author_id = author_id
        self.players = players
        self.message = message
        self.is_running = True
        # نبدأ المهمة التلقائية لتغيير الأسئلة كل فترة (مثلاً كل 15 ثانية)
        bot.loop.create_task(self.auto_questions_loop())

    async def auto_questions_loop(self):
        try:
            while self.is_running:
                await asyncio.sleep(15)  # الوقت بالثواني بين كل سؤال والثاني (يمكنك تعديله)
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
